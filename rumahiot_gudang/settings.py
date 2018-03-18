"""
Django settings for rumahiot_gudang project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# We dont need this thing
#SECRET_KEY = '0g(tuzd(e*hod$l!*35#(nwux!jyx*#bxsx_reg77vcmo-7iqq'
SECRET_KEY = ' '
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rumahiot_gudang.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rumahiot_gudang.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    # 'default': {
    #     'ENGINE': 'django_mongodb_engine',
    #     'NAME': 'my_database'
    # }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
# todo : check for time in aws

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

# CORS Header
# TODO : Limit from one domain only

CORS_ORIGIN_ALLOW_ALL = True

# TODO : Change mongo port, add auth, and add allowed ip range

RUMAHIOT_GUDANG_MONGO_USERNAME = os.environ.get('GUDANG_MONGO_USERNAME','')
RUMAHIOT_GUDANG_MONGO_PASSWORD = os.environ.get('GUDANG_MONGO_PASSWORD','')
RUMAHIOT_GUDANG_MONGO_HOST = os.environ.get('GUDANG_MONGO_HOST','')
RUMAHIOT_GUDANG_MONGO_PORT = os.environ.get('GUDANG_MONGO_PORT','')
RUMAHIOT_GUDANG_DATABASE = os.environ.get('GUDANG_DATABASE','')
RUMAHIOT_GUDANG_USERS_DEVICE_COLLECTION = os.environ.get('GUDANG_USERS_DEVICE_COLLECTION','')
RUMAHIOT_GUDANG_DEVICE_DATA_COLLECTION = os.environ.get('GUDANG_DEVICE_DATA_COLLECTION','')
RUMAHIOT_GUDANG_SENSOR_DETAIL_COLLECTION = os.environ.get('GUDANG_SENSOR_DETAIL_COLLECTION','')
RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION = os.environ.get('RUMAHIOT_GUDANG_USER_SENSORS_COLLECTION','')
RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION = os.environ.get('RUMAHIOT_GUDANG_MASTER_SENSORS_COLLECTION','')
SIDIK_TOKEN_VALIDATION_ENDPOINT = os.environ.get('SIDIK_TOKEN_VALIDATION_ENDPOINT','')