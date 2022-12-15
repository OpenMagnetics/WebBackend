from fastapi import FastAPI, Request, HTTPException
from app.backend.models import UsersTable, RoadmapVotesTable, OperationPointsTable, CoresTable, BobbinsTable, WiresTable, MagneticsTable
from app.backend.models import OperationPointSlugsTable, CoreSlugsTable, BobbinSlugsTable, WireSlugsTable, MagneticSlugsTable
from app.backend.models import Vote, Milestone, UserLogin, UserRegister, OperationPoint, OperationPointSlug, Username
from app.backend.core_models import Core, CoreShape, CoreGap
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas
from datetime import datetime
import json
import bson
import sys
from bson import ObjectId, json_util
import PyMKF
import numpy
import copy
import pprint
import os
from typing import List

sys.path.append("../MVB/src")
from builder import Builder as ShapeBuilder  # noqa: E402


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
    dim = {}
    for k, v in dimensions.items():
        dim[k] = v["nominal"]

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
    "http://localhost:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/is_vote_casted")
def is_vote_casted(data: Vote):
    vote = RoadmapVotesTable().is_vote_casted(**data.dict())
    return {"already_voted": vote}


@app.post("/are_vote_casted")
def are_vote_casted(data: Vote):
    vote = RoadmapVotesTable().are_vote_casted(**data.dict())
    return {"voted_milestones": vote.to_dict('records')}


@app.post("/get_number_votes")
def get_number_votes():
    number_votes = RoadmapVotesTable().get_all_number_votes()
    return {"number_votes": number_votes.to_dict('records')}


@app.post("/get_all_number_votes")
def get_all_number_votes():
    number_votes = RoadmapVotesTable().get_all_number_votes()
    number_votes = number_votes.to_dict('records')
    return number_votes


@app.post("/cast_vote")
def cast_vote(data: Vote):
    roadmap_votes_table = RoadmapVotesTable()
    if roadmap_votes_table.is_vote_casted(**data.dict()):
        return {"voted": False}
    else:
        vote = roadmap_votes_table.insert_vote(**data.dict())
        return {"voted": vote}


@app.post("/login")
def login(data: UserLogin):
    data = data.dict()
    user_table = UsersTable()
    if user_table.username_exists(data['username']):
        if user_table.check_password(data['username'], data['password']):
            return{"status": "logged in", "username": data['username']}
        else:
            return{"status": "wrong password"}
    else:
        return{"status": "unknown username", "username": data['username']}


@app.post("/register")
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


@app.post("/operation_point_save")
@app.post("/operation_point_save/{id}")
@app.post("/core_save")
@app.post("/core_save/{id}")
@app.post("/bobbin_save")
@app.post("/bobbin_save/{id}")
@app.post("/wire_save")
@app.post("/wire_save/{id}")
@app.post("/magnetic_save")
@app.post("/magnetic_save/{id}")
def operation_point_save(data: OperationPoint, request: Request, id: str = None):
    table = get_table(request.url._url)
    data = data.dict()
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


@app.post("/operation_point_publish")
@app.post("/core_publish")
@app.post("/bobbin_publish")
@app.post("/wire_publish")
@app.post("/magnetic_publish")
def operation_point_publish(data: OperationPointSlug, request: Request):
    data = data.dict()
    slugs_table = get_table_slug(request.url._url)
    username = data.pop("username")
    slug = data["slug"]
    if slugs_table.slug_exists(slug):
        return {"status": "slug exists", "slug": slug}
    else:
        slugs_table.insert_slug(slug, username)
        return {"status": "published", "slug": slug}


@app.post("/operation_point_load")
@app.post("/operation_point_load/{element_id_or_slug}")
@app.post("/core_load")
@app.post("/core_load/{element_id_or_slug}")
@app.post("/bobbin_load")
@app.post("/bobbin_load/{element_id_or_slug}")
@app.post("/wire_load")
@app.post("/wire_load/{element_id_or_slug}")
@app.post("/magnetic_load")
@app.post("/magnetic_load/{element_id_or_slug}")
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
            result = result.where(pandas.notnull(result), None)
            result["_id"] = result["_id"].astype(str)
            return {"element": result.to_dict('records')[0]}

        else:
            slugs_table = get_table_slug(request.url._url)

            if slugs_table.slug_exists(element_id_or_slug):
                username = slugs_table.get_slug_username(element_id_or_slug)
                if not table.user_collection_exists(username):
                    return None
                result = table.get_data_by_slug(username, element_id_or_slug)
                result = result.where(pandas.notnull(result), None)
                result["_id"] = result["_id"].astype(str)
                return {"element": result.to_dict('records')[0]}
            else:
                return None


@app.post("/operation_point_count")
@app.post("/core_count")
@app.post("/bobbin_count")
@app.post("/wire_count")
@app.post("/magnetic_count")
def count(username: Username, request: Request):
    table = get_table(request.url._url)
    username = username.dict()["username"]

    if username is None:
        return None

    if not table.user_collection_exists(username):
        table.create_user_collection(username)

    count = table.get_count_by_username(username)
    return {"count": count}


@app.post("/operation_point_delete/{element_id}")
@app.post("/core_delete/{element_id}")
@app.post("/bobbin_delete/{element_id}")
@app.post("/wire_delete/{element_id}")
@app.post("/magnetic_delete/{element_id}")
def operation_point_delete(username: Username, request: Request, element_id: str = None):
    table = get_table(request.url._url)
    username = username.dict()["username"]

    if not table.user_collection_exists(username):
        return {"id": None}
    else:
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
        if result["result"]:
            return {"id": result["id"]}
        else:
            return {"id": None}


@app.post("/core_get_families")
def core_get_families():
    families = ShapeBuilder().get_families()
    return {"families": families}


@app.post("/core_get_commercial_data")
def core_get_commercial_data():
    commercial_data = pandas.read_json('../MAS/data/shapes.ndjson', lines=True)
    commercial_data = commercial_data.where(pandas.notnull(commercial_data), None)
    commercial_data = commercial_data.replace({numpy.nan: None})

    core_data = pandas.DataFrame()
    dummyCore = {
        "functionalDescription": {
            "name": "dummy",
            "type": "two-piece set",
            "material": "N97",
            "shape": None,
            "gapping": [],
            "numberStacks": 1
        }
    }
    for index, row in commercial_data.iterrows():
        if row['family'] not in ['ui']:
            datum = flatten_dimensions(row.to_dict()) 
            if "familySubtype" in datum and datum["familySubtype"] is not None:
                datum["familySubtype"] = str(int(datum["familySubtype"]))
            core = copy.deepcopy(dummyCore)
            if row['family'] in ['ut']:
                core['functionalDescription']['type'] = "closed shape"
            core['functionalDescription']['shape'] = datum

            core_datum = PyMKF.get_core_data(core)
            core_data = pandas.concat([core_data, pandas.DataFrame.from_records([core_datum])])

    return {"commercial_data": core_data.to_dict('records')}


@app.post("/core_compute_shape")
def core_compute_shape(coreShape: CoreShape):
    coreShape = coreShape.dict()
    core_builder = ShapeBuilder().factory(coreShape)
    core_builder.set_output_path(f"{os.getenv('LOCAL_DB_PATH')}/temp")    
    step_path, obj_path = core_builder.get_piece(coreShape)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(obj_path)


@app.post("/core_compute_core_3d_model")
def core_compute_core_3d_model(core: Core):

    core = core.dict()

    core_datum = PyMKF.get_core_data(core)
    pprint.pprint(core)
    step_path, obj_path = ShapeBuilder().get_core(project_name=core_datum['functionalDescription']['shape']['name'],
                                                  geometrical_description=core_datum['geometricalDescription'],
                                                  output_path=f"{os.getenv('LOCAL_DB_PATH')}/temp")
    print(step_path)
    print(obj_path)
    if step_path is None:
        raise HTTPException(status_code=418, detail="Wrong dimensions")
    else:
        return FileResponse(obj_path)


@app.post("/core_compute_technical_drawing")
def core_compute_technical_drawing(coreShape: CoreShape):
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


@app.post("/core_compute_core_parameters")
def core_compute_core_parameters(core: Core):
    core = core.dict()
    # pprint.pprint("core")
    # pprint.pprint(core)
    core_datum = PyMKF.get_core_data(core)
    # pprint.pprint("core_datum")
    # pprint.pprint(core_datum)
    return core_datum


@app.post("/core_compute_gap_reluctances")
async def core_compute_gap_reluctances(request: Request):
    json = await request.json()
    model = json["model"]
    gapping = json["gapping"]
    gapping_data = []
    for index in range(0, len(gapping)):
        gapping_data.append(PyMKF.get_gap_reluctance(gapping[index], model.upper().replace(" ", "_")))

    return gapping_data


@app.post("/get_constants")
def get_constants():
    constants = PyMKF.get_constants()
    return constants


@app.post("/get_gap_reluctance_models")
def get_gap_reluctance_models():
    models_info = PyMKF.get_gap_reluctance_model_information()
    return models_info
