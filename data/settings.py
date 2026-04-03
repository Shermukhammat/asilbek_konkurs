from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
THUMB = os.getenv("THUMB", 4772)
DATA_CHANNEL = os.getenv("DATA_CHANNEL", -1002359587138)
