from .common import *
import os
import dj_database_url

DEBUG = False

ALLOWED_HOSTS = [
    'cocker-test.herokuapp.com'
]

SECRET_KEY = os.environ['SECRET_KEY']

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}


# DATABASES['default']['TEST'] = {
#     'NAME': DATABASES['default']['NAME']
# }
