from .common import *
import os
import dj_database_url

DEBUG = True

ALLOWED_HOSTS = [
    'enigmatic-everglades-98656.herokuapp.com'
]

SECRET_KEY = os.environ['SECRET_KEY']

DATABASES = {
    'default':dj_database_url.config(conn_max_age=600)
}
