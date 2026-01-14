# 🤖 AI Meeting Agent

> **🎯 New here? Check out [README_SIMPLE.md](README_SIMPLE.md) for a friendlier introduction!**

An autonomous AI agent that transforms raw meeting transcripts into structured, actionable outputs with minimal human intervention.

## 📋 Overview

This project implements an AI-powered meeting analysis system that:
- Extracts action items, decisions, and risks from meeting transcripts
- Resolves action item owners against a people directory
- Converts relative deadlines (e.g., "next Friday") to absolute dates
- Validates all extracted information
- Generates personalized follow-up messages
- Simulates email triggering

## 🏗️ Architecture

The system follows a multi-stage pipeline architecture:

1. **Stage 1: Transcript Intelligence Extraction** - LLM extracts actions, decisions, risks with evidence
2. **Stage 2: Owner Resolution Engine** - Matches names/roles to people directory
3. **Stage 3: Deadline Resolution Engine** - Converts relative dates to ISO dates
4. **Stage 4: Mini Autonomous Validation Agent** - Validates owners, deadlines, consistency
5. **Stage 5: Follow-up Message Generator** - Creates personalized draft emails
6. **Stage 6: Email Trigger Simulation** - Logs trigger events without sending

All stages are orchestrated through a central pipeline controller that manages state flow and handles retries.

## 📁 Project Structure

```
Meeting_Agent/
├── .env                    # Environment variables (API keys)
├── .gitignore
├── requirements.txt        # Python dependencies
├── config.py              # Global configuration
├── models.py              # Pydantic data models
├── orchestrator.py        # Main pipeline controller
├── app.py                 # Streamlit UI
├── stages/                # Individual pipeline stages
│   ├── stage1_extraction.py
│   ├── stage2_owner_resolution.py
│   ├── stage3_deadline_resolution.py
│   ├── stage4_validation_agent.py
│   ├── stage5_message_generator.py
│   └── stage6_email_simulator.py
├── data/                  # Input data
│   ├── people.json
│   ├── sprint_planning.txt
│   ├── product_sync.txt
│   └── incident_review.txt
└── outputs/               # Generated outputs
    ├── meeting_output.json
    ├── meeting_summary.txt
    └── email_triggers.json
```

## 🚀 Setup

### Prerequisites
- Python 3.9+
- OpenAI API key

### Installation

1. **Clone/Download the project**

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   
   Edit `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   REFERENCE_DATE=2026-01-10
   ```

4. **Verify Setup**
   ```powershell
   python -c "import config; config.validate_config()"
   ```

## 💻 Usage

### Option 1: Streamlit UI (Recommended)

Run the interactive web interface:

```powershell
streamlit run app.py
```

This will open a browser with:
- Input tab for transcript and people directory
- Process tab to run the agent
- Results tab to view and download outputs

### Option 2: Command Line

Run directly from terminal:

```powershell
python orchestrator.py data/sprint_planning.txt data/people.json
```

### Option 3: Python API

Use in your own code:

```python
from orchestrator import run_agent

result = run_agent(
    transcript_path="data/sprint_planning.txt",
    people_path="data/people.json"
)

# Access results
print(f"Found {len(result.action_items)} action items")
print(f"Found {len(result.decisions)} decisions")
```

## 📊 Outputs

The agent generates three types of outputs:

1. **meeting_output.json** - Structured JSON with all extracted data
2. **meeting_summary.txt** - Human-readable summary
3. **email_triggers.json** - Simulated email trigger logs

All outputs are saved to the `outputs/` directory.

## 📥 Input Format

### Meeting Transcript
Plain text with timestamps and speaker names:
```
[00:00] James: Sprint planning kickoff.
[00:45] Emily: I can deliver first draft by Friday.
[01:30] James: Decision: we will remove legacy signup flow.
```

### People Directory (people.json)
JSON mapping names to emails and roles:
```json
{
  "James Miller": {
    "email": "james.miller@example.com",
    "role": "Product Manager"
  }
}
```

## 🔧 Configuration

Key settings in `config.py`:

- `OPENAI_MODEL` - LLM model (default: gpt-4o-mini for cost efficiency)
- `LLM_TEMPERATURE` - 0.1 for consistency
- `CONFIDENCE_THRESHOLD` - 0.7 for owner matching
- `REFERENCE_DATE` - Date for deadline resolution

## 📝 Sample Data

Three sample meetings are included in `data/`:

1. **sprint_planning.txt** - Sprint planning meeting with multiple action items
2. **product_sync.txt** - Product sync with feature decisions
3. **incident_review.txt** - Post-incident review with technical tasks

## 🎯 Features

- **Autonomous Extraction** - No manual tagging required
- **Smart Owner Resolution** - Handles name variations and role inference
- **Intelligent Deadline Parsing** - Converts "next Friday", "in 2 weeks", etc.
- **Validation Agent** - Autonomous quality checks with validation tools
- **Personalized Messages** - Context-aware follow-up emails
- **Email Simulation** - Full email triggering logic without actual sending

## ⚠️ Assumptions

1. **Reference Date**: Deadlines are resolved relative to the configured reference date
2. **Name Matching**: First names alone are matched if unique in the directory
3. **OpenAI API**: Uses GPT-4o-mini for cost efficiency (~$0.15 per 1M input tokens)
4. **No Email Sending**: Email triggers are logged but not sent
5. **English Language**: Optimized for English meeting transcripts

## 💡 Cost Optimization

With a $20 OpenAI budget:
- Using `gpt-4o-mini` model (cost-effective)
- Average transcript (~3,000 tokens) costs ~$0.002 per processing
- Can process ~10,000 meetings with $20 budget
- Adjust `LLM_TEMPERATURE` and `LLM_MAX_TOKENS` in config for further optimization

## 🐛 Troubleshooting

**API Key Error**
- Verify `.env` file contains valid OpenAI API key
- Check key has credits remaining

**Import Errors**
- Run `pip install -r requirements.txt`
- Ensure Python 3.9+

**No Outputs Generated**
- Check `outputs/` directory exists
- Verify write permissions

**Poor Extraction Quality**
- Ensure transcript has timestamps and speaker names
- Verify people directory contains all participants
- Adjust `LLM_TEMPERATURE` in config.py

## 📄 License

This project is created for assessment purposes.

## 🤝 Contributing

This is an assessment project. For questions or issues, please contact the project maintainer.

## 📧 Contact

For questions about this implementation, please refer to the project documentation or raise an issue.

---

**Built with:** Python, OpenAI GPT-4, Streamlit, Pydantic
