from flask import render_template, request, redirect, url_for, make_response, current_app, send_from_directory, jsonify
from app import app
from app.backend.models import Vote, RoadmapVotesTable, User, Milestone
from email_validator import validate_email, EmailNotValidError
from urllib.request import urlopen
import json
import os
import sys
import base64
import sqlalchemy
import glob
import zipfile
import shutil
import time


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html')


@app.route('/musings', methods=['GET', 'POST'])
def musings_menu():
    return render_template('musings.html')


@app.route('/musings<int:chapter>', methods=['GET', 'POST'])
def musings(chapter):
    return render_template(f'musings/musings{chapter}.html')


@app.route('/roadmap', methods=['GET', 'POST'])
def roadmap():
    return render_template('roadmap.html')


@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    data = Vote(**request.json).dict()
    roadmap_votes_table = RoadmapVotesTable()
    if roadmap_votes_table.is_vote_casted(**data):
        return {"voted": False}
    else:
        vote = roadmap_votes_table.insert_vote(**data)
        return {"voted": vote}


@app.route('/is_vote_casted', methods=['POST'])
def is_vote_casted():
    data = Vote(**request.json).dict()
    vote = RoadmapVotesTable().is_vote_casted(**data)
    return {"already_voted": vote}


@app.route('/get_number_votes', methods=['POST'])
def get_number_votes():
    data = Milestone(**request.json).dict()
    number_votes = RoadmapVotesTable().get_number_votes(**data)
    return {"number_votes": number_votes}


@app.route('/get_all_number_votes', methods=['POST'])
def get_all_number_votes():
    number_votes = RoadmapVotesTable().get_all_number_votes()
    print("number_votes")
    print(number_votes)
    number_votes = number_votes.to_dict('records')
    return make_response(json.dumps(number_votes))
