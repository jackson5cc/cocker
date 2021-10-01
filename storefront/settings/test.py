from .common import *
import dj_database_url

DEBUG = True

ALLOWED_HOSTS = ['*']

SECRET_KEY = 'django-insecure-hs6j037urx6iav+7#10%-vu4l4f5@@-1_zo)oft4g7$vf2$jmp'

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}


# DATABASES['default']['TEST'] = {
#     'NAME': DATABASES['default']['NAME']
# }
