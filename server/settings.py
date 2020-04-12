import os

from dotenv import load_dotenv
load_dotenv()

MODEL_DEF_PATH = os.getenv("MODEL_DEF_PATH")
PRETRAINED_MODEL_PATH = os.getenv("PRETRAINED_MODEL_PATH")

# format: redis://username:password@hostname:port/db_number
BROKER_URL = os.getenv("BROKER_URL") or "redis://localhost:26379/0"
