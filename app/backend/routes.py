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


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template("index.html")


@app.route('/musings', methods=['GET', 'POST'])
def musings():
    return render_template('musings.html')


@app.route('/musings1', methods=['GET', 'POST'])
def musings1():
    return render_template('musings/musings1.html')


@app.route('/musings2', methods=['GET', 'POST'])
def musings2():
    return render_template('musings/musings2.html')


@app.route('/musings3', methods=['GET', 'POST'])
def musings3():
    return render_template('musings/musings3.html')


@app.route('/musings5', methods=['GET', 'POST'])
def musings5():
    return render_template('musings/musings5.html')
