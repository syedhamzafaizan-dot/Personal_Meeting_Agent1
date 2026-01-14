"""
Orchestration Layer - Pipeline Controller
Controls execution order and manages state flow between stages
"""
import json
import os
from datetime import datetime
from typing import Dict
from models import MeetingState, Person, FinalOutput
import config

# Import all stages
from stages.stage1_extraction import extract_intelligence
from stages.stage2_owner_resolution import resolve_owners
from stages.stage3_deadline_resolution import resolve_deadlines
from stages.stage4_validation_agent import validate_state
from stages.stage5_message_generator import generate_messages
from stages.stage6_email_simulator import simulate_email_triggers, export_email_logs


class MeetingAgentOrchestrator:
    """
    Main orchestrator that controls the pipeline execution
    """
    
    def __init__(self, transcript: str, people_directory_path: str, reference_date=None):
        """
        Initialize orchestrator with inputs
        
        Args:
            transcript: Meeting transcript text
            people_directory_path: Path to people.json
            reference_date: Reference date for deadline resolution
        """
        self.transcript = transcript
        self.people_directory = self._load_people_directory(people_directory_path)
        self.reference_date = reference_date or config.REFERENCE_DATE
        
        # Initialize state
        self.state = MeetingState(
            transcript=transcript,
            people_directory=self.people_directory,
            reference_date=self.reference_date
        )
        
        # Ensure output directory exists
        os.makedirs(config.OUTPUT_DIRECTORY, exist_ok=True)
    
    def _load_people_directory(self, path: str) -> Dict[str, Person]:
        """Load and parse people directory"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        people_dir = {}
        for name, info in data.items():
            people_dir[name] = Person(
                name=name,
                email=info['email'],
                role=info['role']
            )
        
        return people_dir
    
    def run_pipeline(self) -> FinalOutput:
        """
        Execute the complete pipeline
        """
        print("=" * 70)
        print("MEETING AGENT PIPELINE STARTED")
        print("=" * 70)
        
        try:
            # Stage 1: Extract intelligence from transcript
            print("\n[STAGE 1] Extracting intelligence from transcript...")
            self.state = extract_intelligence(self.state)
            print(f"✓ Extracted {len(self.state.action_items)} actions, "
                  f"{len(self.state.decisions)} decisions, {len(self.state.risks)} risks")
            
            # Stage 2: Resolve owners
            print("\n[STAGE 2] Resolving action item owners...")
            self.state = resolve_owners(self.state)
            resolved_count = sum(1 for a in self.state.action_items if a.owner_email)
            print(f"✓ Resolved {resolved_count}/{len(self.state.action_items)} owners")
            
            # Stage 3: Resolve deadlines
            print("\n[STAGE 3] Resolving deadlines...")
            self.state = resolve_deadlines(self.state)
            deadline_count = sum(1 for a in self.state.action_items if a.deadline_date)
            print(f"✓ Resolved {deadline_count}/{len(self.state.action_items)} deadlines")
            
            # Stage 4: Validation
            print("\n[STAGE 4] Running validation agent...")
            self.state = validate_state(self.state)
            review_count = sum(1 for a in self.state.action_items if a.needs_review)
            print(f"✓ Validated all items, {review_count} need human review")
            
            # Stage 5: Generate follow-up messages
            print("\n[STAGE 5] Generating follow-up messages...")
            self.state = generate_messages(self.state)
            print(f"✓ Generated {len(self.state.follow_up_messages)} messages")
            
            # Stage 6: Simulate email triggers
            print("\n[STAGE 6] Simulating email triggers...")
            self.state = simulate_email_triggers(self.state)
            print(f"✓ Simulated {len(self.state.email_triggers)} email triggers")
            
            # Generate final output
            print("\n[FINAL] Generating outputs...")
            final_output = self._generate_final_output()
            
            print("\n" + "=" * 70)
            print("PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 70)
            
            return final_output
            
        except Exception as e:
            print(f"\n[ERROR] Pipeline failed: {str(e)}")
            raise
    
    def _generate_final_output(self) -> FinalOutput:
        """Generate final structured output and export files"""
        
        # Create summary
        summary = self._generate_summary()
        
        # Create final output object
        final_output = FinalOutput(
            meeting_summary=summary,
            action_items=self.state.action_items,
            decisions=self.state.decisions,
            risks=self.state.risks,
            follow_up_messages=self.state.follow_up_messages,
            email_triggers=self.state.email_triggers,
            metadata={
                "reference_date": str(self.reference_date),
                "processing_notes": self.state.processing_notes,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Export to JSON
        self._export_json(final_output)
        
        # Export email logs
        export_email_logs(self.state, config.OUTPUT_DIRECTORY)
        
        # Export human-readable summary
        self._export_summary(final_output)
        
        return final_output
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary"""
        lines = []
        lines.append("MEETING ANALYSIS SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Reference Date: {self.reference_date}")
        lines.append("")
        
        # Action Items
        lines.append(f"ACTION ITEMS ({len(self.state.action_items)})")
        lines.append("-" * 60)
        for action in self.state.action_items:
            lines.append(f"\n[{action.id}] {action.description}")
            lines.append(f"  Owner: {action.owner_name or 'UNASSIGNED'} ({action.owner_email or 'N/A'})")
            lines.append(f"  Deadline: {action.deadline_date or action.deadline_text or 'None'}")
            if action.needs_review:
                lines.append(f"  ⚠️  NEEDS REVIEW: {', '.join(action.validation_notes)}")
        
        # Decisions
        lines.append(f"\n\nDECISIONS ({len(self.state.decisions)})")
        lines.append("-" * 60)
        for decision in self.state.decisions:
            lines.append(f"\n[{decision.id}] {decision.description}")
            if decision.made_by:
                lines.append(f"  Made by: {decision.made_by}")
        
        # Risks
        lines.append(f"\n\nRISKS & OPEN QUESTIONS ({len(self.state.risks)})")
        lines.append("-" * 60)
        for risk in self.state.risks:
            lines.append(f"\n[{risk.id}] {risk.description}")
            lines.append(f"  Category: {risk.category}")
            if risk.mentioned_by:
                lines.append(f"  Mentioned by: {risk.mentioned_by}")
        
        return "\n".join(lines)
    
    def _export_json(self, final_output: FinalOutput):
        """Export structured JSON output"""
        output_file = f"{config.OUTPUT_DIRECTORY}/meeting_output.json"
        
        # Convert to dict
        output_dict = {
            "meeting_summary": final_output.meeting_summary,
            "action_items": [
                {
                    "id": a.id,
                    "description": a.description,
                    "owner_name": a.owner_name,
                    "owner_email": a.owner_email,
                    "owner_role": a.owner_role,
                    "deadline_text": a.deadline_text,
                    "deadline_date": str(a.deadline_date) if a.deadline_date else None,
                    "evidence": a.evidence,
                    "confidence": a.confidence,
                    "needs_review": a.needs_review,
                    "validation_notes": a.validation_notes
                }
                for a in final_output.action_items
            ],
            "decisions": [
                {
                    "id": d.id,
                    "description": d.description,
                    "made_by": d.made_by,
                    "evidence": d.evidence,
                    "timestamp": d.timestamp
                }
                for d in final_output.decisions
            ],
            "risks": [
                {
                    "id": r.id,
                    "description": r.description,
                    "category": r.category,
                    "mentioned_by": r.mentioned_by,
                    "evidence": r.evidence,
                    "timestamp": r.timestamp
                }
                for r in final_output.risks
            ],
            "follow_up_messages": [
                {
                    "to_email": m.to_email,
                    "to_name": m.to_name,
                    "subject": m.subject,
                    "body": m.body,
                    "action_items": m.action_items
                }
                for m in final_output.follow_up_messages
            ],
            "metadata": final_output.metadata
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported JSON to: {output_file}")
    
    def _export_summary(self, final_output: FinalOutput):
        """Export human-readable summary"""
        output_file = f"{config.OUTPUT_DIRECTORY}/meeting_summary.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_output.meeting_summary)
        
        print(f"✓ Exported summary to: {output_file}")


def run_agent(transcript_path: str, people_path: str, reference_date=None) -> FinalOutput:
    """
    Convenience function to run the agent
    
    Args:
        transcript_path: Path to meeting transcript file
        people_path: Path to people.json
        reference_date: Optional reference date
    
    Returns:
        FinalOutput object
    """
    # Validate config
    config.validate_config()
    
    # Load transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Create and run orchestrator
    orchestrator = MeetingAgentOrchestrator(
        transcript=transcript,
        people_directory_path=people_path,
        reference_date=reference_date
    )
    
    return orchestrator.run_pipeline()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python orchestrator.py <transcript_path> <people_json_path>")
        sys.exit(1)
    
    transcript_path = sys.argv[1]
    people_path = sys.argv[2]
    
    result = run_agent(transcript_path, people_path)
    print("\n✓ Agent execution completed!")
