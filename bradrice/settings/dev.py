from .base import *  # noqa
from dotenv import load_dotenv
import logging
import os

# Determine the environment (e.g., 'development', 'production')
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')  # Default to development
load_dotenv(dotenv_path=f'.env.{DJANGO_ENV}')
# ENV = os.getenv('DJANGO_ENV', 'development')
#
# if DJANGO_ENV == "development":
#            load_dotenv(".env.development")
#        else:
#            load_dotenv(".env") # Load default .env for other environments (e.g., production)


STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [  # noqa
    "django_sass",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

WAGTAIL_CACHE = False

try:
    from .local import *  # noqa
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'success_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/www/webapps/dev.bradrice/log/django_success.log',
            # 'maxBytes': 1024 * 1024 * 5,  # 5 MB
            # 'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/www/webapps/dev.bradrice/log/django_error.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'django': {  # Custom logger for success messages
            'handlers': ['success_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.error': {  # Custom logger for error messages
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {  # Custom logger for success messages
            'handlers': ['success_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}



# LOGGING = {
#         'version': 1,
#         'disable_existing_loggers': False,
#         'formatters': {
#             'verbose': {
#                 'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
#             },
#         },
#         'handlers': {
#             'file': {
#                 'level': 'DEBUG',
#                 'class': 'logging.FileHandler',
#                 'formatter': 'verbose',
#                 'filename': '/var/www/webapps/dev.bradrice/log/django_app.log', # Specify the path to your log file
#             },
#         },
#         'loggers': {
#             'django': {
#                 'handlers': ['file'],
#                 'level': 'DEBUG',
#                 'propagate': True,
#             },
#             # You can also define custom loggers for your applications
#             'bradrice': {
#                 'handlers': ['file'],
#                 'level': 'INFO',
#                 'propagate': False, # Set to False to prevent propagation to parent loggers
#             },
#         },
#     }
