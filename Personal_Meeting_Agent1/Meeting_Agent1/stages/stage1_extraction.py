"""Stage 1: Extract action items, decisions and risks from transcript"""
from loguru import logger
from models import ActionItem, Decision, Risk, MeetingState
from utils import call_openai_with_retry, parse_json_safely


def extract_intelligence(state: MeetingState) -> MeetingState:
    """Extract action items, decisions and risks from transcript"""
    logger.info("Reading transcript...")
    
    # build prompt for extraction
    prompt = create_extraction_prompt(state.transcript)
    
    # call LLM
    logger.info("Extracting actions, decisions, and risks...")
    resp = call_openai_with_retry(
        prompt=prompt,
        system_message="You are an expert meeting analyst. Extract information accurately and provide evidence."
    )
    
    # parse response
    result = parse_json_safely(resp, fallback={
        "action_items": [],
        "decisions": [],
        "risks": []
    })
    
    # convert to structured models
    state.action_items = convert_to_action_items(result.get("action_items", []))
    state.decisions = convert_to_decisions(result.get("decisions", []))
    state.risks = convert_to_risks(result.get("risks", []))
    
    # log results
    logger.success(
        f"Found {len(state.action_items)} actions, "
        f"{len(state.decisions)} decisions, "
        f"{len(state.risks)} risks"
    )
    
    state.stage_completed = "extraction"
    state.processing_notes.append(
        f"Stage 1: Extracted {len(state.action_items)} actions, "
        f"{len(state.decisions)} decisions, {len(state.risks)} risks"
    )
    
    return state


def create_extraction_prompt(transcript: str) -> str:
    # TODO: could probably optimize this prompt further
    return f"""You are analyzing a meeting transcript. Your job is to find:

1. **ACTION ITEMS** - Tasks someone needs to complete
2. **DECISIONS** - Important choices that were made  
3. **RISKS & QUESTIONS** - Concerns or unresolved issues

For each item, provide:
- A clear description
- The owner's name (if mentioned)
- Deadline (the exact phrase used, like "by Friday" or "next week")
- Evidence (direct quotes with timestamps that prove this came from the meeting)

Here's the meeting:
{transcript}

Respond with ONLY valid JSON in this format:
{{
  "action_items": [
    {{
      "description": "Clear description of the task",
      "owner_name": "Person Name or null",
      "deadline_text": "deadline phrase or null",
      "evidence": ["[HH:MM] Speaker: exact quote"]
    }}
  ],
  "decisions": [
    {{
      "description": "What was decided",
      "made_by": "Person Name or null",
      "evidence": ["[HH:MM] Speaker: exact quote"],
      "timestamp": "[HH:MM]"
    }}
  ],
  "risks": [
    {{
      "description": "The risk or question",
      "category": "risk or open_question",
      "mentioned_by": "Person Name or null",
      "evidence": ["[HH:MM] Speaker: exact quote"],
      "timestamp": "[HH:MM]"
    }}
  ]
}}"""


def convert_to_action_items(raw_items: list) -> list[ActionItem]:
    # convert raw json to ActionItem objects
    action_items = []
    
    for idx, item in enumerate(raw_items):
        try:
            action_items.append(ActionItem(
                id=f"action_{idx+1}",
                description=item["description"],
                owner_name=item.get("owner_name"),
                deadline_text=item.get("deadline_text"),
                evidence=item.get("evidence", [])
            ))
        except Exception as e:
            logger.warning(f"Skipped malformed action item: {e}")
            # skip bad items
            continue
    
    return action_items


def convert_to_decisions(raw_items: list) -> list[Decision]:
    decisions = []
    
    for idx, item in enumerate(raw_items):
        try:
            decisions.append(Decision(
                id=f"decision_{idx+1}",
                description=item["description"],
                made_by=item.get("made_by"),
                evidence=item.get("evidence", []),
                timestamp=item.get("timestamp")
            ))
        except Exception as e:
            logger.warning(f"Skipped malformed decision: {e}")
            continue  # just skip if parse fails
    
    return decisions


def convert_to_risks(raw_items: list) -> list[Risk]:
    risks = []
    
    for idx, item in enumerate(raw_items):
        try:
            risks.append(Risk(
                id=f"risk_{idx+1}",
                description=item["description"],
                category=item.get("category", "risk"),
                mentioned_by=item.get("mentioned_by"),
                evidence=item.get("evidence", []),
                timestamp=item.get("timestamp")
            ))
        except Exception as e:
            logger.warning(f"Skipped malformed risk: {e}")
            continue
    
    return risks
