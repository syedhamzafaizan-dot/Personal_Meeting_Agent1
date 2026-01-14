"""
Stage 6: Email Trigger Simulation Engine
Simulates email triggering without actually sending emails
"""
from datetime import datetime
from typing import List
from models import MeetingState, EmailTrigger, FollowUpMessage
import json


def simulate_email_trigger(message: FollowUpMessage) -> EmailTrigger:
    """
    Simulate triggering an email
    In a real system, this would integrate with an email service
    """
    return EmailTrigger(
        to=message.to_email,
        to_name=message.to_name,
        subject=message.subject,
        body=message.body,
        triggered_at=datetime.now(),
        status="simulated"
    )


def simulate_email_triggers(state: MeetingState) -> MeetingState:
    """
    Simulate email triggers for all follow-up messages
    """
    if not state.follow_up_messages:
        state.processing_notes.append("Stage 6: No messages to trigger")
        state.stage_completed = "email_simulation"
        return state
    
    triggers = []
    for message in state.follow_up_messages:
        trigger = simulate_email_trigger(message)
        triggers.append(trigger)
        
        # Log the trigger event
        print(f"[EMAIL SIMULATED] To: {trigger.to_name} <{trigger.to}>")
        print(f"[EMAIL SIMULATED] Subject: {trigger.subject}")
        print(f"[EMAIL SIMULATED] Triggered at: {trigger.triggered_at}")
        print("-" * 60)
    
    state.email_triggers = triggers
    state.stage_completed = "email_simulation"
    state.processing_notes.append(
        f"Stage 6: Simulated {len(triggers)} email triggers"
    )
    
    return state


def export_email_logs(state: MeetingState, output_path: str) -> str:
    """
    Export email trigger logs to a JSON file
    """
    logs = []
    
    for trigger in state.email_triggers:
        logs.append({
            "to": trigger.to,
            "to_name": trigger.to_name,
            "subject": trigger.subject,
            "body": trigger.body,
            "triggered_at": trigger.triggered_at.isoformat(),
            "status": trigger.status
        })
    
    log_file = f"{output_path}/email_triggers.json"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    
    return log_file
