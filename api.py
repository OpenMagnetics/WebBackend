from fastapi import FastAPI, Request, HTTPException
from app.backend.models import UsersTable, NotificationsTable, BugReportsTable, RoadmapVotesTable, OperationPointsTable, CoresTable, BobbinsTable, WiresTable, MagneticsTable
from app.backend.models import OperationPointSlugsTable, CoreSlugsTable, BobbinSlugsTable, WireSlugsTable, MagneticSlugsTable
from app.backend.models import Vote, Milestone, UserLogin, UserRegister, OperationPoint, OperationPointSlug, Username, BugReport, MaterialNameOnly
from app.backend.mas_models import MagneticCore, CoreShape, CoreGap, CoreFunctionalDescription, Mas
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import pandas
from datetime import datetime
import json
import bson
import sys
from bson import ObjectId, json_util
import numpy
import copy
import pprint
import os
import pathlib
import base64
from typing import List, Union
from pylatex import Document, Section, Subsection, Command, Package
from pylatex.utils import italic, NoEscape


sys.path.append("../MVB/src")
from builder import Builder as ShapeBuilder  # noqa: E402


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


@app.post("/are_vote_casted", include_in_schema=False)
def are_vote_casted(data: Vote):
    vote = RoadmapVotesTable().are_vote_casted(**data.dict())
    return {"voted_milestones": vote.to_dict('records')}


@app.post("/get_number_votes", include_in_schema=False)
def get_number_votes():
    number_votes = RoadmapVotesTable().get_all_number_votes()
    return {"number_votes": number_votes.to_dict('records')}


@app.post("/get_all_number_votes", include_in_schema=False)
def get_all_number_votes():
    number_votes = RoadmapVotesTable().get_all_number_votes()
    number_votes = number_votes.to_dict('records')
    return number_votes


@app.post("/cast_vote", include_in_schema=False)
def cast_vote(data: Vote):
    roadmap_votes_table = RoadmapVotesTable()
    if roadmap_votes_table.is_vote_casted(**data.dict()):
        return {"voted": False}
    vote = roadmap_votes_table.insert_vote(**data.dict())
    return {"voted": vote}


@app.post("/get_notifications", include_in_schema=False)
def get_notifications():
    notifications_table = NotificationsTable()
    new_notifications = notifications_table.read_active_notifications(datetime.now())
    return{"notifications": new_notifications.to_dict('records')}


@app.post("/report_bug", include_in_schema=False)
def report_bug(data: BugReport):
    data = data.dict()

    bug_reports_table = BugReportsTable()
    bug_report_id = bug_reports_table.report_bug(data['username'], data['userDataDump'], data['userInformation'])
    return{"status": "reported", "bug_report_id": bug_report_id}


@app.post("/login", include_in_schema=False)
def login(data: UserLogin):
    data = data.dict()
    user_table = UsersTable()
    if not user_table.username_exists(data['username']):
        return{"status": "unknown username", "username": data['username']}
    if user_table.check_password(data['username'], data['password']):
        return{"status": "logged in", "username": data['username']}
    else:
        return{"status": "wrong password"}


@app.post("/register", include_in_schema=False)
def register(data: UserRegister):
    data = data.dict()
    user_table = UsersTable()
    if user_table.username_exists(data['username']):
        return{"status": "username exists", "username": data['username']}
    elif user_table.email_exists(data['email']):
        return{"status": "email exists", "email": data['email']}
    else:
        user_id = user_table.insert_user(**data)
        return{"status": "registered", "user_id": user_id, "username": data['username']}


@app.post("/operation_point_save", include_in_schema=False)
@app.post("/operation_point_save/{id}", include_in_schema=False)
@app.post("/core_save", include_in_schema=False)
@app.post("/core_save/{id}", include_in_schema=False)
@app.post("/bobbin_save", include_in_schema=False)
@app.post("/bobbin_save/{id}", include_in_schema=False)
@app.post("/wire_save", include_in_schema=False)
@app.post("/wire_save/{id}", include_in_schema=False)
@app.post("/magnetic_save", include_in_schema=False)
@app.post("/magnetic_save/{id}", include_in_schema=False)
async def save(request: Request, id: str = None):
    table = get_table(request.url._url)
    data = await request.json()
    username = data.pop("username")
    data = delete_none(data)
    data["updated_at"] = datetime.now()
    data["deleted_at"] = None
    if not table.user_collection_exists(username):
        table.create_user_collection(username)
    if id is None:
        data["created_at"] = datetime.now()
        result = table.insert_data(username, data)
    else:
        result = table.update_data(username, data, id)
    if result["result"] is not None:
        return {"status": "saved", "id": result["id"]}
    else:
        return {"status": "error saving"}


@app.post("/operation_point_publish", include_in_schema=False)
@app.post("/core_publish", include_in_schema=False)
@app.post("/bobbin_publish", include_in_schema=False)
@app.post("/wire_publish", include_in_schema=False)
@app.post("/magnetic_publish", include_in_schema=False)
def operation_point_publish(data: OperationPointSlug, request: Request):
    data = data.dict()
    slugs_table = get_table_slug(request.url._url)
    username = data.pop("username")
    slug = data["slug"]
    if slugs_table.slug_exists(slug):
        return {"status": "slug exists", "slug": slug}
    slugs_table.insert_slug(slug, username)
    return {"status": "published", "slug": slug}


@app.post("/operation_point_load", include_in_schema=False)
@app.post("/operation_point_load/{element_id_or_slug}", include_in_schema=False)
@app.post("/core_load", include_in_schema=False)
@app.post("/core_load/{element_id_or_slug}", include_in_schema=False)
@app.post("/bobbin_load", include_in_schema=False)
@app.post("/bobbin_load/{element_id_or_slug}", include_in_schema=False)
@app.post("/wire_load", include_in_schema=False)
@app.post("/wire_load/{element_id_or_slug}", include_in_schema=False)
@app.post("/magnetic_load", include_in_schema=False)
@app.post("/magnetic_load/{element_id_or_slug}", include_in_schema=False)
def operation_point_load(username: Username, request: Request, element_id_or_slug: str = None):
    table = get_table(request.url._url)
    username = username.dict()["username"]

    # checking if is slug or id
    try:
        _id = ObjectId(element_id_or_slug)
        new_id = json.loads(json_util.dumps(_id))['$oid']
        is_id = element_id_or_slug == new_id
    except bson.errors.InvalidId:
        is_id = False

    if element_id_or_slug is None:
        if not table.user_collection_exists(username):
            table.create_user_collection(username)

        result = table.get_data_by_username(username)
        if result.empty:
            return {"elements": []}
        result = result.where(pandas.notnull(result), None)
        result["_id"] = result["_id"].astype(str)
        return {"elements": result.to_dict('records')}
    else:
        if is_id:
            if not table.user_collection_exists(username):
                table.create_user_collection(username)

            result = table.get_data_by_id(username, element_id_or_slug)
        else:
            slugs_table = get_table_slug(request.url._url)

            if not slugs_table.slug_exists(element_id_or_slug):
                return None
            username = slugs_table.get_slug_username(element_id_or_slug)
            if not table.user_collection_exists(username):
                return None
            result = table.get_data_by_slug(username, element_id_or_slug)
        result = result.where(pandas.notnull(result), None)
        result["_id"] = result["_id"].astype(str)
        return {"element": result.to_dict('records')[0]}


@app.post("/operation_point_count", include_in_schema=False)
@app.post("/core_count", include_in_schema=False)
@app.post("/bobbin_count", include_in_schema=False)
@app.post("/wire_count", include_in_schema=False)
@app.post("/magnetic_count", include_in_schema=False)
def count(username: Username, request: Request):
    table = get_table(request.url._url)
    username = username.dict()["username"]

    if username is None:
        return None

    if not table.user_collection_exists(username):
        table.create_user_collection(username)

    count = table.get_count_by_username(username)
    return {"count": count}


@app.post("/operation_point_delete/{element_id}", include_in_schema=False)
@app.post("/core_delete/{element_id}", include_in_schema=False)
@app.post("/bobbin_delete/{element_id}", include_in_schema=False)
@app.post("/wire_delete/{element_id}", include_in_schema=False)
@app.post("/magnetic_delete/{element_id}", include_in_schema=False)
def operation_point_delete(username: Username, request: Request, element_id: str = None):
    table = get_table(request.url._url)
    username = username.dict()["username"]

    if not table.user_collection_exists(username):
        return {"id": None}
    result = table.delete_data_by_id(username, element_id)

    # Clean slugs
    operation_points_slugs_table = OperationPointSlugsTable()
    slugs = operation_points_slugs_table.get_all_slugs()
    slugs_by_username = slugs.groupby(["username"])
    for username, group in slugs_by_username:
        data = table.get_data_by_username(username)
        if not data.empty and "slug" in data:
            slugs_in_username = list(data["slug"].values)
            for index, row in group.iterrows():
                if row["slug"] not in slugs_in_username:
                    print("Slug to delete:", row["slug"])
                    operation_points_slugs_table.delete_slug(row["slug"])
    return {"id": result["id"]} if result["result"] else {"id": None}


@app.post("/core_get_families", include_in_schema=False)
def core_get_families():
    families = ShapeBuilder().get_families()
    return {"families": families}


@app.post("/core_compute_shape_obj", include_in_schema=False)
@app.post("/core_compute_shape", include_in_schema=False)
def core_compute_shape(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder().factory(coreShape)
    core_builder.set_output_path(f"{os.getenv('LOCAL_DB_PATH')}/temp")    
    step_path, obj_path = core_builder.get_piece(coreShape)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(obj_path)


@app.post("/core_compute_shape_stp", include_in_schema=False)
def core_compute_shape_stp(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder().factory(coreShape)
    core_builder.set_output_path(f"{os.getenv('LOCAL_DB_PATH')}/temp")    
    step_path, obj_path = core_builder.get_piece(coreShape)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(step_path)


@app.post("/core_compute_core_3d_model_obj", include_in_schema=False)
@app.post("/core_compute_core_3d_model", include_in_schema=False)
async def core_compute_core_3d_model(request: Request):
    json = await request.json()
    if 'familySubtype' in json['functionalDescription']['shape']:
        json['functionalDescription']['shape']['familySubtype'] = str(json['functionalDescription']['shape']['familySubtype'])

    core = MagneticCore(**json)
    core = core.dict()

    core = clean_dimensions(core)
    if not isinstance(core['functionalDescription']['material'], str):
        core['functionalDescription']['material'] = core['functionalDescription']['material']['name']

    pprint.pprint(core)
    step_path, obj_path = ShapeBuilder().get_core(project_name=core['functionalDescription']['shape']['name'],
                                                  geometrical_description=core['geometricalDescription'],
                                                  output_path=f"{os.getenv('LOCAL_DB_PATH')}/temp")
    print(step_path)
    print(obj_path)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(obj_path)


@app.post("/core_compute_core_3d_model_stp", include_in_schema=False)
async def core_compute_core_3d_model_stp(request: Request):
    json = await request.json()
    if 'familySubtype' in json['functionalDescription']['shape']:
        json['functionalDescription']['shape']['familySubtype'] = str(json['functionalDescription']['shape']['familySubtype'])

    core = MagneticCore(**json)
    core = core.dict()

    core = clean_dimensions(core)
    step_path, obj_path = ShapeBuilder().get_core(project_name=core['functionalDescription']['shape']['name'],
                                                  geometrical_description=core['geometricalDescription'],
                                                  output_path=f"{os.getenv('LOCAL_DB_PATH')}/temp")
    # print(step_path)
    # print(obj_path)
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
    core_builder.set_output_path(f"{os.getenv('LOCAL_DB_PATH')}/temp")
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

@app.post("/read_mas_database", include_in_schema=False)
def read_mas_database():
    core_materials = pandas.read_json(f'{os.path.dirname(os.path.abspath(__file__))}/../MAS/data/core_materials.ndjson', lines=True).fillna('')
    core_shapes = pandas.read_json(f'{os.path.dirname(os.path.abspath(__file__))}/../MAS/data/core_shapes.ndjson', lines=True).fillna('')
    wires = pandas.read_json(f'{os.path.dirname(os.path.abspath(__file__))}/../MAS/data/wires.ndjson', lines=True).fillna('')
    bobbins = pandas.read_json(f'{os.path.dirname(os.path.abspath(__file__))}/../MAS/data/bobbins.ndjson', lines=True).fillna('')
    insulation_materials = pandas.read_json(f'{os.path.dirname(os.path.abspath(__file__))}/../MAS/data/insulation_materials.ndjson', lines=True).fillna('')
    wire_materials = pandas.read_json(f'{os.path.dirname(os.path.abspath(__file__))}/../MAS/data/wire_materials.ndjson', lines=True).fillna('')
    core_shapes = core_shapes[(core_shapes['family'] != 'ui') & (core_shapes['family'] != 'pqi')]
    return {
        'coreMaterials': core_materials.to_dict('records'),
        'coreShapes': core_shapes.to_dict('records'),
        'wires': wires.to_dict('records'),
        'bobbins': bobbins.to_dict('records'),
        'insulationMaterials': insulation_materials.to_dict('records'),
        'wireMaterials': wire_materials.to_dict('records'),
    }

@app.post("/read_mas_inventory", include_in_schema=False)
def read_mas_inventory():
    cores = pandas.read_json(f'{os.path.dirname(os.path.abspath(__file__))}/../MAS/data/cores_stock.ndjson', lines=True).fillna('')

    cores = cores[cores.apply(lambda row: len(row['distributorsInfo']) > 1, axis=1)]
    print(len(cores.index))

    return {
        'cores': cores.to_dict('records'),
    }

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
    doc.preamble.append(Command('setlength\cellspacetoplimit', '4pt'))
    doc.preamble.append(Command('setlength\cellspacebottomlimit', '4pt'))
    doc.preamble.append(Command('usetikzlibrary', 'datavisualization'))
    doc.preamble.append(Command('geometry', 'tmargin=1in'))
    doc.preamble.append(Command('pagestyle', 'fancy'))
    tex = tex.replace('μ', '$\mu$')
    doc.append(NoEscape(tex))
    doc.generate_pdf(clean_tex=False)

    with open(f"{filepath}/tex.pdf", "rb") as pdf_file:
        pdf_string = base64.b64encode(pdf_file.read())
        return pdf_string