"""
Stage 5: Follow-up Message Generator
Generates personalized follow-up messages for action item owners
"""
import json
from typing import Dict, List
from models import MeetingState, FollowUpMessage, ActionItem
import config
from utils import call_openai_with_retry, clean_json_response


def group_actions_by_owner(state: MeetingState) -> Dict[str, List[ActionItem]]:
    """Group action items by owner email"""
    groups = {}
    
    for action in state.action_items:
        if action.owner_email:
            if action.owner_email not in groups:
                groups[action.owner_email] = []
            groups[action.owner_email].append(action)
    
    return groups


def generate_follow_up_message(
    owner_name: str,
    owner_email: str,
    actions: List[ActionItem],
    state: MeetingState
) -> FollowUpMessage:
    """Generate a personalized follow-up message for an owner"""
    
    # Prepare action list
    action_list = []
    for action in actions:
        action_info = {
            "description": action.description,
            "deadline": str(action.deadline_date) if action.deadline_date else "No deadline specified",
            "evidence": action.evidence[:2] if action.evidence else []  # Limit evidence
        }
        action_list.append(action_info)
    
    prompt = f"""Generate a professional, personalized follow-up email for {owner_name}.

Their assigned action items from the meeting:
{json.dumps(action_list, indent=2)}

The email should:
1. Be friendly but professional
2. Clearly list each action item with its deadline
3. Be concise (under 200 words)
4. Include a clear subject line
5. Encourage them to reach out if they have questions

Respond ONLY with valid JSON:
{{
  "subject": "Follow-up: Your Action Items from [Meeting]",
  "body": "Email body text with proper formatting"
}}"""

    try:
        result_text = call_openai_with_retry(
            prompt=prompt,
            system_message="You are a professional meeting coordinator. Generate clear, actionable follow-up emails. Output only valid JSON.",
            temperature=0.3,
            max_tokens=1000
        )
        
        # Clean markdown
        result_text = clean_json_response(result_text)
        
        result = json.loads(result_text)
        
        return FollowUpMessage(
            to_email=owner_email,
            to_name=owner_name,
            subject=result.get("subject", "Follow-up: Your Action Items"),
            body=result.get("body", ""),
            action_items=[action.id for action in actions]
        )
        
    except Exception as e:
        # Fallback: create basic message
        action_descriptions = "\n".join([
            f"- {action.description} (Due: {action.deadline_date or 'TBD'})"
            for action in actions
        ])
        
        return FollowUpMessage(
            to_email=owner_email,
            to_name=owner_name,
            subject="Follow-up: Your Action Items",
            body=f"""Hi {owner_name},

Following up on the meeting, here are your assigned action items:

{action_descriptions}

Please let me know if you have any questions.

Best regards""",
            action_items=[action.id for action in actions]
        )
def generate_messages(state: MeetingState) -> MeetingState:
    """
    Generate follow-up messages for all action item owners
    """
    # Group actions by owner
    owner_groups = group_actions_by_owner(state)
    
    if not owner_groups:
        state.processing_notes.append("Stage 5: No owners to send messages to")
        state.stage_completed = "message_generation"
        return state
    
    # Generate message for each owner
    messages = []
    for owner_email, actions in owner_groups.items():
        # Get owner name from first action
        owner_name = actions[0].owner_name or "Team Member"
        
        message = generate_follow_up_message(
            owner_name=owner_name,
            owner_email=owner_email,
            actions=actions,
            state=state
        )
        
        messages.append(message)
    
    state.follow_up_messages = messages
    state.stage_completed = "message_generation"
    state.processing_notes.append(
        f"Stage 5: Generated {len(messages)} follow-up messages"
    )
    
    return state
