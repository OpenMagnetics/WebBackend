import sqlalchemy
from sqlalchemy.ext.automap import automap_base
import os
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
import datetime
from typing import Optional
import json
import hashlib
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound


class BugReport(BaseModel):
    userDataDump: dict
    userInformation: Optional[str] = None
    username: Optional[str] = None


class Database:
    def connect(self, schema='public'):
        raise NotImplementedError

    def disconnect(self):
        self.session.close()


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


class TelemetryTable(Database):
    """Normalised design telemetry as a small star schema in the `telemetry`
    Postgres schema: one `sessions` row per browser tab, deduplicated MAS
    payloads in `designs` (keyed by content hash), and a thin `events` stream
    that references both. Lets us analyse which topologies, inputs and magnetic
    designs people actually use, and tell intermediate working state apart from
    finished designs via `events.stage` ('intermediate' | 'final')."""

    def connect(self):
        driver = "postgresql"
        address = os.getenv('OM_DB_ADDRESS')
        port = os.getenv('OM_DB_PORT')
        name = os.getenv('OM_DB_NAME')
        user = os.getenv('OM_DB_USER')
        password = os.getenv('OM_DB_PASSWORD')
        self.engine = sqlalchemy.create_engine(f"{driver}://{user}:{password}@{address}:{port}/{name}")

    def disconnect(self):
        self.engine.dispose()

    def record(self, session_id, event_type, source, stage=None, environment='production',
               app_version=None, mas_data=None, topology=None, mas_version=None,
               result_count=None, error_message=None):
        self.connect()
        try:
            with self.engine.begin() as conn:
                # 1. Upsert the session. first_seen/last_seen use server-side NOW()
                #    so timestamps are always full-precision (date + time).
                conn.execute(sqlalchemy.text(
                    "INSERT INTO telemetry.sessions (session_id, environment, app_version) "
                    "VALUES (:sid, :env, :ver) "
                    "ON CONFLICT (session_id) DO UPDATE SET last_seen = NOW()"),
                    {"sid": session_id, "env": environment, "ver": app_version})

                # 2. Dedup-upsert the design payload (if any). Identical MAS across
                #    several events stores ONE design row, referenced many times.
                design_id = None
                if mas_data is not None:
                    canonical = json.dumps(mas_data, sort_keys=True, separators=(',', ':'))
                    mas_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
                    row = conn.execute(sqlalchemy.text(
                        "INSERT INTO telemetry.designs (mas_hash, topology, mas_version, mas_data) "
                        "VALUES (:hash, :topo, :mver, CAST(:mas AS JSONB)) "
                        "ON CONFLICT (mas_hash) DO UPDATE SET mas_hash = EXCLUDED.mas_hash "
                        "RETURNING design_id"),
                        {"hash": mas_hash, "topo": topology, "mver": mas_version,
                         "mas": json.dumps(mas_data)}).fetchone()
                    design_id = row[0]

                # 3. Append the event.
                conn.execute(sqlalchemy.text(
                    "INSERT INTO telemetry.events "
                    "(session_id, event_type, source, stage, design_id, result_count, error_message) "
                    "VALUES (:sid, :etype, :src, :stage, :did, :rc, :err)"),
                    {"sid": session_id, "etype": event_type, "src": source, "stage": stage,
                     "did": design_id, "rc": result_count, "err": error_message})
        finally:
            self.disconnect()


class PlotCacheTable(Database):
    def connect(self):
        self.engine = sqlalchemy.create_engine("sqlite:////cache/cache.db", isolation_level="AUTOCOMMIT")

        Base = declarative_base()

        class PlotCache(Base):
            __tablename__ = 'plot_cache'
            hash = Column(String, primary_key=True)
            data = Column(String)
            created_at = Column(String)

        # Create all tables in the engine
        Base.metadata.create_all(self.engine)

        metadata = sqlalchemy.MetaData()
        metadata.reflect(self.engine, )
        Base = automap_base(metadata=metadata)
        Base.prepare()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        self.Table = Base.classes.plot_cache

    def insert_plot(self, hash, data):
        try:
            self.connect()
        except sqlalchemy.exc.OperationalError:
            return False
        data = {
            'hash': hash,
            'data': data,
            'created_at': datetime.datetime.now(),
        }
        row = self.Table(**data)
        self.session.add(row)
        self.session.flush()
        self.session.commit()
        self.disconnect()
        return True

    def read_plot(self, hash):
        try:
            self.connect()
        except sqlalchemy.exc.OperationalError:
            return None
        query = self.session.query(self.Table).filter(self.Table.hash == hash)
        try:
            data = query.one().data
        except MultipleResultsFound:
            data = None
        except NoResultFound:
            data = None
        self.disconnect()
        return data
