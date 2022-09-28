import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    LOCAL_DB_PATH = '/etc/openmagnetics/'
    LOCAL_DB_FILENAME = 'local.db'
