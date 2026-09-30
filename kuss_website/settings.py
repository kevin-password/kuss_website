"""
Django settings for kuss_website project.
"""

from pathlib import Path
import os
import dj_database_url


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-local-dev-key-change-me-12345'
)

DEBUG = os.environ.get(
    'DEBUG',
    'False'
) == 'True'


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    '.onrender.com',
    'localhost',
    '127.0.0.1',
    'kabsurgicalsociety.com',
    'www.kabsurgicalsociety.com',
]


RENDER_EXTERNAL_HOSTNAME = os.environ.get(
    'RENDER_EXTERNAL_HOSTNAME'
)

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(
        RENDER_EXTERNAL_HOSTNAME
    )


# ============================================================
# CANONICAL SITE DOMAIN
# ============================================================

SITE_DOMAIN = 'https://kabsurgicalsociety.com'


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [

    'https://*.onrender.com',

    'https://kabsurgicalsociety.com',

    'https://www.kabsurgicalsociety.com',

]


# ============================================================
# APPLICATION DEFINITION
# ============================================================

INSTALLED_APPS = [

    # Django built-in applications

    'django.contrib.admin',

    'django.contrib.auth',

    'django.contrib.contenttypes',

    'django.contrib.sessions',

    'django.contrib.messages',

    'django.contrib.staticfiles',


    # Sitemap / SEO

    'django.contrib.sitemaps',


    # Cloudinary

    'cloudinary',

    'cloudinary_storage',


    # KUSS application

    'core',

]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]


# ============================================================
# ROOT URL CONFIGURATION
# ============================================================

ROOT_URLCONF = 'kuss_website.urls'


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [

    {

        'BACKEND':
            'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

        'APP_DIRS': True,

        'OPTIONS': {

            'context_processors': [

                'django.template.context_processors.debug',

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',

                'core.context_processors.leadership_context',

            ],

        },

    },

]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = 'kuss_website.wsgi.application'


# ============================================================
# DATABASE — NEON POSTGRESQL ONLY
# ============================================================
#
# KUSS production data must live in Neon PostgreSQL.
#
# There is intentionally NO SQLite fallback.
#
# If DATABASE_URL is missing, the application will stop
# instead of silently creating/using a local SQLite database.
# ============================================================

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise RuntimeError(
        'DATABASE_URL is missing. '
        'KUSS requires Neon PostgreSQL. '
        'Configure DATABASE_URL in the Render environment.'
    )


DATABASES = {

    'default': dj_database_url.parse(

        DATABASE_URL,

        conn_max_age=600,

        ssl_require=True,

    )

}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator'
    },

    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator'
    },

]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Kampala'

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(
    BASE_DIR,
    'staticfiles'
)


# ============================================================
# FILE STORAGE
# ============================================================
#
# DEFAULT STORAGE:
# Cloudinary
#
# STATIC FILE STORAGE:
# WhiteNoise
#
# Uploaded media is therefore NOT dependent on the Render
# filesystem.
# ============================================================

STORAGES = {

    'default': {

        'BACKEND':
            'cloudinary_storage.storage.MediaCloudinaryStorage',

    },

    'staticfiles': {

        'BACKEND':
            'whitenoise.storage.CompressedManifestStaticFilesStorage',

    },

}


# ============================================================
# MEDIA
# ============================================================
#
# User-uploaded files are handled by Cloudinary.
#
# No local MEDIA_ROOT is configured.
# ============================================================

MEDIA_URL = '/media/'


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = (
    'django.db.models.BigAutoField'
)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================
#
# Existing KUSS email system.
#
# DO NOT CHANGE.
# ============================================================

EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
)

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 587

EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.environ.get(
    'EMAIL_HOST_USER',
    'tumusiimekevin3@gmail.com'
)

EMAIL_HOST_PASSWORD = os.environ.get(
    'EMAIL_HOST_PASSWORD'
)

DEFAULT_FROM_EMAIL = (
    'KUSS <tumusiimekevin3@gmail.com>'
)
