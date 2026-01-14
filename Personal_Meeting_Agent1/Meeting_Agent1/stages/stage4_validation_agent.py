"""
Stage 4: Mini Autonomous Validation Agent
Validates owners, deadlines, and consistency of extracted items
"""
import json
from typing import List, Dict, Any
from models import MeetingState, ActionItem
import config
from utils import call_openai_with_retry, clean_json_response


class ValidationAgent:
    """Autonomous agent with validation tools"""
    
    def __init__(self):
        self.validation_results = []
    
    def validate_owner(self, action: ActionItem) -> Dict[str, Any]:
        """Validate if owner is properly assigned"""
        issues = []
        
        if not action.owner_name:
            issues.append("No owner assigned")
        
        if action.owner_name and not action.owner_email:
            issues.append(f"Owner '{action.owner_name}' not found in directory")
        
        if action.confidence and action.confidence < config.CONFIDENCE_THRESHOLD:
            issues.append(f"Low confidence match: {action.confidence:.2f}")
        
        return {
            "action_id": action.id,
            "tool": "validate_owner",
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def validate_deadline(self, action: ActionItem) -> Dict[str, Any]:
        """Validate if deadline is properly resolved"""
        issues = []
        
        if action.deadline_text and not action.deadline_date:
            issues.append(f"Could not resolve deadline: '{action.deadline_text}'")
        
        if action.deadline_date:
            # Check if deadline is in the past (relative to reference date)
            # This would need reference_date passed in, skipping for now
            pass
        
        return {
            "action_id": action.id,
            "tool": "validate_deadline",
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def check_consistency(self, actions: List[ActionItem]) -> Dict[str, Any]:
        """Check for conflicting or duplicate actions"""
        issues = []
        
        # Check for potential duplicates
        descriptions = [a.description.lower() for a in actions]
        seen = set()
        for desc in descriptions:
            if desc in seen:
                issues.append(f"Potential duplicate action: {desc[:50]}...")
            seen.add(desc)
        
        # Check for actions with same owner and same deadline
        owner_deadline_pairs = {}
        for action in actions:
            if action.owner_email and action.deadline_date:
                key = (action.owner_email, action.deadline_date)
                if key in owner_deadline_pairs:
                    owner_deadline_pairs[key].append(action.id)
                else:
                    owner_deadline_pairs[key] = [action.id]
        
        for (owner, deadline), action_ids in owner_deadline_pairs.items():
            if len(action_ids) > 3:
                issues.append(
                    f"Many actions ({len(action_ids)}) for {owner} on {deadline}"
                )
        
        return {
            "tool": "check_consistency",
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def autonomous_validation(self, state: MeetingState) -> MeetingState:
        """
        Autonomous agent that decides which validations to run
        """
        validation_report = {
            "total_actions": len(state.action_items),
            "owner_validations": [],
            "deadline_validations": [],
            "consistency_check": None,
            "needs_human_review": []
        }
        
        # Run validations on each action
        for action in state.action_items:
            # Validate owner
            owner_result = self.validate_owner(action)
            validation_report["owner_validations"].append(owner_result)
            
            if not owner_result["valid"]:
                action.needs_review = True
                for issue in owner_result["issues"]:
                    if issue not in action.validation_notes:
                        action.validation_notes.append(issue)
            
            # Validate deadline
            deadline_result = self.validate_deadline(action)
            validation_report["deadline_validations"].append(deadline_result)
            
            if not deadline_result["valid"]:
                action.needs_review = True
                for issue in deadline_result["issues"]:
                    if issue not in action.validation_notes:
                        action.validation_notes.append(issue)
        
        # Run consistency check
        consistency_result = self.check_consistency(state.action_items)
        validation_report["consistency_check"] = consistency_result
        
        # Collect actions needing review
        for action in state.action_items:
            if action.needs_review:
                validation_report["needs_human_review"].append({
                    "action_id": action.id,
                    "description": action.description,
                    "issues": action.validation_notes
                })
        
        # Use LLM to identify additional issues
        validation_report = self._llm_validation_check(state, validation_report)
        
        # Store results
        state.processing_notes.append(
            f"Stage 4: Validated {len(state.action_items)} actions, "
            f"{len(validation_report['needs_human_review'])} need review"
        )
        
        state.stage_completed = "validation"
        return state
    
    def _llm_validation_check(self, state: MeetingState, report: Dict) -> Dict:
        """Use LLM to identify additional validation issues"""
        
        # Prepare action summary
        action_summary = []
        for action in state.action_items:
            action_summary.append({
                "id": action.id,
                "description": action.description,
                "owner": action.owner_name,
                "deadline": str(action.deadline_date) if action.deadline_date else action.deadline_text,
                "needs_review": action.needs_review
            })
        
        prompt = f"""Review these action items for potential issues:

{json.dumps(action_summary, indent=2)}

Identify:
1. Ambiguous or unclear action descriptions
2. Actions that might be missing critical information
3. Potential conflicts or dependencies between actions
4. Actions that seem unrealistic given the deadline

Respond ONLY with valid JSON:
{{
  "issues": [
    {{
      "action_id": "action_1",
      "severity": "high|medium|low",
      "issue": "Description of the issue",
      "recommendation": "What should be done"
    }}
  ]
}}"""

        try:
            result_text = call_openai_with_retry(
                prompt=prompt,
                system_message="You are a validation expert. Output only valid JSON.",
                max_tokens=2000
            )
            
            # Clean markdown
            result_text = clean_json_response(result_text)
            
            result = json.loads(result_text)
            
            # Apply LLM-identified issues
            for issue_item in result.get("issues", []):
                action_id = issue_item.get("action_id")
                severity = issue_item.get("severity", "medium")
                issue_text = issue_item.get("issue", "")
                
                # Find action and add note
                for action in state.action_items:
                    if action.id == action_id:
                        if severity == "high":
                            action.needs_review = True
                        
                        note = f"[{severity.upper()}] {issue_text}"
                        if note not in action.validation_notes:
                            action.validation_notes.append(note)
                        break
            
            report["llm_issues"] = result.get("issues", [])
            
        except Exception as e:
            state.processing_notes.append(f"Stage 4 LLM validation ERROR: {str(e)}")
        
        return report


def validate_state(state: MeetingState) -> MeetingState:
    """Main validation function"""
    agent = ValidationAgent()
    return agent.autonomous_validation(state)
