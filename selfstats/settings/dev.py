from .base import *
from dotenv import load_dotenv
import os

load_dotenv()

print(f"found : {os.getenv('SECRET_KEY')}")
print(f"found : {os.getenv('DEBUG')}")
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG')
ALLOWED_HOSTS = ['*',
                 'archlinux.tail71809f.ts.net'
                 ]
CSRF_TRUSTED_ORIGINS = [
    'https://archlinux.tail71809f.ts.net', 'https://nondiscursive-voguishly-tomoko.ngrok-free.dev'
]
print(f"{ALLOWED_HOSTS=}")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
