import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
OWNER_IDS = [int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x]  # Your ID(s)