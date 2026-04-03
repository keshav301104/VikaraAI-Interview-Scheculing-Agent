import json
from datetime import datetime, timedelta

# ==========================================
# 1. MOCK DATABASE (Your source of truth)
# ==========================================
# In a real app, this would be PostgreSQL, MongoDB, or Google Calendar API.
db = {
    "appointments": {
        "appt_123": {"user": "Keshav", "time": "2026-04-10T10:00:00"}
    },
    "booked_slots": [
        "2026-04-10T10:00:00",
        "2026-04-10T14:00:00", 
        "2026-04-10T15:00:00"
    ]
}

# ==========================================
# 2. BACKEND LOGIC (The functions your server runs)
# ==========================================

def is_slot_free(requested_time: str) -> bool:
    """Helper: Checks if the time is available."""
    return requested_time not in db["booked_slots"]

def get_slots_around(requested_time: str) -> list:
    """Helper: Finds the next 3 available slots around a taken time."""
    req_dt = datetime.fromisoformat(requested_time)
    alternatives = []
    
    for offset in [-1, 1, 2, 3, 4]:
        alt_time = req_dt + timedelta(hours=offset)
        alt_time_str = alt_time.isoformat()
        if is_slot_free(alt_time_str):
            alternatives.append(alt_time_str)
            if len(alternatives) >= 3:
                break
    return alternatives

# --- Core Tools for the LLM ---

def book_appointment(user_name: str, requested_time: str) -> str:
    """Books a new appointment if the slot is free."""
    if is_slot_free(requested_time):
        appt_id = f"appt_{len(db['appointments']) + 100}"
        db["appointments"][appt_id] = {"user": user_name, "time": requested_time}
        db["booked_slots"].append(requested_time)
        return json.dumps({"status": "success", "appointment_id": appt_id, "time": requested_time})
    else:
        alternatives = get_slots_around(requested_time)
        return json.dumps({"status": "unavailable", "alternative_slots": alternatives})

def reschedule_appointment(appointment_id: str, new_time: str) -> str:
    """Moves an appointment to a new time, offering alternatives if taken."""
    if appointment_id not in db["appointments"]:
        return json.dumps({"status": "error", "message": "Appointment ID not found."})

    if is_slot_free(new_time):
        old_time = db["appointments"][appointment_id]["time"]
        db["booked_slots"].remove(old_time) # Free up the old slot
        
        db["appointments"][appointment_id]["time"] = new_time
        db["booked_slots"].append(new_time) # Block the new slot
        return json.dumps({"status": "success", "message": f"Rescheduled to {new_time}."})
    else:
        alternatives = get_slots_around(new_time)
        return json.dumps({"status": "unavailable", "alternative_slots": alternatives})

def cancel_appointment(appointment_id: str) -> str:
    """Cancels an appointment and frees up the calendar slot."""
    if appointment_id in db["appointments"]:
        time_to_free = db["appointments"][appointment_id]["time"]
        db["booked_slots"].remove(time_to_free)
        del db["appointments"][appointment_id]
        return json.dumps({"status": "success", "message": "Appointment cancelled."})
    return json.dumps({"status": "error", "message": "Appointment not found."})

# ==========================================
# 3. LLM TOOL SCHEMAS (What you send to OpenAI/Gemini)
# ==========================================
calendar_tools = [
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Books a new appointment. If unavailable, it returns alternative slots to offer the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_name": {"type": "string"},
                    "requested_time": {"type": "string", "description": "ISO 8601 format"}
                },
                "required": ["user_name", "requested_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Changes the time of an existing appointment. Returns alternatives if the new time is taken.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string"},
                    "new_time": {"type": "string", "description": "ISO 8601 format"}
                },
                "required": ["appointment_id", "new_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancels an existing appointment by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string"}
                },
                "required": ["appointment_id"]
            }
        }
    }
]

# ==========================================
# 4. AGENT SYSTEM PROMPT
# ==========================================
SYSTEM_PROMPT = """
You are an intelligent scheduling agent. Your job is to manage the user's calendar.
- When booking or rescheduling, ALWAYS call the appropriate tool.
- If the tool returns 'success', confirm the action with the user naturally.
- If the tool returns 'unavailable', DO NOT confirm the booking. Instead, read the `alternative_slots` from the tool's response and politely offer them to the user.
- Never make up times or assume a booking went through without checking the tool output.
"""