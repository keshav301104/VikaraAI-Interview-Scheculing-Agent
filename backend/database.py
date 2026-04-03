import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Connect to the URI from your .env
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# This creates a database named 'VikaraDB' and a collection named 'interviews'
db = client["VikaraDB"]
interviews_collection = db["interviews"]

def save_interview_log(call_id, transcript, start_time, extracted_info):
    """
    Saves the raw transcript AND the structured AI data to MongoDB.
    """
    log_entry = {
        "call_id": call_id,
        "timestamp": datetime.datetime.utcnow(),
        "start_time": start_time,
        "extracted_info": extracted_info,
        "raw_transcript": transcript,
        "status": "completed"
    }
    
    try:
        result = interviews_collection.insert_one(log_entry)
        print(f"✅ DATA SAVED: Interview log for {call_id} stored in MongoDB (ID: {result.inserted_id})")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")