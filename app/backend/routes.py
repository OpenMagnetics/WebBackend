from flask import render_template, request, redirect, url_for, make_response, current_app, send_from_directory, jsonify
from app import app
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


def get_ip_location(ip_address):
    url = f'https://ipinfo.io/[{ip_address}]/json'
    response = urlopen(url)
    metadata = json.load(response)
    return metadata


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

