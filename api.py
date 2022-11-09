from fastapi import FastAPI
from app.backend.models import UsersTable, RoadmapVotesTable, OperationPointsTable, OperationPointSlugsTable
from app.backend.models import Vote, Milestone, UserLogin, UserRegister, OperationPoint, OperationPointSlug
from fastapi.middleware.cors import CORSMiddleware


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


@app.post("/get_number_votes")
def get_number_votes(data: Milestone):
    number_votes = RoadmapVotesTable().get_number_votes(**data.dict())
    return {"number_votes": number_votes}


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
        return{"status": "registered", "user_id": user_id}


@app.post("/operation_point_save")
@app.post("/operation_point_save/{operation_point_id}")
def operation_point_save(data: OperationPoint, operation_point_id: str = None):
    data = data.dict()
    operation_points_table = OperationPointsTable()
    operation_points_table.connect()
    username = data.pop("username")
    if not operation_points_table.user_collection_exists(username):
        operation_points_table.create_user_collection(username)
    if operation_point_id is None:
        result = operation_points_table.insert_operation_points(username, delete_none(data))
    else:
        result = operation_points_table.update_operation_points(username, delete_none(data), operation_point_id)
    if result["result"] is not None:
        return {"status": "saved", "operation_point_id": result["operation_point_id"]}
    else:
        return {"status": "error saving"}


@app.post("/operation_point_publish")
def operation_point_publish(data: OperationPointSlug):
    data = data.dict()
    operation_points_table = OperationPointsTable()
    operation_points_slugs_table = OperationPointSlugsTable()
    operation_points_table.connect()
    username = data.pop("username")
    slug = data["slug"]
    if operation_points_slugs_table.slug_exists(slug):
        return {"status": "slug exists", "slug": slug}
    else:
        operation_points_slugs_table.insert_slug(slug, username)
        return {"status": "published", "slug": slug}
