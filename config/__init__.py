import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
APP_ID = os.getenv("APP_ID")
APP_PRIVATE_KEY = os.getenv("APP_PRIVATE_KEY", "").encode().decode("unicode_escape").strip()

lines = [line.strip() for line in APP_PRIVATE_KEY.strip().split('\\n') if line.strip()]
APP_PRIVATE_KEY = '\n'.join(lines)