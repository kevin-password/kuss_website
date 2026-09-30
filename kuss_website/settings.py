"""
Django settings for kuss_website project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Reads from Render environment variables, falls back to a local dev key
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-local-dev-key-change-me-12345'
)

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False for safety. Set DEBUG=True in your local environment if needed.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Allowed Hosts
ALLOWED_HOSTS = [
    '.pythonanywhere.com',
    '.onrender.com',
    'localhost',
    '127.0.0.1',
    'kabsurgicalsociety.com',
    'www.kabsurgicalsociety.com'
]

# Render provides this environment variable automatically
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://kabsurgicalsociety.com',
    'https://www.kabsurgicalsociety.com'
]

# ============================================================
# APPLICATION DEFINITION
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Cloudinary
    'cloudinary',
    'cloudinary_storage',

    # KUSS application
    'core',
]

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

ROOT_URLCONF = 'kuss_website.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'kuss_website.wsgi.application'


# ============================================================
# DATABASE
# ============================================================
# Neon PostgreSQL on Render
# This section is intentionally unchanged.

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=True
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

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# ============================================================
# FILE STORAGE
# ============================================================
#
# Static files remain on WhiteNoise.
#
# User-uploaded media files now go to Cloudinary instead
# of Render's temporary local filesystem.
#

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },

    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}


# ============================================================
# MEDIA FILES
# ============================================================
#
# Kept for compatibility with Django and local development.
# Production uploads are handled by Cloudinary through STORAGES.
#

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# EMAIL CONFIGURATION
# ============================================================
#
# DO NOT CHANGE THIS SECTION.
# Your existing email system remains exactly as it was.
#

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

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

DEFAULT_FROM_EMAIL = 'KUSS <tumusiimekevin3@gmail.com>'
