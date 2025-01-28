from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from app.backend.models import UsersTable, NotificationsTable, BugReportsTable, RoadmapVotesTable, OperationPointsTable, CoresTable, BobbinsTable, WiresTable, MagneticsTable, MasTable, IntermediateMasTable
from app.backend.models import OperationPointSlugsTable, CoreSlugsTable, BobbinSlugsTable, WireSlugsTable, MagneticSlugsTable
from app.backend.models import Vote, UserLogin, UserRegister, OperationPointSlug, Username, BugReport
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
import hashlib

temp_folder = "/opt/openmagnetics/temp"


def clean_dimensions(core):
    # Make sure no unwanted dimension gets in
    families = ShapeBuilder().get_families()
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


def get_table(url):
    for chunk in url.split("/")[3:]:
        if "operation_point" in chunk:
            return OperationPointsTable()
        if "core" in chunk:
            return CoresTable()
        if "bobbin" in chunk:
            return BobbinsTable()
        if "wire" in chunk:
            return WiresTable()
        if "magnetic" in chunk:
            return MagneticsTable()


def get_table_slug(url):
    for chunk in url.split("/")[3:]:
        if "operation_point" in chunk:
            return OperationPointSlugsTable()
        if "core" in chunk:
            return CoreSlugsTable()
        if "bobbin" in chunk:
            return BobbinSlugsTable()
        if "wire" in chunk:
            return WireSlugsTable()
        if "magnetic" in chunk:
            return MagneticSlugsTable()


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
    core_builder = ShapeBuilder().factory(coreShape)
    core_builder.set_output_path(temp_folder)    
    step_path, stl_path = core_builder.get_piece(coreShape)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(stl_path)


@app.post("/core_compute_shape_stp", include_in_schema=False)
def core_compute_shape_stp(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder().factory(coreShape)
    core_builder.set_output_path(temp_folder)    
    step_path, stl_path = core_builder.get_piece(coreShape)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(step_path)


@app.post("/core_compute_core_3d_model_stl", include_in_schema=False)
@app.post("/core_compute_core_3d_model", include_in_schema=False)
async def core_compute_core_3d_model(request: Request):
    number_tries = 2

    while number_tries > 0:
        json = await request.json()

        if 'familySubtype' in json['functionalDescription']['shape']:
            json['functionalDescription']['shape']['familySubtype'] = str(json['functionalDescription']['shape']['familySubtype'])

        core = MagneticCore(**json)
        core = core.dict()

        core = clean_dimensions(core)
        if not isinstance(core['functionalDescription']['material'], str):
            core['functionalDescription']['material'] = core['functionalDescription']['material']['name']

        # pprint.pprint(core)
        aux = {
            "core": core,
        }
        hash_value = hashlib.sha256(str(aux).encode()).hexdigest()
        # print(hash_value)

        if os.path.exists(f"{temp_folder}/cores/{hash_value}_core.stl"):
            print("Core stl Hit!")
            with open(f"{temp_folder}/cores/{hash_value}_core.stl", "rb") as stl:
                stl_data = stl.read()
                json_compatible_item_data = jsonable_encoder(stl_data, custom_encoder={bytes: lambda v: base64.b64encode(v).decode('utf-8')})
                return json_compatible_item_data

        step_path, stl_path = ShapeBuilder().get_core(project_name=hash_value,
                                                      geometrical_description=core['geometricalDescription'],
                                                      output_path=f"{temp_folder}/cores")
        if stl_path is None and number_tries > 0:
            number_tries -= 1
            continue

        break

    if stl_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        with open(stl_path, "rb") as stl:
            stl_data = stl.read()
            json_compatible_item_data = jsonable_encoder(stl_data, custom_encoder={bytes: lambda v: base64.b64encode(v).decode('utf-8')})
            return json_compatible_item_data


@app.post("/core_compute_core_3d_model_stp", include_in_schema=False)
async def core_compute_core_3d_model_stp(request: Request):
    json = await request.json()
    number_tries = 2

    while number_tries > 0:
        if 'familySubtype' in json['functionalDescription']['shape']:
            json['functionalDescription']['shape']['familySubtype'] = str(json['functionalDescription']['shape']['familySubtype'])

        core = MagneticCore(**json)
        core = core.dict()

        core = clean_dimensions(core)

        aux = {
            "core": core,
        }
        hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

        if os.path.exists(f"{temp_folder}/cores/{hash_value}_core.stp"):
            print("Hit!")
            return FileResponse(f"{temp_folder}/cores/{hash_value}_core.stp")

        step_path, stl_path = ShapeBuilder().get_core(project_name=hash_value,
                                                      geometrical_description=core['geometricalDescription'],
                                                      output_path=f"{temp_folder}/cores")
        if step_path is None and number_tries > 0:
            number_tries -= 1
            continue
        
        break

    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(step_path)


@app.post("/core_compute_technical_drawing", include_in_schema=False)
async def core_compute_technical_drawing(request: Request):
    json = await request.json()
    if 'familySubtype' in json:
        json['familySubtype'] = str(json['familySubtype'])

    coreShape = CoreShape(**json)

    coreShape = coreShape.dict()
    core_builder = ShapeBuilder().factory(coreShape)
    core_builder.set_output_path(f"{temp_folder}/")
    colors = {
        "projection_color": "#d4d4d4",
        "dimension_color": "#d4d4d4"
    }
    views = core_builder.get_piece_technical_drawing(coreShape, colors)
    if views['top_view'] is None or views['front_view'] is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return views


@app.post("/core_compute_gapping_technical_drawing", include_in_schema=False)
async def core_compute_gapping_technical_drawing(request: Request):
    json = await request.json()
    if 'familySubtype' in json['functionalDescription']['shape']:
        json['functionalDescription']['shape']['familySubtype'] = str(json['functionalDescription']['shape']['familySubtype'])

    core = MagneticCore(**json)
    core = core.dict()

    colors = {
        "projection_color": "#d4d4d4",
        "dimension_color": "#d4d4d4"
    }

    views = ShapeBuilder().get_core_gapping_technical_drawing(project_name=core['functionalDescription']['shape']['name'],
                                                              core_data=core,
                                                              colors=colors,
                                                              save_files=False)
    if views['front_view'] is None:
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

    aux = {
        "magnetic": data["magnetic"],
        "operatingPoint": data["operatingPoint"],
        "includeFringing": data["includeFringing"],
    }
    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Hit!")
        return FileResponse(f"{temp_folder}/{hash_value}.svg")

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = True
    settings["painterAdvancedLitz"] = False
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    settings["painterIncludeFringing"] = data["includeFringing"]
    settings["painterColorBobbin"] = "0x7F539796"
    settings["painterColorText"] = "0xd4d4d4"
    settings["painterColorLines"] = "0x1a1a1a"
    settings["painterColorMargin"] = "0x7Ffff05b"
    PyMKF.set_settings(settings)
    result = PyMKF.plot_field(data["magnetic"], data["operatingPoint"], f"{temp_folder}/{hash_value}.svg")
    print(result)
    timeout = 0
    current_size = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        print(timeout)
        if timeout == 1000:
            raise HTTPException(status_code=418, detail="Plotting timed out")
    return FileResponse(f"{temp_folder}/{hash_value}.svg")


@app.post("/plot_core", include_in_schema=True)
async def plot_core(request: Request):
    data = await request.json()
    aux = {
        "magnetic": data["magnetic"]
    }
    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Plot core Hit!")
        print(hash_value)
        return FileResponse(f"{temp_folder}/{hash_value}.svg")

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = True
    settings["painterAdvancedLitz"] = False
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    PyMKF.set_settings(settings)
    PyMKF.plot_turns(data["magnetic"], f"{temp_folder}/{hash_value}.svg")

    timeout = 0
    current_size = 0
    while not os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        time.sleep(0.01)
        timeout += 1
        if timeout == 200:
            raise HTTPException(status_code=418, detail="Plotting timed out")

    timeout = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        if timeout == 1000:
            raise HTTPException(status_code=418, detail="Plotting timed out")
    return FileResponse(f"{temp_folder}/{hash_value}.svg")


@app.post("/plot_wire", include_in_schema=True)
async def plot_wire(request: Request):
    data = await request.json()
    aux = {
        "wire": data["wire"]
    }

    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Hit!")
        return FileResponse(f"{temp_folder}/{hash_value}.svg")

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = False
    settings["painterAdvancedLitz"] = False
    settings["painterColorBobbin"] = "0x539796"
    settings["painterColorMargin"] = "0xfff05b"
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    PyMKF.set_settings(settings)

    # print(data["wire"])
    PyMKF.plot_wire(data["wire"], f"{temp_folder}/{hash_value}.svg", "/opt/openmagnetics/cci_coords/coordinates/")
    timeout = 0
    current_size = 0
    while not os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        time.sleep(0.01)
        timeout += 1
        if timeout == 200:
            raise HTTPException(status_code=418, detail="Plotting timed out")

    timeout = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        if timeout == 1000:
            raise HTTPException(status_code=418, detail="Plotting timed out")
    return FileResponse(f"{temp_folder}/{hash_value}.svg")


@app.post("/plot_wire_and_current_density", include_in_schema=True)
async def plot_wire_and_current_density(request: Request):
    data = await request.json()
    aux = {
        "wire": data["wire"],
        "operatingPoint": data["operatingPoint"],
    }

    hash_value = hashlib.sha256(str(aux).encode()).hexdigest()

    if os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        print("Hit!")
        return FileResponse(f"{temp_folder}/{hash_value}.svg")

    settings = PyMKF.get_settings()
    settings["painterSimpleLitz"] = False
    settings["painterAdvancedLitz"] = False
    settings["painterCciCoordinatesPath"] = "/opt/openmagnetics/cci_coords/coordinates/"
    PyMKF.set_settings(settings)

    PyMKF.plot_current_density(data["wire"], data["operatingPoint"], f"{temp_folder}/{hash_value}.svg")
    timeout = 0
    current_size = 0
    while not os.path.exists(f"{temp_folder}/{hash_value}.svg"):
        time.sleep(0.01)
        timeout += 1
        if timeout == 200:
            raise HTTPException(status_code=418, detail="Plotting timed out")

    timeout = 0
    while os.stat(f"{temp_folder}/{hash_value}.svg").st_size == 0 or current_size != os.stat(f"{temp_folder}/{hash_value}.svg").st_size:
        current_size = os.stat(f"{temp_folder}/{hash_value}.svg").st_size
        time.sleep(0.01)
        timeout += 1
        if timeout == 1000:
            raise HTTPException(status_code=418, detail="Plotting timed out")
    return FileResponse(f"{temp_folder}/{hash_value}.svg")


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
