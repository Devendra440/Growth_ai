
import os
import pymongo
from dotenv import load_dotenv
import sys

# Force load from current directory to be sure
load_dotenv(".env")

uri = os.getenv("MONGO_URI")
print(f"Loaded URI: {uri}")

if not uri:
    print("Error: MONGO_URI is empty or not found.")
    sys.exit(1)

try:
    print("Attempting to connect...")
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("SUCCESS: Connected to MongoDB!")
except Exception as e:
    print(f"FAILURE: Could not connect to MongoDB.")
    print(f"Error details: {e}")
