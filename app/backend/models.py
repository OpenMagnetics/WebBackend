import sqlalchemy
import pandas
from sqlalchemy.ext.automap import automap_base
from flask_login import UserMixin
import bcrypt
import os
import datetime
from pydantic import BaseModel
from typing import Optional, Union, List
from app import app
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Integer, String, Table, MetaData
import sqlite3
import shutil


class Vote(BaseModel):
    ip_address: str
    user_id: Optional[int] = None
    milestone_id: int


class User(BaseModel):
    ip_address: str
    user_id: Optional[int] = None


class Milestone(BaseModel):
    milestone_id: int


class Database:

    # def __init__(self):
    #     driver = "postgresql"
    #     address = app.config['AUTOP_DB_ADDRESS']
    #     port = app.config['AUTOP_DB_PORT']
    #     name = app.config['AUTOP_DB_NAME']
    #     user = app.config['AUTOP_DB_USER']
    #     password = app.config['AUTOP_DB_PASSWORD']

    #     self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

    def connect(self, schema='public'):
        raise NotImplementedError

    def disconnect(self):
        self.session.close()


class RoadmapVotesTable(Database):
    def connect(self, schema='public'):
        path = os.path.join(app.config['LOCAL_DB_PATH'], app.config['LOCAL_DB_FILENAME'])
        os.makedirs(app.config['LOCAL_DB_PATH'], exist_ok=True)
        
        Base = declarative_base()
        print(f'sqlite:///{path}')
        self.engine = sqlalchemy.create_engine(f'sqlite:///{path}', echo=True)

        metadata = MetaData()
        Table(
            'milestone_voting', metadata, 
            Column('id', Integer, primary_key=True), 
            Column('ip_address', String), 
            Column('user_id', Integer),
            Column('milestone_id', Integer),
        )

        metadata.create_all(self.engine)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.milestone_voting

    def is_vote_casted(self, ip_address, user_id, milestone_id):
        self.connect()
        query = self.session.query(self.Table.milestone_id).filter(self.Table.milestone_id == milestone_id)
        if user_id is None:
            query = query.filter(self.Table.ip_address == ip_address)
        else:
            query = query.filter(self.Table.user_id == user_id)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return not data.empty

    def get_number_votes(self, milestone_id):
        self.connect()
        query = self.session.query(sqlalchemy.func.count()).filter(self.Table.milestone_id == milestone_id)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        if data.empty:
            return 0
        else:
            return int(data.values[0][0])

    def get_all_number_votes(self):
        self.connect()
        query = self.session.query(self.Table.milestone_id, sqlalchemy.func.count(self.Table.milestone_id).label("count"))
        query = query.group_by(self.Table.milestone_id).order_by(sqlalchemy.desc("count"))
        data = pandas.read_sql(query.statement, query.session.bind)
        # data = engine.execute(query).fetchall()
        self.disconnect()
        return data

    def insert_vote(self, ip_address, user_id, milestone_id):
        self.connect()
        data = {
            'ip_address': ip_address,
            'user_id': user_id,
            'milestone_id': milestone_id
        }
        row = self.Table(**data)
        self.session.add(row)
        self.session.flush()
        self.session.commit()
        query = self.session.query(self.Table)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return True
