from typing import Optional, Union, List
from fastapi import FastAPI, Body, Request
from fastapi.encoders import jsonable_encoder
import shutil
import base64
import os
import json
from app.backend.models import UsersTable, RoadmapVotesTable, OperationPointsTable, OperationPointSlugsTable
from app.backend.models import Vote, Milestone, UserLogin, UserRegister, OperationPoint, OperationPointSlug
from fastapi.middleware.cors import CORSMiddleware


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
    return json.dumps(number_votes)


@app.post("/cast_vote")
def cast_vote(data: Vote):
    roadmap_votes_table = RoadmapVotesTable()
    if roadmap_votes_table.is_vote_casted(**data.dict()):
        return {"voted": False}
    else:
        vote = roadmap_votes_table.insert_vote(**data.dict())
        return {"voted": vote}
