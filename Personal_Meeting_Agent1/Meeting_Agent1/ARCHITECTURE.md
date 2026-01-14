# 🏗️ Meeting Agent Architecture & Flow

## 📊 System Overview

```
USER INPUT
    ↓
┌─────────────────────────────────────┐
│   Streamlit Web Interface (app.py)  │
│                                     │
│  • Upload meeting transcript        │
│  • Upload people directory (JSON)   │
│  • Click "Run Agent"                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  MeetingAgentOrchestrator           │
│  (orchestrator.py)                  │
│                                     │
│  Manages the entire pipeline        │
└─────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│         6 PROCESSING STAGES (Sequential)         │
│                                                  │
│  1️⃣  Extract Intelligence (LLM)                 │
│  2️⃣  Resolve Owners (Name Matching)             │
│  3️⃣  Resolve Deadlines (Date Parsing)           │
│  4️⃣  Validate Items (Quality Check)             │
│  5️⃣  Generate Messages (Email Drafts)           │
│  6️⃣  Simulate Emails (Send Triggers)            │
└──────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│      FINAL OUTPUT                   │
│                                     │
│  • JSON structured data             │
│  • Text summary                     │
│  • Email logs                       │
└─────────────────────────────────────┘
    ↓
  DISPLAY ON UI / DOWNLOAD
```

---

## 🗂️ File Structure & Relationships

### **Core Files**

```
config.py
├─ OPENROUTER_API_KEY (from .env)
├─ OPENROUTER_MODEL ("openai/gpt-4o-mini")
├─ LLM_TEMPERATURE (0.1)
├─ REFERENCE_DATE (from .env or today)
└─ Used by: Every stage, orchestrator, utils

models.py
├─ ActionItem (id, description, owner, deadline)
├─ Decision (id, description, made_by)
├─ Risk (id, description, category)
├─ Person (name, role, email)
├─ MeetingState (holds all the above)
├─ FinalOutput (final structured results)
└─ Used by: All stages, orchestrator

utils.py
├─ clean_json_response() → Strips markdown from AI responses
├─ call_openai_with_retry() → Calls OpenRouter API with auto-retry
├─ parse_json_safely() → Parses JSON without crashing
└─ Used by: All stages for API calls

orchestrator.py
├─ MeetingAgentOrchestrator class
│  ├─ __init__() → Initialize with transcript + people directory
│  ├─ run_pipeline() → Execute all 6 stages in order
│  ├─ _generate_final_output() → Create final output
│  ├─ _export_json() → Save JSON to file
│  ├─ _export_summary() → Save text summary
│  └─ _load_people_directory() → Parse people.json
└─ Used by: app.py
```

### **UI Layer**

```
app.py (Streamlit)
├─ load_sample_transcripts() → Load example meetings
└─ main()
   ├─ TAB 1: Input
   │  ├─ Paste transcript
   │  ├─ Upload people.json
   │  └─ Set reference date
   ├─ TAB 2: Process
   │  └─ Click "Run Agent" → calls orchestrator.run_pipeline()
   └─ TAB 3: Results
      ├─ Display action items
      ├─ Display decisions
      ├─ Display risks
      ├─ Display follow-up messages
      ├─ Display email triggers
      └─ Download buttons (JSON & Summary)
```

### **Processing Pipeline (stages/)**

```
Stage 1: stage1_extraction.py
├─ Input: MeetingState with transcript
├─ Process: LLM extracts 3 things
│  ├─ Action items (tasks to do)
│  ├─ Decisions (choices made)
│  └─ Risks (concerns/issues)
└─ Output: MeetingState with extracted items

Stage 2: stage2_owner_resolution.py
├─ Input: MeetingState with action items (no owners yet)
├─ Process:
│  ├─ Try exact name matching with people directory
│  └─ Use LLM to resolve ambiguous names
└─ Output: MeetingState with owner_email + owner_name filled

Stage 3: stage3_deadline_resolution.py
├─ Input: MeetingState with deadline_text (e.g., "next Friday")
├─ Process:
│  ├─ Try rule-based parsing (regex patterns)
│  └─ Use LLM for complex dates
└─ Output: MeetingState with deadline_date (ISO format)

Stage 4: stage4_validation_agent.py
├─ Input: MeetingState (fully resolved)
├─ Process: Validate quality
│  ├─ Check owners exist in directory
│  ├─ Check deadlines are valid
│  └─ Flag items for human review
└─ Output: MeetingState with needs_review flags

Stage 5: stage5_message_generator.py
├─ Input: MeetingState with validated items
├─ Process: LLM generates personalized emails
│  ├─ Group action items by owner
│  └─ Generate follow-up message for each person
└─ Output: MeetingState with follow_up_messages

Stage 6: stage6_email_simulator.py
├─ Input: MeetingState with follow-up messages
├─ Process: Simulate sending emails
│  ├─ Create email trigger objects
│  └─ Log them (don't actually send)
└─ Output: MeetingState with email_triggers
```

---

## 🔄 Data Flow Through Pipeline

```
USER INPUTS:
┌──────────────────────────────────┐
│ Meeting Transcript               │
│ People Directory (JSON)          │
│ Reference Date                   │
└──────────────────────────────────┘
          ↓
    ORCHESTRATOR CREATES
    MeetingState object
          ↓
┌─────────────────────────────────────────┐
│ STAGE 1: Extract Intelligence           │
│                                         │
│ state.action_items = []                 │
│ state.decisions = []                    │
│ state.risks = []                        │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ STAGE 2: Resolve Owners                 │
│                                         │
│ for each action_item:                   │
│   action_item.owner_name → owner_email  │
│   action_item.owner_email → from people │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ STAGE 3: Resolve Deadlines              │
│                                         │
│ for each action_item:                   │
│   action_item.deadline_text → deadline  │
│   "next Friday" → "2026-01-17"          │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ STAGE 4: Validate Quality               │
│                                         │
│ Check all items are complete            │
│ Flag suspicious items for review        │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ STAGE 5: Generate Messages              │
│                                         │
│ Group action_items by owner_email       │
│ Create personalized email for each      │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│ STAGE 6: Simulate Emails                │
│                                         │
│ Create email trigger objects            │
│ Log them to state.email_triggers        │
└─────────────────────────────────────────┘
          ↓
    ORCHESTRATOR CONVERTS
    MeetingState → FinalOutput
          ↓
    ORCHESTRATOR EXPORTS
    ├─ JSON to outputs/meeting_output.json
    ├─ Summary to outputs/meeting_summary.txt
    └─ Email logs to state
          ↓
    APP DISPLAYS RESULTS
    └─ Shows on UI / Ready for download
```

---

## 🔌 API Integration

### **OpenRouter API Call Flow**

```
Stage needs AI assistance
    ↓
Call utils.call_openai_with_retry()
    ↓
├─ Prepare prompt
├─ Create HTTP POST to OpenRouter
│  URL: https://openrouter.ai/api/v1/chat/completions
│  Headers:
│  ├─ Authorization: Bearer {OPENROUTER_API_KEY}
│  └─ Content-Type: application/json
│  Body:
│  ├─ model: "openai/gpt-4o-mini"
│  ├─ messages: [system_msg, user_msg]
│  ├─ temperature: {LLM_TEMPERATURE}
│  └─ max_tokens: {LLM_MAX_TOKENS}
    ↓
Check response status
    ├─ 200 OK → Parse and return
    └─ Error → Retry (up to 3 times with exponential backoff)
    ↓
Clean response with utils.clean_json_response()
    ↓
Return to stage
```

---

## 🔐 Configuration & Security

### **config.py** (Loaded from .env)

```
OPENROUTER_API_KEY
├─ Source: .env file
├─ Format: sk-or-v1-xxxxx
├─ Used by: All stages via utils.py
└─ Validated on startup

REFERENCE_DATE
├─ Source: .env (default: today)
├─ Format: YYYY-MM-DD (2026-01-10)
├─ Used by: stage3_deadline_resolution.py
└─ Can be overridden in UI

OPENROUTER_MODEL
├─ Value: "openai/gpt-4o-mini"
└─ Used by: utils.call_openai_with_retry()

LLM SETTINGS
├─ LLM_TEMPERATURE: 0.1 (very deterministic)
├─ LLM_MAX_TOKENS: 4000 (response length limit)
└─ CONFIDENCE_THRESHOLD: 0.7 (70% for flagging)
```

---

## 📥 Input Data Format

### **Meeting Transcript** (Plain Text)

```
[HH:MM] Speaker Name: What they said
[HH:MM] Another Person: Their response

Example:
[00:00] Sarah: We need to launch by next Friday
[00:30] Mike: I'll handle the backend
[01:00] Sarah: Great! Mike, is that deadline okay?
```

### **People Directory** (data/people.json)

```json
{
  "Sarah Johnson": {
    "email": "sarah@company.com",
    "role": "Product Manager"
  },
  "Mike Davis": {
    "email": "mike@company.com",
    "role": "Backend Engineer"
  }
}
```

---

## 📤 Output Data Format

### **JSON Output** (outputs/meeting_output.json)

```json
{
  "action_items": [
    {
      "id": "action_1",
      "description": "Task description",
      "owner_name": "Mike Davis",
      "owner_email": "mike@company.com",
      "deadline_text": "next Friday",
      "deadline_date": "2026-01-17",
      "evidence": ["[00:30] Mike: I'll handle the backend"],
      "needs_review": false
    }
  ],
  "decisions": [
    {
      "id": "decision_1",
      "description": "Decision made",
      "made_by": "Sarah"
    }
  ],
  "risks": [
    {
      "id": "risk_1",
      "description": "Risk identified",
      "category": "deadline"
    }
  ],
  "follow_up_messages": [
    {
      "to_email": "mike@company.com",
      "to_name": "Mike Davis",
      "subject": "Follow-up: Your Action Items",
      "body": "Email content..."
    }
  ],
  "email_triggers": [
    {
      "to": "mike@company.com",
      "to_name": "Mike Davis",
      "subject": "Follow-up: Your Action Items",
      "status": "simulated",
      "triggered_at": "2026-01-10T02:30:00"
    }
  ]
}
```

### **Text Summary** (outputs/meeting_summary.txt)

```
MEETING ANALYSIS SUMMARY
============================================================

ACTION ITEMS
------------------------------------------------------------
[action_1] Task description
  Owner: Mike Davis (mike@company.com)
  Deadline: 2026-01-17

DECISIONS
------------------------------------------------------------
[decision_1] Decision made
  Made by: Sarah

RISKS
------------------------------------------------------------
[risk_1] Risk identified
```

---

## 🎯 How Each Stage Uses Other Components

```
Stage 1 (Extraction)
├─ Uses: config (LLM settings)
├─ Uses: utils.call_openai_with_retry() (API call)
├─ Uses: models (ActionItem, Decision, Risk)
└─ Produces: state.action_items, state.decisions, state.risks

Stage 2 (Owner Resolution)
├─ Uses: config (LLM settings)
├─ Uses: utils.call_openai_with_retry() (API call)
├─ Uses: state.people_directory (from loaded JSON)
└─ Produces: action_item.owner_email, owner_name

Stage 3 (Deadline Resolution)
├─ Uses: config (REFERENCE_DATE)
├─ Uses: utils.call_openai_with_retry() (API call)
└─ Produces: action_item.deadline_date (ISO format)

Stage 4 (Validation)
├─ Uses: config (CONFIDENCE_THRESHOLD)
├─ Uses: utils.call_openai_with_retry() (API call)
└─ Produces: action_item.needs_review flag

Stage 5 (Message Generation)
├─ Uses: config (LLM settings)
├─ Uses: utils.call_openai_with_retry() (API call)
└─ Produces: state.follow_up_messages

Stage 6 (Email Simulation)
├─ No external dependencies
└─ Produces: state.email_triggers
```

---

## 🚀 User Journey

```
1. USER OPENS APP
   └─ app.py starts Streamlit server
      └─ Validates config via validate_config()

2. USER INPUTS DATA (Tab 1)
   ├─ Pastes meeting transcript
   ├─ Uploads people.json
   └─ Sets reference date

3. USER CLICKS "RUN AGENT" (Tab 2)
   ├─ Creates MeetingAgentOrchestrator instance
   ├─ Runs orchestrator.run_pipeline()
   │  ├─ Stage 1: Extract intelligence
   │  ├─ Stage 2: Resolve owners
   │  ├─ Stage 3: Resolve deadlines
   │  ├─ Stage 4: Validate items
   │  ├─ Stage 5: Generate messages
   │  └─ Stage 6: Simulate emails
   ├─ Converts to FinalOutput
   └─ Exports JSON & Summary files

4. USER VIEWS RESULTS (Tab 3)
   ├─ Sees action items, decisions, risks
   ├─ Reviews follow-up messages
   ├─ Checks email triggers
   └─ Downloads JSON or Summary

5. USER DOWNLOADS OUTPUT
   └─ Gets files ready for use
```

---

## ⚙️ Key Classes & Their Relationships

```
MeetingState (models.py)
├─ Attributes:
│  ├─ transcript: str
│  ├─ people_directory: Dict[str, Person]
│  ├─ reference_date: date
│  ├─ action_items: List[ActionItem]
│  ├─ decisions: List[Decision]
│  ├─ risks: List[Risk]
│  ├─ follow_up_messages: List[FollowUpMessage]
│  ├─ email_triggers: List[EmailTrigger]
│  └─ processing_notes: List[str]
└─ Passed through all 6 stages sequentially

MeetingAgentOrchestrator (orchestrator.py)
├─ state: MeetingState
├─ Methods:
│  ├─ __init__() → Create state from inputs
│  ├─ run_pipeline() → Execute stages 1-6
│  ├─ _generate_final_output() → Convert to FinalOutput
│  ├─ _export_json() → Save JSON
│  └─ _export_summary() → Save text summary
└─ Manages flow and exports

FinalOutput (models.py)
├─ action_items, decisions, risks
├─ follow_up_messages, email_triggers
├─ meeting_summary, metadata
└─ Ready for UI display / download
```

---

## 🔍 Error Handling

```
Try/Except blocks at:
├─ API calls (with retry logic)
│  └─ Retries up to 3 times with exponential backoff
├─ JSON parsing
│  └─ Falls back to safe defaults
├─ Name matching
│  └─ Flags as needs_review if uncertain
└─ Deadline parsing
   └─ Flags as needs_review if can't parse

All errors logged via logger.error()
UI catches exceptions and shows user-friendly messages
```

---

## 📊 Processing Time Estimate

```
For a 2,000-word transcript:
├─ Stage 1 (Extraction): ~15-20 seconds (LLM call)
├─ Stage 2 (Owner Resolution): ~5-10 seconds (LLM call)
├─ Stage 3 (Deadline Resolution): ~5-10 seconds (LLM call)
├─ Stage 4 (Validation): ~5-10 seconds (LLM call)
├─ Stage 5 (Message Generation): ~10-15 seconds (LLM call)
├─ Stage 6 (Email Simulation): <1 second
├─ Output Export: <1 second
└─ TOTAL: 40-65 seconds

Cost estimate:
└─ ~$0.002-0.005 per transcript (OpenRouter pricing)
```

---

## 🎓 To Understand Each Part

**Want to learn about...**

| Topic | Read This |
|-------|-----------|
| **Data structures** | `models.py` |
| **Configuration** | `config.py` |
| **Web interface** | `app.py` |
| **Pipeline orchestration** | `orchestrator.py` |
| **Utility functions** | `utils.py` |
| **Intelligence extraction** | `stages/stage1_extraction.py` |
| **Owner matching** | `stages/stage2_owner_resolution.py` |
| **Date parsing** | `stages/stage3_deadline_resolution.py` |
| **Quality validation** | `stages/stage4_validation_agent.py` |
| **Email generation** | `stages/stage5_message_generator.py` |
| **Email simulation** | `stages/stage6_email_simulator.py` |

---

**This architecture is designed to be:**
- ✅ **Modular** - Each stage is independent
- ✅ **Sequential** - Clear order of operations
- ✅ **Extensible** - Easy to add new stages
- ✅ **Maintainable** - Clear separation of concerns
- ✅ **Transparent** - Full logging and debugging
