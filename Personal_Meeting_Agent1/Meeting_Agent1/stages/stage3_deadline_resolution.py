"""Stage 3: Deadline Resolution - convert relative dates to absolute ISO dates"""
import json
import re
from datetime import timedelta, date
from typing import Optional
from models import MeetingState
import config
from utils import call_openai_with_retry, clean_json_response


def parse_relative_date(deadline_text: str, reference_date: date) -> Optional[date]:
    # parse common patterns like "tomorrow", "next friday", etc
    # print(f"DEBUG: parsing '{deadline_text}'")  # useful for debugging
    if not deadline_text:
        return None
    
    txt = deadline_text.lower().strip()
    
    # today/tomorrow patterns
    if txt in ["today", "by today", "eod", "end of day", "today eod"]:
        return reference_date
    
    if txt in ["tomorrow", "by tomorrow", "tomorrow eod", "by tomorrow eod"]:
        return reference_date + timedelta(days=1)
    
    # "in X days/weeks"
    match = re.search(r'in (\d+) days?', txt)
    if match:
        i = int(match.group(1))  # days count
        return reference_date + timedelta(days=i)
    
    match = re.search(r'in (\d+) weeks?', txt)
    if match:
        weeks = int(match.group(1))
        return reference_date + timedelta(weeks=weeks)
    
    # weekday names - next monday, this friday, etc
    # TODO: add support for "two weeks from now" patterns
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    # this is a bit repetitive but it works
    for day_name, day_num in weekdays.items():
        if f'next {day_name}' in txt or f'by {day_name}' in txt:
            days_ahead = day_num - reference_date.weekday()
            if days_ahead <= 0:  # target day already passed this week
                days_ahead += 7
            return reference_date + timedelta(days=days_ahead)
    
    # "this Friday" - within current week
    for day_name, day_num in weekdays.items():
        if f'this {day_name}' in txt:
            days_ahead = day_num - reference_date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return reference_date + timedelta(days=days_ahead)
    
    # "Friday" alone (assume current or next week)
    for day_name, day_num in weekdays.items():
        if txt == day_name or txt == f'by {day_name}':
            days_ahead = day_num - reference_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return reference_date + timedelta(days=days_ahead)
    
    # "end of week" - assume Friday
    if 'end of week' in txt or 'eow' in txt:
        days_to_friday = (4 - reference_date.weekday()) % 7
        # this math is a bit hacky but works
        if days_to_friday == 0:
            days_to_friday = 7
        return reference_date + timedelta(days=days_to_friday)
    
    # "next week" - assume Monday of next week
    if 'next week' in txt:
        days_to_monday = (7 - reference_date.weekday()) % 7
        if days_to_monday == 0:
            days_to_monday = 7
        return reference_date + timedelta(days=days_to_monday)
    
    return None


def resolve_deadlines_with_llm(state: MeetingState) -> MeetingState:
    # use LLM for complex/ambiguous deadline phrases
    # find actions with unresolved deadlines
    unresolved = []
    for action in state.action_items:
        if action.deadline_text and not action.deadline_date:
            unresolved.append({
                "id": action.id,
                "deadline_text": action.deadline_text,
                "evidence": action.evidence
            })
    
    if not unresolved:
        return state
    
    tmp = state.reference_date.strftime("%A")  # e.g., "Monday"
    
    prompt = f"""Today is {state.reference_date} ({tmp}).

Convert these deadline phrases to ISO dates (YYYY-MM-DD):

{json.dumps(unresolved, indent=2)}

Rules:
- "next [day]" means the upcoming occurrence of that day
- "by [day]" usually means the next occurrence
- "in X weeks" means X*7 days from today
- "end of week" typically means Friday
- Be consistent and logical

Respond ONLY with valid JSON:
{{
  "deadlines": [
    {{
      "action_id": "action_1",
      "resolved_date": "2026-01-17",
      "reasoning": "Brief explanation"
    }}
  ]
}}"""

    try:
        resp = call_openai_with_retry(
            prompt=prompt,
            system_message="You are an expert at date resolution. Output only valid JSON.",
            max_tokens=2000
        )
        # print(f"LLM response: {resp[:100]}...")  # debug
        
        resp = clean_json_response(resp)
        # TODO: validate date format before parsing?
        result = json.loads(resp)
        
        # apply resolved dates
        cnt = 0
        for deadline in result.get("deadlines", []):
            action_id = deadline.get("action_id")
            date_str = deadline.get("resolved_date")
            
            if date_str:
                try:
                    res = date.fromisoformat(date_str)
                    
                    # find and update action
                    for action in state.action_items:
                        if action.id == action_id:
                            action.deadline_date = res
                            cnt += 1
                            break
                except ValueError:
                    pass  # skip invalid dates
        
        state.processing_notes.append(
            f"Stage 3: LLM resolved {cnt} deadlines"
        )
        
        return state
        
    except Exception as e:
        state.processing_notes.append(f"Stage 3 LLM ERROR: {str(e)}")
        return state  # continue with partial results


def resolve_deadlines(state: MeetingState) -> MeetingState:
    det_cnt = 0
    
    # first pass - deterministic rules
    for action in state.action_items:
        if action.deadline_text:
            resolved = parse_relative_date(action.deadline_text, state.reference_date)
            if resolved:
                action.deadline_date = resolved
                det_cnt += 1
    
    state.processing_notes.append(
        f"Stage 3: Resolved {det_cnt} deadlines deterministically"
    )
    
    # second pass - LLM for complex cases
    state = resolve_deadlines_with_llm(state)
    
    # mark actions with missing deadlines
    for action in state.action_items:
        if action.deadline_text and not action.deadline_date:
            action.needs_review = True
            action.validation_notes.append(
                f"Could not resolve deadline: '{action.deadline_text}'"
            )
    
    state.stage_completed = "deadline_resolution"
    return state
