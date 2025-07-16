import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env

from .base import *

if os.getenv('DJANGO_ENV') == 'development':
    from .prod import *
else:
    from .dev import *
