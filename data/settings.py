from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
THUMB = os.getenv("THUMB", 4772)
