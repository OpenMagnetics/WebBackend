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
    milestone_id: int = None


class User(BaseModel):
    ip_address: str
    user_id: Optional[int] = None


class Milestone(BaseModel):
    milestone_id: int


class Username(BaseModel):
    username: Optional[str] = None


class MaterialNameOnly(BaseModel):
    name: str


class BugReport(BaseModel):
    userDataDump: dict
    userInformation: Optional[str] = None
    username: Optional[str] = None


class Database:
    def connect(self, schema='public'):
        raise NotImplementedError

    def disconnect(self):
        self.session.close()


class NotificationsTable(Database):

    def connect(self, schema='public'):
        driver = "postgresql"
        address = os.getenv('OM_DB_ADDRESS')
        port = os.getenv('OM_DB_PORT')
        name = os.getenv('OM_DB_NAME')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')

        self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

        metadata = sqlalchemy.MetaData()
        metadata.reflect(self.engine, schema=schema)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.notifications

    def read_active_notifications(self, datetime):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.starting_date < datetime)
        query = query.filter(sqlalchemy.or_(self.Table.ending_date >= datetime, self.Table.ending_date.is_(None)))
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return data


class UsersTable(Database):

    def connect(self, schema='public'):
        driver = "postgresql"
        address = os.getenv('OM_DB_ADDRESS')
        port = os.getenv('OM_DB_PORT')
        name = os.getenv('OM_DB_NAME')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')

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
        user_id = None if data.empty else data.iloc[0]['id']
        self.disconnect()
        return user_id

    def check_password(self, username, password):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.username == username)
        data = pandas.read_sql(query.statement, query.session.bind)
        hashed_password = None if data.empty else data.iloc[0]['password']
        match = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        self.disconnect()
        return match

    def get_username(self, user_id):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.id == user_id)
        data = pandas.read_sql(query.statement, query.session.bind)
        username = None if data.empty else data.iloc[0]['username']
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


class BugReportsTable(Database):

    def connect(self, schema='public'):
        driver = "postgresql"
        address = os.getenv('OM_DB_ADDRESS')
        port = os.getenv('OM_DB_PORT')
        name = os.getenv('OM_DB_NAME')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')

        self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

        metadata = sqlalchemy.MetaData()
        metadata.reflect(self.engine, schema=schema)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.bug_reports

    def report_bug(self, username, user_data, user_information):
        self.connect()
        data = {
            'username': username,
            'user_data': user_data,
            'user_information': user_information,
            'created_at': datetime.datetime.now()
        }
        row = self.Table(**data)
        self.session.add(row)
        self.session.flush()
        bug_report_id = row.index
        self.session.commit()
        self.disconnect()
        return bug_report_id


class DataTable(Database):

    def connect(self, schema='public'):
        driver = os.getenv('OM_DB_DRIVER')
        address = os.getenv('OM_DB_ADDRESS')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')

        self.session = MongoClient(f"{driver}://{user}:{password}@{address}/")

        self.database = self.get_table()

    def get_table(self):
        raise NotImplementedError

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

    def insert_data(self, username, data):
        self.connect()
        result = self.database[username].insert_one(data)
        self.disconnect()
        return {"result": True,
                "id": json.loads(json_util.dumps(result.inserted_id))['$oid']}

    def update_data(self, username, data, id):
        self.connect()
        _id = ObjectId(id)
        result = self.database[username].replace_one({'_id': _id}, data, upsert=False)
        self.disconnect()
        return {"result": result.modified_count == 1,
                "id": id}

    def get_data_by_id(self, username, id):
        self.connect()
        _id = ObjectId(id)
        data_read = pandas.DataFrame(self.database[username].find({"_id": _id}))
        return self.clean_time_columns(data_read)

    def get_data_by_slug(self, username, slug):
        self.connect()
        data_read = pandas.DataFrame(self.database[username].find({"slug": slug}))
        return self.clean_time_columns(data_read)

    def get_data_by_username(self, username):
        self.connect()
        data_read = pandas.DataFrame(self.database[username].find({'deleted_at': {"$eq": None}}))
        return self.clean_time_columns(data_read)

    # TODO Rename this here and in `get_data_by_id`, `get_data_by_slug` and `get_data_by_username`
    def clean_time_columns(self, data_read):
        self.disconnect()
        data_read = data_read.drop('updated_at', axis=1, errors='ignore')
        data_read = data_read.drop('deleted_at', axis=1, errors='ignore')
        data_read = data_read.drop('created_at', axis=1, errors='ignore')
        return data_read

    def get_count_by_username(self, username):
        self.connect()
        count = self.database[username].count_documents({'deleted_at': {"$eq": None}})
        self.disconnect()
        return count

    def delete_data_by_id(self, username, id):
        self.connect()
        _id = ObjectId(id)
        result = self.database[username].update_one({'_id': _id}, {"$set": {"deleted_at": datetime.datetime.now()}})
        self.disconnect()
        return {"result": result.modified_count == 1,
                "id": id}


class MasTable(Database):

    def connect(self, schema='public'):
        driver = "postgresql"
        address = os.getenv('OM_DB_ADDRESS')
        port = os.getenv('OM_DB_PORT')
        name = os.getenv('OM_DB_NAME')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')

        self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

        metadata = sqlalchemy.MetaData()
        metadata.reflect(self.engine, schema=schema)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.mas

    def insert_mas(self, mas):
        self.connect()
        data = {
            'mas': mas,
            'created_at': datetime.datetime.now()
        }
        row = self.Table(**data)
        self.session.add(row)
        self.session.flush()
        mas_id = row.index
        self.session.commit()
        self.disconnect()
        return mas_id


class IntermediateMasTable(Database):

    def connect(self, schema='public'):
        driver = "postgresql"
        address = os.getenv('OM_DB_ADDRESS')
        port = os.getenv('OM_DB_PORT')
        name = os.getenv('OM_DB_NAME')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')

        self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

        metadata = sqlalchemy.MetaData()
        metadata.reflect(self.engine, schema=schema)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.intermediate_mas

    def insert_mas(self, mas):
        self.connect()
        data = {
            'mas': mas,
            'created_at': datetime.datetime.now()
        }
        row = self.Table(**data)
        self.session.add(row)
        self.session.flush()
        mas_id = row.index
        self.session.commit()
        self.disconnect()
        return mas_id


class CoreMaterialsTable(Database):

    def connect(self, schema='public'):
        driver = "postgresql"
        address = os.getenv('OM_DB_ADDRESS')
        port = os.getenv('OM_DB_PORT')
        name = os.getenv('OM_DB_NAME')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')

        self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

        metadata = sqlalchemy.MetaData()
        metadata.reflect(self.engine, schema=schema)
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.advanced_core_materials

    def read_material_by_name(self, material_name):
        self.connect()
        query = self.session.query(self.Table).filter(self.Table.name == material_name)
        data = pandas.read_sql(query.statement, query.session.bind)
        self.disconnect()
        return data.to_dict('records')[0]
