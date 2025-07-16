from .base import *  # noqa
from dotenv import load_dotenv
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
STRIPE_ENDPONT_SECRET = os.getenv('STRIPE_ENDPONT_SECRET')

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


LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': '/var/www/webapps/bradrice/log/django_app.log', # Specify the path to your log file
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            # You can also define custom loggers for your applications
            'bradrice': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': False, # Set to False to prevent propagation to parent loggers
            },
        },
    }
