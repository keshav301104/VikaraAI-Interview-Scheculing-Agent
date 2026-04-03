import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

CALENDAR_ID = "2a163eddd00d5dfcb3ee9be4b844d3b9420d035f774bc5984e58f9d3203ceccb@group.calendar.google.com"
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def check_availability(date_str: str) -> str:
    service = get_calendar_service()
    start_of_day = f"{date_str}T00:00:00Z"
    end_of_day = f"{date_str}T23:59:59Z"

    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return f"The calendar is completely free on {date_str}."
        
        busy_times = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            busy_times.append(f"Busy from {start} to {end}")
        
        return f"On {date_str}, the following slots are booked:\n" + "\n".join(busy_times) + "\nAll other times are free to book."
        
    except Exception as e:
        return f"Error checking calendar: {str(e)}"

def book_meeting(name: str, role: str, start_time: str, end_time: str, email: str) -> str:
    service = get_calendar_service()
    
    event_body = {
        'summary': f'Interview: {role} - {name}',
        'description': 'Interview scheduled automatically via the Vikara AI Voice Agent. A Google Meet link has been generated for this session.',
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Kolkata',
        },
        # THIS IS NEW: Adds the candidate to the event
        'attendees': [
            {'email': email}
        ],
        # THIS IS NEW: Generates the Google Meet Link
        'conferenceData': {
            'createRequest': {
                'requestId': f"vikara-{name.replace(' ', '')}-{start_time.replace(':', '')}",
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        }
    }

    try:
        # sendUpdates='all' is the magic word that triggers the email to the candidate
        created_event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates='all'
        ).execute()
        
        # Grab the generated Meet link to pass back to the AI
        meet_link = created_event.get('hangoutLink', created_event.get('htmlLink'))
        
        return f"Successfully booked! The calendar invite and Meet link have been emailed to {email}."
        
    except Exception as e:
        return f"Failed to book the meeting: {str(e)}"

def cancel_meeting(name: str) -> str:
    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID, 
            q=name,
            timeMin=now, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return f"I could not find any upcoming meetings on the calendar for someone named {name}."

        event_id = events[0]['id']
        
        # Adding sendUpdates='all' emails the candidate that it was canceled
        service.events().delete(
            calendarId=CALENDAR_ID, 
            eventId=event_id,
            sendUpdates='all'
        ).execute()
        
        return f"Successfully canceled the upcoming meeting for {name} and notified the candidate."
        
    except Exception as e:
        return f"Error canceling the meeting: {str(e)}"

def reschedule_meeting(name: str, new_start_time: str, new_end_time: str) -> str:
    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID, 
            q=name, 
            timeMin=now, 
            singleEvents=True
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return f"I could not find any existing meetings for {name} to reschedule."

        event = events[0]
        event_id = event['id']

        event['start']['dateTime'] = new_start_time
        event['end']['dateTime'] = new_end_time

        # Adding sendUpdates='all' emails the candidate about the time change
        updated_event = service.events().update(
            calendarId=CALENDAR_ID, 
            eventId=event_id, 
            body=event,
            sendUpdates='all'
        ).execute()

        return f"Successfully rescheduled the meeting for {name}. The calendar is updated and the candidate has been notified."
        
    except Exception as e:
        return f"Error rescheduling the meeting: {str(e)}"