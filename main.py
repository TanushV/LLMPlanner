import sys
import ollama
import datetime
import re
from ics import Calendar, Event
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def generate_weekly_plan(tasks):
    prompt = f"Create a weekly plan for the following tasks:\n{tasks}\n\nFormat each event as: 'Day: Task - Start time - End time'"
    response = ollama.chat(model='llama2:3b', messages=[{'role': 'user', 'content': prompt}])
    return response['message']['content']

def parse_events(plan):
    events = []
    pattern = r'(\w+):\s*(.*?)\s*-\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})'
    matches = re.findall(pattern, plan)
    
    for day, task, start_time, end_time in matches:
        events.append({
            'day': day,
            'summary': task,
            'start_time': start_time,
            'end_time': end_time
        })
    
    return events

def create_ics_file(events):
    cal = Calendar()
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    
    for event in events:
        day_offset = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(event['day'].lower())
        event_date = start_of_week + datetime.timedelta(days=day_offset)
        
        start_datetime = datetime.datetime.combine(event_date, datetime.datetime.strptime(event['start_time'], '%H:%M').time())
        end_datetime = datetime.datetime.combine(event_date, datetime.datetime.strptime(event['end_time'], '%H:%M').time())
        
        e = Event()
        e.name = event['summary']
        e.begin = start_datetime
        e.end = end_datetime
        cal.events.add(e)
    
    with open('weekly_plan.ics', 'w') as f:
        f.write(str(cal))
    
    return 'weekly_plan.ics'

def send_email(file_path):
    sender_email = "sender@example.com"
    receiver_email = "receiver@example.com"
    password = "your_app_password_here"  # Use an app password, not your regular password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Weekly Plan ICS File"

    body = "Please find attached the weekly plan ICS file."
    message.attach(MIMEText(body, "plain"))

    with open(file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {file_path}",
    )
    message.attach(part)
    text = message.as_string()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)

def main():
    print("Enter your tasks (one per line). Press Enter twice when you're done:")
    tasks = []
    while True:
        task = input()
        if task == "":
            break
        tasks.append(task)
    
    tasks_string = "\n".join(tasks)
    
    weekly_plan = generate_weekly_plan(tasks_string)
    print("\nGenerated Weekly Plan:")
    print(weekly_plan)
    
    events = parse_events(weekly_plan)
    
    ics_file = create_ics_file(events)
    
    send_email(ics_file)
    
    print("\nICS file created and sent via email successfully!")

if __name__ == '__main__':
    main()
