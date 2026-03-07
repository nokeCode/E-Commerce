"""
Django settings for HStore project.
"""

from pathlib import Path
import os
import dj_database_url
from django.utils.translation import gettext_lazy as _
from decouple import config
BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================
# SECURITY
# =====================================================
SECRET_KEY = config("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False").strip().lower() in ("1", "true", "yes", "on")
ALLOWED_HOSTS = ["e-commerce-32qv.onrender.com"]


# =====================================================
# APPS
# =====================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',

    'django.contrib.sites',

    'accounts',
    'cart',
    'core',
    'orders',
    'products',
    'reviews',
    'custumAdmin',
]
SITE_ID = 1

AUTH_USER_MODEL = 'accounts.Users'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.GeoLocationMiddleware',
]

ROOT_URLCONF = 'HStore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart_context',
                'custumAdmin.context_processors.admin_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'HStore.wsgi.application'


# =====================================================
# DATABASE (RENDER)
# =====================================================
DATABASE_URL = config("DATABASE_URL")
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}


# =====================================================
# PASSWORD VALIDATORS
# =====================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =====================================================
# INTERNATIONALIZATION
# =====================================================
LANGUAGE_CODE = 'fr'
LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
]

USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'


# =====================================================
# STATIC & MEDIA
# =====================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CLOUDINARY_URL = config("CLOUDINARY_URL", default="")
if CLOUDINARY_URL:
    os.environ.setdefault("CLOUDINARY_URL", CLOUDINARY_URL)
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'


# =====================================================
# EMAIL / SENDGRID
# =====================================================
try:
    from decouple import config
except:
    def config(key, default=None, cast=None):
        val = os.environ.get(key, default)
        if cast and val is not None:
            return cast(val)
        return val

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SENDGRID_API_KEY = config("SENDGRID_API_KEY", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="webmaster@localhost")


# =====================================================
# AUTHENTIFICATION
# =====================================================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# =====================================================
# ALLAUTH (if installed)
# =====================================================
try:
    import allauth
    INSTALLED_APPS += [
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'allauth.socialaccount.providers.google',
    ]
    MIDDLEWARE.append('allauth.account.middleware.AccountMiddleware')
    AUTHENTICATION_BACKENDS += ['allauth.account.auth_backends.AuthenticationBackend']

    SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "APP": {
                "client_id": config("GOOGLE_CLIENT_ID", default=""),
                "secret": config("GOOGLE_CLIENT_SECRET", default=""),
                "key": ""
            }
        }
    }
except:
    SOCIALACCOUNT_PROVIDERS = {}


# =====================================================
# GEOIP
# =====================================================
GEOIP_PATH = BASE_DIR / 'geoip'
GEOIP_TEST_IP = "0.0.0.0"


# =====================================================
# STRIPE
# =====================================================
STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
