import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. IMPORT LIVE TOOLS INSTEAD OF MOCK LOGIC
from calendar_tools import check_availability, book_meeting, reschedule_meeting, cancel_meeting
from rag_tools import query_knowledge_base

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY") 
)
MODEL_NAME = "llama-3.1-8b-instant"

# 2. UPDATED SCHEMAS FOR LIVE GOOGLE CALENDAR
agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Checks the Google Calendar for free and busy slots on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {"type": "string", "description": "The date to check in YYYY-MM-DD format."}
                },
                "required": ["date_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_meeting",
            "description": "Books a new interview on the Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Candidate's full name."},
                    "role": {"type": "string", "description": "The role they are applying for."},
                    "email": {"type": "string", "description": "Candidate's email address to send the Google Meet invite."},
                    "start_time": {"type": "string", "description": "ISO 8601 format (e.g. 2026-04-10T10:00:00Z)"},
                    "end_time": {"type": "string", "description": "ISO 8601 format (e.g. 2026-04-10T11:00:00Z)"}
                },
                "required": ["name", "role", "email", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_meeting",
            "description": "Moves an existing meeting to a new time slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Candidate's name to find their existing meeting."},
                    "new_start_time": {"type": "string", "description": "ISO 8601 format"},
                    "new_end_time": {"type": "string", "description": "ISO 8601 format"}
                },
                "required": ["name", "new_start_time", "new_end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_meeting",
            "description": "Cancels an existing meeting for a candidate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Candidate's name to find and cancel their meeting."}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge_base",
            "description": "Answers company-related questions (tech stack, roles, process).",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"]
            }
        }
    }
]

# Map names to actual imported live functions
available_functions = {
    "check_availability": check_availability,
    "book_meeting": book_meeting,
    "reschedule_meeting": reschedule_meeting,
    "cancel_meeting": cancel_meeting,
    "query_knowledge_base": query_knowledge_base
}

# 3. UPDATED SYSTEM PROMPT
SYSTEM_PROMPT = """
You are the Vikara AI Voice Assistant. Today is April 3, 2026.
You are conducting a phone call. Your speaking style must be conversational, concise, and natural.

You must strictly follow a TWO-PHASE conversation structure. Do NOT mix these phases.

PHASE 1: SCHEDULING & ADMIN
- Greet the user and confirm their name and the role they are applying for.
- IMPORTANT CALENDAR RULE: Always use the `check_availability` tool FIRST to see if the requested date is free.
- If the time is free, you MUST explicitly ask the user for their email address: "What email address should I send the calendar invite and Google Meet link to?"
- Once they provide a valid-sounding email address, use the `book_meeting` tool (assume meetings are 1 hour long) and include their email.
- After the tool returns success, confirm to the user: "I have successfully booked the interview and sent the Google Calendar invite with the Meet link to your email."
- If they want to change times, use `reschedule_meeting`. If they want to cancel, use `cancel_meeting`.
- NEVER ask any interview questions during this phase.

TRANSITION:
- Once the calendar is completely settled and booked, you MUST ask explicitly: "Are you ready to begin the interview questionnaire?"
- You must WAIT for the user to say "yes" before moving to Phase 2.

PHASE 2: THE INTERVIEW
- Only begin this phase after the user has explicitly agreed to start.
- Ask ONE interview question at a time. Wait for the user's answer before asking the next one.
- Keep the flow natural, acknowledge their answers briefly, and move to the next question.
"""

class ChatSession:
    def __init__(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def send_message(self, user_text):
        self.messages.append({"role": "user", "content": user_text})
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=self.messages,
            tools=agent_tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        self.messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"[Log] Executing Live Tool: {fn_name}({fn_args})")
                
                try:
                    result = available_functions[fn_name](**fn_args)
                except Exception as e:
                    result = f"Error executing tool: {str(e)}"
                
                self.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": str(result),
                })

            second_res = client.chat.completions.create(model=MODEL_NAME, messages=self.messages)
            final_text = second_res.choices[0].message.content
            self.messages.append({"role": "assistant", "content": final_text})
            return type('Response', (object,), {'text': final_text})

        return type('Response', (object,), {'text': response_message.content})

# THIS IS THE CRITICAL FUNCTION FOR ISOLATED MEMORY
def create_chat_session():
    return ChatSession()

def extract_call_summary(transcript_list):
    text = "\n".join(transcript_list)
    res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": f"Extract JSON summary: {text}. Include 'role', 'name', 'status'."}],
        response_format={"type": "json_object"}
    )
    return json.loads(res.choices[0].message.content)

def chat_with_agent():
    session = create_chat_session()
    print("\n--- Live Calendar Terminal Mode ---")
    while True:
        inp = input("\nYou: ")
        if inp.lower() == 'exit': break
        print(f"AI: {session.send_message(inp).text}")

if __name__ == "__main__":
    chat_with_agent()