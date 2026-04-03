import os
import json
import asyncio
import re  
import datetime
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from retell import Retell

# IMPORT THE FACTORY FUNCTION & EXTRACTOR
from llm import create_chat_session, extract_call_summary

# IMPORT EXACT DATABASE FUNCTIONS
from database import db, save_interview_log

load_dotenv()

# Initialize FastAPI App
app = FastAPI()

# Enable CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Retell SDK
retell = Retell(api_key=os.getenv("RETELL_API_KEY"))

@app.post("/create-web-call")
async def create_web_call(request: Request):
    """
    Creates a new web call token for the frontend to connect to Retell.
    """
    try:
        body = await request.json()
        agent_id = body.get("agent_id")

        if not agent_id:
            return {"error": "agent_id is required"}, 400

        # Generate the call token using the Retell SDK
        web_call_response = retell.call.create_web_call(
            agent_id=agent_id
        )

        print(f"🌐 Web call token generated for Agent: {agent_id}")
        return {"access_token": web_call_response.access_token}

    except Exception as e:
        print(f"❌ Error creating web call: {e}")
        return {"error": str(e)}, 500


@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    """
    This is the core loop where Retell talks to our Groq Llama-3 brain.
    """
    await websocket.accept()
    print(f"\n🟢 CONNECTION ESTABLISHED: Call ID {call_id}")

    # Create a fresh, isolated brain for THIS specific phone call
    chat_session = create_chat_session()
    full_transcript = []
    start_time = datetime.datetime.utcnow()

    try:
        # BUG FIX: Send the greeting IMMEDIATELY without waiting.
        # This guarantees the AI speaks the exact second the call connects!
        # Step 2: Send the opening greeting
        greeting_text = "Hi there! I'm Vikara AI, your autonomous recruiting assistant. To get started, could you please tell me your full name and the role you are applying for?"
        print("🤖 Greeting Sent: Asking for name and role.")
        
        full_transcript.append(f"AI: {greeting_text}")
        
        await websocket.send_text(json.dumps({
            "response_id": 0,
            "content": greeting_text,
            "content_complete": True,
            "end_call": False
        }))

        # Step 3: Enter the main conversation loop
        while True:
            request = await websocket.receive_json()

            # Handle Retell Keep-Alive Pings
            if request.get("interaction_type") == "ping_pong":
                await websocket.send_text(json.dumps({
                    "interaction_type": "ping_pong",
                    "timestamp": request["timestamp"]
                }))
                continue

            # Ignore background setup packets
            if request.get("interaction_type") in ["update_only", "call_details"]:
                continue

            # Process the user's spoken words
            if request.get("interaction_type") == "response_required":
                user_text = request.get("transcript", [])[-1].get("content", "")
                print(f"👤 User: {user_text}")
                
                full_transcript.append(f"User: {user_text}")

                # Send user text to our isolated Llama-3 session
                try:
                    response = chat_session.send_message(user_text)
                    raw_ai_text = response.text
                    
                    # Scrub out any raw <function> tags so Retell doesn't speak them
                    ai_response_text = re.sub(r'<[^>]+>', '', raw_ai_text).strip()
                    
                    print(f"🤖 AI: {ai_response_text}")
                    full_transcript.append(f"AI: {ai_response_text}") 

                    # Send Llama-3's response back to Retell (Voice)
                    await websocket.send_text(json.dumps({
                        "response_id": request["response_id"],
                        "content": ai_response_text,
                        "content_complete": True,
                        "end_call": False
                    }))
                
                except Exception as e:
                    print(f"❌ Error communicating with LLM: {e}")
                    # Fallback message if Groq crashes
                    await websocket.send_text(json.dumps({
                        "response_id": request["response_id"],
                        "content": "I'm sorry, I'm having trouble thinking right now. Let me try that again.",
                        "content_complete": True,
                        "end_call": False
                    }))

    except WebSocketDisconnect:
        print(f"\n🔴 DISCONNECTED: Call {call_id} ended.")
        
        # When the call ends, extract data and save to MongoDB
        print("🧠 Summarizing call for the records...")
        try:
            extracted_info = extract_call_summary(full_transcript)
            save_interview_log(call_id, full_transcript, start_time, extracted_info)
        except Exception as e:
            print(f"❌ Error saving to MongoDB: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected WebSocket error: {e}")
        
    finally:
        print("INFO: connection closed")