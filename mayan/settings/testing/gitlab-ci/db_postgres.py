from .base import *  # NOQA

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mayan_edms',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'postgres',
    }
}
