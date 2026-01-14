"""
📊 Data Models - The Building Blocks of Our Agent

Think of these as "containers" that hold information in a structured way.
Like filling out a form with specific fields for each piece of information.
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """
    📝 A single task someone needs to complete
    
    Example: "Emily needs to finalize the signup copy by Friday"
    """
    id: str  # Unique identifier like "action_1"
    description: str  # What needs to be done
    
    # 👤 Who owns this task?
    owner_name: Optional[str] = None  # e.g., "Emily Carter"
    owner_email: Optional[str] = None  # e.g., "emily.carter@example.com"
    owner_role: Optional[str] = None  # e.g., "Product Designer"
    
    # ⏰ When is it due?
    deadline_text: Optional[str] = None  # Original phrase like "next Friday"
    deadline_date: Optional[date] = None  # Actual date like 2026-01-17
    
    # 📌 Proof from the meeting
    evidence: List[str] = Field(default_factory=list)  # Direct quotes
    
    # 🎯 Quality control
    confidence: Optional[float] = None  # How sure are we? (0.0 to 1.0)
    needs_review: bool = False  # Should a human double-check this?
    validation_notes: List[str] = Field(default_factory=list)  # Any issues found


class Decision(BaseModel):
    """
    ✅ An important decision made during the meeting
    
    Example: "Team decided to remove the legacy signup flow"
    """
    id: str  # Unique identifier
    description: str  # What was decided
    made_by: Optional[str] = None  # Who made the call
    evidence: List[str] = Field(default_factory=list)  # Quotes from meeting
    timestamp: Optional[str] = None  # When it was decided


class Risk(BaseModel):
    """
    ⚠️ A concern or question that was raised
    
    Example: "Too many dependencies might delay the demo"
    """
    id: str  # Unique identifier
    description: str  # What's the risk or question
    category: str  # Is it a "risk" or "open_question"?
    mentioned_by: Optional[str] = None  # Who brought it up
    evidence: List[str] = Field(default_factory=list)  # Quotes
    timestamp: Optional[str] = None  # When mentioned


class Person(BaseModel):
    """
    👤 A team member from the people directory
    """
    name: str  # Full name
    email: str  # Email address
    role: str  # Job title


class FollowUpMessage(BaseModel):
    """
    📧 A draft email to send to someone about their tasks
    """
    to_email: str  # Who gets this email
    to_name: str  # Their name
    subject: str  # Email subject line
    body: str  # The actual message
    action_items: List[str] = Field(default_factory=list)  # Which tasks it covers


class EmailTrigger(BaseModel):
    """
    📤 A record of an email we would send (but we're just simulating)
    """
    to: str  # Recipient email
    to_name: str  # Recipient name
    subject: str  # Email subject
    body: str  # Email content
    triggered_at: datetime  # When we "sent" it
    status: str = "simulated"  # Always "simulated" since we don't really send


class MeetingState(BaseModel):
    """
    🗂️ The "clipboard" that travels through each stage
    
    As each stage completes, it adds its results here.
    Think of it like a form being passed from desk to desk,
    with each person filling in their section.
    """
    transcript: str  # The meeting conversation
    people_directory: Dict[str, Person]  # Who's on the team
    reference_date: date  # What day to use as "today"
    
    # 📋 What we've extracted so far
    action_items: List[ActionItem] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    
    # 📧 Generated outputs
    follow_up_messages: List[FollowUpMessage] = Field(default_factory=list)
    email_triggers: List[EmailTrigger] = Field(default_factory=list)
    
    # 📊 Progress tracking
    stage_completed: str = "none"  # Which stage just finished
    processing_notes: List[str] = Field(default_factory=list)  # Log of what happened


class FinalOutput(BaseModel):
    """
    🎁 The final gift-wrapped results for the user
    """
    meeting_summary: str  # Human-readable overview
    action_items: List[ActionItem]  # All the tasks
    decisions: List[Decision]  # All the decisions
    risks: List[Risk]  # All the concerns
    follow_up_messages: List[FollowUpMessage]  # Draft emails
    email_triggers: List[EmailTrigger]  # Email simulation records
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Extra info
