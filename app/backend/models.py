import sqlalchemy
import pandas
from sqlalchemy.ext.automap import automap_base
import bcrypt
import os
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, MetaData
import datetime
from typing import List, Optional, Any, Union
from enum import Enum
from pymongo import MongoClient
from bson import ObjectId, json_util
import json


class Harmonics(BaseModel):
    """Data containing the harmonics of the waveform, defined by a list of amplitudes and a list
    of frequencies
    """
    """List of amplitudes of the harmonics that compose the waveform"""
    amplitudes: List[float]
    """List of frequencies of the harmonics that compose the waveform"""
    frequencies: List[float]


class Label(Enum):
    """Label of the waveform, if applicable. Used for common waveforms"""
    flyback = "flyback"
    phaseshiftedfullbridge = "phase-shifted full bridge"
    sinusoidal = "sinusoidal"
    square = "square"
    squarewithdeadtime = "square with dead time"
    triangular = "triangular"


class ProcessedClass(BaseModel):
    """The duty cycle of the waveform, if applicable"""
    dutyCycle: Optional[float] = None
    """The effective frequency value of the waveform, according to
    https://sci-hub.wf/https://ieeexplore.ieee.org/document/750181, Appedix C
    """
    effectiveFrequency: Optional[float] = None
    """Label of the waveform, if applicable. Used for common waveforms"""
    label: Optional[Label] = None
    """The offset value of the waveform, referred to 0"""
    offset: Optional[float] = None
    """The peak to peak value of the waveform"""
    peakToPeak: Optional[float] = None
    """The RMS value of the waveform"""
    rms: Optional[float] = None
    """The Total Harmonic Distortion of the waveform, according to
    https://en.wikipedia.org/wiki/Total_harmonic_distortion
    """
    thd: Optional[float] = None


class Waveform(BaseModel):
    """Data containing the points that define an arbitrary waveform with equidistant points
    
    Data containing the points that define an arbitrary waveform with non-equidistant points
    paired with their time in the period
    """
    """List of values that compose the waveform, at equidistant times form each other"""
    data: List[float]
    """The number of periods covered by the data"""
    numberPeriods: Optional[int] = None
    time: Optional[List[float]] = None


class ElectromagneticParameter(BaseModel):
    """Structure definining one electromagnetic parameters: current, voltage, magnetic flux
    density
    """
    processed: Union[List[Any], bool, ProcessedClass, float, int, None, str]
    waveform: Waveform
    """Data containing the harmonics of the waveform, defined by a list of amplitudes and a list
    of frequencies
    """
    harmonics: Optional[Harmonics] = None


class OperationPoint(BaseModel):
    """The description of a magnetic operation point"""
    """Frequency of the waveform, common for all electromagnetic parameters, in Hz"""
    frequency: float
    current: Optional[ElectromagneticParameter] = None
    magneticField: Optional[ElectromagneticParameter] = None
    magneticFluxDensity: Optional[ElectromagneticParameter] = None
    """A label that identifies this Operation Point"""
    name: Optional[str] = None
    voltage: Optional[ElectromagneticParameter] = None
    username: str
    slug: Optional[str] = None


class OperationPointSlug(BaseModel):
    username: str
    slug: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


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
    def connect(self, schema='public'):
        raise NotImplementedError

    def disconnect(self):
        self.session.close()


class UsersTable(Database):

    def connect(self, schema='public'):
        driver = "postgresql"
        address = os.getenv('OM_USERS_DB_ADDRESS')
        port = os.getenv('OM_USERS_DB_PORT')
        name = os.getenv('OM_USERS_DB_NAME')
        user = os.getenv('OM_USERS_DB_USER')
        password = os.getenv('OM_USERS_DB_PASSWORD')

        self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

        metadata = sqlalchemy.MetaData()
        metadata.reflect(self.engine, schema=schema)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.users

    def username_exists(self, username):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.username == username)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return not data.empty

    def email_exists(self, email):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.email == email)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return not data.empty

    def get_user_id(self, username=None, user_id=None):
        self.connect()
        if username is not None:
            query = self.session.query(self.Table).filter(self.Table.username == username)
        else:
            query = self.session.query(self.Table).filter(self.Table.id == user_id)
        data = pandas.read_sql(query.statement, query.session.bind)
        if not data.empty:
            user_id = data.iloc[0]['id']
        else:
            user_id = None
        self.disconnect()
        return user_id

    def check_password(self, username, password):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.username == username)
        data = pandas.read_sql(query.statement, query.session.bind)
        if not data.empty:
            hashed_password = data.iloc[0]['password']
        else:
            hashed_password = None
        match = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        self.disconnect()
        return match

    def get_username(self, user_id):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.id == user_id)
        data = pandas.read_sql(query.statement, query.session.bind)
        if not data.empty:
            username = data.iloc[0]['username']
        else:
            username = None
        self.disconnect()
        return username

    def update_user(self, user_id, username, password, email):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.id == user_id)

        data = {
            'username': username,
            'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'email': email,
            'updated_at': datetime.datetime.now()
        }

        query = query.update(data)
        self.session.commit()
        self.disconnect()
        return True

    def insert_user(self, username, password, email):
        self.connect()
        data = {
            'username': username,
            'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'email': email,
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now()
        }
        row = self.Table(**data)
        self.session.add(row)
        self.session.flush()
        user_id = row.id
        self.session.commit()
        self.disconnect()
        return user_id


class RoadmapVotesTable(Database):
    def connect(self, schema='public'):
        path = os.path.join(os.getenv('LOCAL_DB_PATH'), os.getenv('LOCAL_DB_FILENAME'))
        os.makedirs(os.getenv('LOCAL_DB_PATH'), exist_ok=True)
        
        Base = declarative_base()
        self.engine = sqlalchemy.create_engine(f'sqlite:///{path}')

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


class OperationPointSlugsTable(Database):
    def connect(self, schema='public'):
        path = os.path.join(os.getenv('LOCAL_DB_PATH'), os.getenv('LOCAL_DB_FILENAME'))
        os.makedirs(os.getenv('LOCAL_DB_PATH'), exist_ok=True)
        
        Base = declarative_base()
        self.engine = sqlalchemy.create_engine(f'sqlite:///{path}')

        metadata = MetaData()
        Table(
            'operation_point_slugs', metadata, 
            Column('slug', String, primary_key=True), 
            Column('username', Integer)
        )

        metadata.create_all(self.engine)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.operation_point_slugs

    def slug_exists(self, slug):
        self.connect()
        query = self.session.query(self.Table.slug).filter(self.Table.slug == slug)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return not data.empty

    def get_slug_username(self, slug):
        self.connect()
        query = self.session.query(self.Table.username).filter(self.Table.slug == slug)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        if data.empty:
            return 0
        else:
            return int(data.values[0][0])

    def insert_slug(self, slug, username):
        self.connect()
        data = {
            'slug': slug,
            'username': username
        }
        row = self.Table(**data)
        self.session.add(row)
        self.session.flush()
        self.session.commit()
        query = self.session.query(self.Table)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return True


class OperationPointsTable(Database):

    def connect(self, schema='public'):
        driver = os.getenv('OM_OPERATION_POINTS_DB_DRIVER')
        address = os.getenv('OM_OPERATION_POINTS_DB_ADDRESS')
        user = os.getenv('OM_OPERATION_POINTS_DB_USER')
        password = os.getenv('OM_OPERATION_POINTS_DB_PASSWORD')

        # self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")
        self.session = MongoClient(f"{driver}://{user}:{password}@{address}/")

        self.database = self.session.OperationPoints

    def create_user_collection(self, username):
        self.connect()
        collection = self.database[username]
        self.disconnect()
        return collection

    def user_collection_exists(self, username):
        self.connect()
        collections = self.database.list_collection_names()
        self.disconnect()
        return username in collections

    def insert_operation_points(self, username, data):
        self.connect()
        result = self.database[username].insert_one(data)
        self.disconnect()
        return {"result": True,
                "operation_point_id": json.loads(json_util.dumps(result.inserted_id))['$oid']}

    def update_operation_points(self, username, data, operation_points_id):
        self.connect()
        _id = ObjectId(operation_points_id)
        result = self.database[username].replace_one({'_id': _id}, data, upsert=False)
        self.disconnect()
        return {"result": result.modified_count == 1,
                "operation_point_id": operation_points_id}

    def get_operation_point_by_id(self, username, operation_points_id):
        self.connect()
        _id = ObjectId(operation_points_id)
        data_read = pandas.DataFrame(self.database[username].find({"_id": _id}))
        self.disconnect()
        return data_read

    def delete_operation_points(self, operation_points_id):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.id == operation_points_id)

        data = {
            'deleted_at': datetime.datetime.now()
        }

        query = query.update(data)
        self.session.commit()
        self.disconnect()
        return True
