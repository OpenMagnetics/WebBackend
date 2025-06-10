from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from app.backend.models import NotificationsTable, BugReportsTable, MasTable, IntermediateMasTable, CoreMaterialsTable
from app.backend.models import BugReport
from app.backend.mas_models import MagneticCore, CoreShape, Magnetic, Inputs
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.encoders import jsonable_encoder
import pandas
from datetime import datetime
import json
import bson
from bson import ObjectId, json_util
import copy
import os
import pathlib
import base64
import time
from pylatex import Document, Command, Package
from pylatex.utils import NoEscape
import PyMKF
from OpenMagneticsVirtualBuilder.builder import Builder as ShapeBuilder  # noqa: E402
import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../MVB/src/OpenMagneticsVirtualBuilder')))
# from builder import Builder as ShapeBuilder  # noqa: E402
import hashlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app/backend')))
from plotter import task_generate_core_3d_model, task_plot_core_and_fields, task_plot_core, task_plot_wire, task_plot_wire_and_current_density
from plotter import task_generate_core_technical_drawing, task_generate_gapping_technical_drawing

temp_folder = "/opt/openmagnetics/temp"


def clean_dimensions(core):
    # Make sure no unwanted dimension gets in
    families = ShapeBuilder("FreeCAD").get_families()
    if "familySubtype" in core['functionalDescription']['shape'] and core['functionalDescription']['shape']['familySubtype'] is not None:
        dimensions = families[core['functionalDescription']['shape']['family']][int(core['functionalDescription']['shape']['familySubtype'])]
    else:
        dimensions = families[core['functionalDescription']['shape']['family']][1]
    aux = copy.deepcopy(core['functionalDescription']['shape']['dimensions'])
    for key, value in core['functionalDescription']['shape']['dimensions'].items():
        if key not in dimensions:
            aux.pop(key)
    core['functionalDescription']['shape']['dimensions'] = aux
    return core


def delete_none(_dict):
    """Delete None values recursively from all of the dictionaries, tuples, lists, sets"""
    if isinstance(_dict, dict):
        for key, value in list(_dict.items()):
            if isinstance(value, (list, dict, tuple, set)):
                _dict[key] = delete_none(value)
            elif value is None or key is None:
                del _dict[key]

    elif isinstance(_dict, (list, set, tuple)):
        _dict = type(_dict)(delete_none(item) for item in _dict if item is not None)

    return _dict


def flatten_dimensions(data):
    dimensions = data["dimensions"]
    for k, v in dimensions.items():
        if "nominal" not in v:
            if "maximum" not in v:
                v["nominal"] = v["minimum"]
            elif "minimum" not in v:
                v["nominal"] = v["maximum"]
            else:
                v["nominal"] = round((v["maximum"] + v["minimum"]) / 2, 6)
    dim = {k: v["nominal"] for k, v in dimensions.items()}
    data["dimensions"] = dim
    return data


app = FastAPI()

origins = [
    "https://openmagnetics.com",
    "https://beta.openmagnetics.com",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def read_root():
    return {"Hello": "World"}


@app.post("/get_notifications", include_in_schema=False)
def get_notifications():
    notifications_table = NotificationsTable()
    new_notifications = notifications_table.read_active_notifications(datetime.now())
    return {"notifications": new_notifications.to_dict('records')}


@app.post("/report_bug", include_in_schema=False)
def report_bug(data: BugReport):
    data = data.dict()

    bug_reports_table = BugReportsTable()
    bug_report_id = bug_reports_table.report_bug(data['username'], data['userDataDump'], data['userInformation'])
    return {"status": "reported", "bug_report_id": bug_report_id}


@app.post("/core_compute_shape_stl", include_in_schema=False)
@app.post("/core_compute_shape", include_in_schema=False)
def core_compute_shape(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder("FreeCAD").factory(coreShape)
    core_builder.set_output_path(temp_folder)    
    step_path, stl_path = core_builder.get_piece(coreShape)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(stl_path)


@app.post("/core_compute_shape_stp", include_in_schema=False)
def core_compute_shape_stp(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder("FreeCAD").factory(coreShape)
    core_builder.set_output_path(temp_folder)    
    step_path, stl_path = core_builder.get_piece(coreShape)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(step_path)


@app.post("/core_compute_core_3d_model_stl", include_in_schema=False)
@app.post("/core_compute_core_3d_model", include_in_schema=False)
async def core_compute_core_3d_model(request: Request):
    core = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_generate_core_3d_model.delay(core, temp_folder)
        stl_data = result.get(timeout=10)
        if stl_data is not None:
            break
        print("Retrying task_generate_core_3d_model")

    if stl_data is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        json_compatible_item_data = jsonable_encoder(stl_data, custom_encoder={bytes: lambda v: base64.b64encode(v).decode('utf-8')})
        return json_compatible_item_data


@app.post("/core_compute_core_3d_model_stp", include_in_schema=False)
async def core_compute_core_3d_model_stp(request: Request):
    core = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_generate_core_3d_model.delay(core, temp_folder, False)
        stl_data = result.get(timeout=10)
        if stl_data is not None:
            break
        print("Retrying task_generate_core_3d_model")

    if stl_data is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        json_compatible_item_data = jsonable_encoder(stl_data, custom_encoder={bytes: lambda v: base64.b64encode(v).decode('utf-8')})
        return json_compatible_item_data


@app.post("/core_compute_technical_drawing", include_in_schema=False)
async def core_compute_technical_drawing(request: Request):
    data = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_generate_core_technical_drawing.delay(data, temp_folder)
        views = result.get(timeout=10)
        if views is not None:
            break
        print("Retrying task_generate_core_technical_drawing")

    if views is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return views


@app.post("/core_compute_gapping_technical_drawing", include_in_schema=False)
async def core_compute_gapping_technical_drawing(request: Request):
    data = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_generate_gapping_technical_drawing.delay(data, temp_folder)
        views = result.get(timeout=10)
        if views is not None:
            break
        print("Retrying task_generate_gapping_technical_drawing")

    if views is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return views


@app.post("/process_latex", include_in_schema=True)
async def process_latex(request: Request):
    print(request)
    print(dir(request))
    tex = await request.body()
    tex = tex.decode('utf-8')
    filepath = "/opt/openmagnetics/latex"
    pathlib.Path(filepath).mkdir(parents=True, exist_ok=True)
    doc = Document(default_filepath=f"{filepath}/tex")
    doc.packages.append(Package('array'))
    doc.packages.append(Package('booktabs'))
    doc.packages.append(Package('babel'))
    doc.packages.append(Package('amsmath'))
    doc.packages.append(Package('relsize'))
    doc.packages.append(Package('cellspace'))
    doc.packages.append(Package('tikz'))
    doc.packages.append(Package('geometry'))
    doc.packages.append(Package('fancyhdr'))
    doc.preamble.append(Command('setlength\\cellspacetoplimit', '4pt'))
    doc.preamble.append(Command('setlength\\cellspacebottomlimit', '4pt'))
    doc.preamble.append(Command('usetikzlibrary', 'datavisualization'))
    doc.preamble.append(Command('geometry', 'tmargin=1in'))
    doc.preamble.append(Command('pagestyle', 'fancy'))
    tex = tex.replace('μ', '$\\mu$')
    doc.append(NoEscape(tex))
    doc.generate_pdf(clean_tex=False)

    with open(f"{filepath}/tex.pdf", "rb") as pdf_file:
        pdf_string = base64.b64encode(pdf_file.read())
        return pdf_string


@app.post("/plot_core_and_fields", include_in_schema=True)
async def plot_core_and_fields(request: Request):
    data = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_plot_core_and_fields.delay(data, temp_folder)
        plot = result.get(timeout=10)
        if plot is not None:
            break
        print("Retrying plot_core_and_fields")

    if plot is None:
        raise HTTPException(status_code=418, detail="Plotting timed out")

    return FileResponse(plot)


@app.post("/plot_core", include_in_schema=True)
async def plot_core(request: Request):
    data = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_plot_core.delay(data, temp_folder)
        plot = result.get(timeout=10)
        if plot is not None:
            break
        print("Retrying task_plot_core")

    if plot is None:
        raise HTTPException(status_code=418, detail="Plotting timed out")

    return FileResponse(plot)


@app.post("/plot_wire", include_in_schema=True)
async def plot_wire(request: Request):
    data = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_plot_wire.delay(data, temp_folder)
        plot = result.get(timeout=10)
        if plot is not None:
            break
        print("Retrying task_plot_wire")

    if plot is None:
        raise HTTPException(status_code=418, detail="Plotting timed out")

    return FileResponse(plot)


@app.post("/plot_wire_and_current_density", include_in_schema=True)
async def plot_wire_and_current_density(request: Request):
    data = await request.json()
    number_retries = 5

    for retry in range(number_retries):
        result = task_plot_wire_and_current_density.delay(data, temp_folder)
        plot = result.get(timeout=10)
        if plot is not None:
            break
        print("Retrying task_plot_wire_and_current_density")

    if plot is None:
        raise HTTPException(status_code=418, detail="Plotting timed out")

    return FileResponse(plot)


def insert_mas_background(data):
    mas_table = MasTable()
    mas_table.insert_mas(data)


@app.post("/insert_mas", include_in_schema=False)
async def insert_mas(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    background_tasks.add_task(insert_mas_background, data)

    return "Inserting in the background"


def insert_intermediate_mas_background(data):
    mas_table = IntermediateMasTable()
    mas_table.insert_mas(data)


@app.post("/insert_intermediate_mas", include_in_schema=False)
async def insert_intermediate_mas(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    background_tasks.add_task(insert_intermediate_mas_background, data)

    return "Inserting in the background"


@app.post("/load_external_core_materials", include_in_schema=False)
async def load_external_core_materials(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    external_core_materials_string = data["coreMaterialsString"]

    PyMKF.load_core_materials(external_core_materials_string)
    PyMKF.load_core_materials("")
    return "Data loaded"


@app.post("/store_request", include_in_schema=False)
async def store_request(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    request = {
        "email": data["email"],
        "name": data["name"],
        "mas": data["mas"],
    }

    file = "/opt/openmagnetics/temp/requests.csv"

    requests = pandas.DataFrame()

    if os.path.exists(file):
        requests = pandas.read_csv(file)

    row = pandas.DataFrame([request])
    print(row)

    requests = pandas.concat([requests, row], ignore_index=True)
    print(requests)

    requests.to_csv(file)


@app.post("/read_core_material_by_name", include_in_schema=False)
async def read_core_material_by_name(request: Request):
    dataJson = await request.json()
    core_materials_table = CoreMaterialsTable()
    core_material_data = core_materials_table.read_material_by_name(dataJson["name"])

    return core_material_data
