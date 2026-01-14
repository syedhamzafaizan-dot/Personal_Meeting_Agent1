"""Stage 2: Owner Resolution - matches owners to people directory"""
import json
from typing import Dict, Optional
from models import MeetingState, Person
import config
from utils import call_openai_with_retry, clean_json_response


def normalize_name(name: str) -> str:
    if not name:
        return ""
    return name.lower().strip()


def find_exact_match(owner_name: str, people_dir: Dict[str, Person]) -> Optional[Person]:
    if not owner_name:
        return None
    
    norm = normalize_name(owner_name)
    
    for person_name, person in people_dir.items():
        if normalize_name(person_name) == norm:
            return person
        
        # also check just first name
        first_name = person_name.split()[0].lower()
        if norm == first_name:
            return person
    
    return None


def resolve_owners_with_llm(state: MeetingState) -> MeetingState:
    """Use LLM to resolve ambiguous names and infer from roles"""
    # build people directory string for prompt
    people_list = []
    for name, person in state.people_directory.items():
        people_list.append(f"- {name} ({person.role}) - {person.email}")
    
    people_str = "\n".join(people_list)
    # print(f"DEBUG: {len(people_list)} people in directory")  # useful for debugging
    
    # get actions that still need resolution
    unresolved = []
    for action in state.action_items:
        if action.owner_name and not action.owner_email:
            unresolved.append({
                "id": action.id,
                "description": action.description,
                "owner_name": action.owner_name,
                "evidence": action.evidence
            })
    
    if not unresolved:
        state.processing_notes.append("Stage 2: No unresolved owners")
        return state
    
    # TODO: maybe cache this prompt template?
    prompt = f"""Given this people directory and action items, match each action to the correct person.

People Directory:
{people_str}

Unresolved Actions:
{json.dumps(unresolved, indent=2)}

For each action, determine the best matching person from the directory. Consider:
- Name variations (e.g., "Emily" → "Emily Carter")
- Role inference (e.g., "backend work" → Backend Engineer)
- Context from evidence quotes

Respond ONLY with valid JSON:
{{
  "matches": [
    {{
      "action_id": "action_1",
      "matched_name": "Full Name from directory",
      "confidence": 0.95,
      "reasoning": "Brief explanation"
    }}
  ]
}}"""

    try:
        result_text = call_openai_with_retry(
            prompt=prompt,
            system_message="You are an expert at matching names and roles. Output only valid JSON.",
            max_tokens=2000
        )
        
        result_text = clean_json_response(result_text)
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        
        # apply the matches
        cnt = 0
        for match in result.get("matches", []):
            action_id = match.get("action_id")
            matched_name = match.get("matched_name")
            confidence = match.get("confidence", 0.0)
            
            if matched_name in state.people_directory:
                person = state.people_directory[matched_name]
                
                # find and update the action
                for action in state.action_items:
                    if action.id == action_id:
                        action.owner_name = matched_name
                        action.owner_email = person.email
                        action.owner_role = person.role
                        action.confidence = confidence
                        
                        # flag low confidence matches for review
                        if confidence < config.CONFIDENCE_THRESHOLD:
                            action.needs_review = True
                            action.validation_notes.append(
                                f"Low confidence match ({confidence:.2f}): {match.get('reasoning', '')}"
                            )
                        
                        cnt += 1
                        break
        
        state.stage_completed = "owner_resolution"
        state.processing_notes.append(
            f"Stage 2: Resolved {cnt} owners via LLM"
        )
        
        return state
        
    except Exception as e:
        state.processing_notes.append(f"Stage 2 LLM ERROR: {str(e)}")
        return state  # continue with partial resolution


def resolve_owners(state: MeetingState) -> MeetingState:
    """Main entry point for owner resolution"""
    # first pass - try exact matches
    exact = 0
    for action in state.action_items:
        if action.owner_name:
            person = find_exact_match(action.owner_name, state.people_directory)
            if person:
                action.owner_email = person.email
                action.owner_role = person.role
                action.confidence = 1.0
                exact += 1
    
    state.processing_notes.append(f"Stage 2: Found {exact} exact matches")
    
    # second pass - use LLM for fuzzy matching
    state = resolve_owners_with_llm(state)
    
    # mark anything still unresolved
    for action in state.action_items:
        if not action.owner_email:
            action.needs_review = True
            action.validation_notes.append("Owner could not be resolved")
    
    return state
