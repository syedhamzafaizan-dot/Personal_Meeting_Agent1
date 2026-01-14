"""
Streamlit UI for Meeting Agent
Interactive interface to run the agent and view results
"""
import streamlit as st
import json
import os
from datetime import date
from orchestrator import MeetingAgentOrchestrator
import config


def load_sample_transcripts():
    """Load available sample transcripts"""
    transcript_dir = "data"
    if not os.path.exists(transcript_dir):
        return {}
    
    transcripts = {}
    for file in os.listdir(transcript_dir):
        if file.endswith('.txt'):
            with open(os.path.join(transcript_dir, file), 'r', encoding='utf-8') as f:
                transcripts[file] = f.read()
    
    return transcripts


def main():
    st.set_page_config(
        page_title="Meeting Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Meeting Agent")
    st.markdown("Transform meeting transcripts into actionable outputs")
    
    # Sidebar - Configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Check API key
    try:
        config.validate_config()
        st.sidebar.success("✓ OpenAI API Key configured")
    except ValueError as e:
        st.sidebar.error(f"❌ {str(e)}")
        st.error("Please configure your OpenAI API key in the .env file")
        st.stop()
    
    # Reference date
    reference_date = st.sidebar.date_input(
        "Reference Date",
        value=config.REFERENCE_DATE,
        help="Date used for resolving relative deadlines like 'next Friday'"
    )
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📝 Input", "🚀 Process", "📊 Results"])
    
    with tab1:
        st.header("Input Meeting Data")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Meeting Transcript")
            
            # Load sample transcripts
            samples = load_sample_transcripts()
            
            if samples:
                sample_choice = st.selectbox(
                    "Load sample transcript",
                    ["Custom"] + list(samples.keys())
                )
                
                if sample_choice != "Custom":
                    transcript = samples[sample_choice]
                else:
                    transcript = ""
            else:
                transcript = ""
            
            transcript_input = st.text_area(
                "Paste meeting transcript here",
                value=transcript,
                height=400,
                help="Timestamped meeting transcript with speaker names"
            )
            
            st.session_state['transcript'] = transcript_input
        
        with col2:
            st.subheader("People Directory")
            
            people_file = st.file_uploader(
                "Upload people.json",
                type=['json'],
                help="JSON file with names, roles, and emails"
            )
            
            if people_file:
                people_data = json.load(people_file)
                st.session_state['people_data'] = people_data
                st.success(f"✓ Loaded {len(people_data)} people")
                
                with st.expander("View people directory"):
                    st.json(people_data)
            
            elif os.path.exists(config.PEOPLE_DIRECTORY_PATH):
                with open(config.PEOPLE_DIRECTORY_PATH, 'r') as f:
                    people_data = json.load(f)
                    st.session_state['people_data'] = people_data
                    st.info(f"Using default people.json ({len(people_data)} people)")
            else:
                st.warning("No people directory loaded")
    
    with tab2:
        st.header("Process Meeting")
        
        if st.button("🚀 Run Agent", type="primary", use_container_width=True):
            
            if 'transcript' not in st.session_state or not st.session_state['transcript']:
                st.error("Please provide a meeting transcript")
                return
            
            if 'people_data' not in st.session_state:
                st.error("Please provide a people directory")
                return
            
            # Save temp files
            temp_transcript = "data/temp_transcript.txt"
            temp_people = "data/temp_people.json"
            
            os.makedirs("data", exist_ok=True)
            
            with open(temp_transcript, 'w', encoding='utf-8') as f:
                f.write(st.session_state['transcript'])
            
            with open(temp_people, 'w', encoding='utf-8') as f:
                json.dump(st.session_state['people_data'], f, indent=2)
            
            # Run orchestrator
            with st.spinner("Processing meeting transcript..."):
                try:
                    orchestrator = MeetingAgentOrchestrator(
                        transcript=st.session_state['transcript'],
                        people_directory_path=temp_people,
                        reference_date=reference_date
                    )
                    
                    # Show progress
                    progress_bar = st.progress(0)
                    status = st.empty()
                    
                    # Import all stage functions at the start
                    from stages.stage1_extraction import extract_intelligence
                    from stages.stage2_owner_resolution import resolve_owners
                    from stages.stage3_deadline_resolution import resolve_deadlines
                    from stages.stage4_validation_agent import validate_state
                    from stages.stage5_message_generator import generate_messages
                    from stages.stage6_email_simulator import simulate_email_triggers
                    
                    status.text("Stage 1: Extracting intelligence...")
                    progress_bar.progress(16)
                    orchestrator.state = extract_intelligence(orchestrator.state)
                    
                    status.text("Stage 2: Resolving owners...")
                    progress_bar.progress(33)
                    orchestrator.state = resolve_owners(orchestrator.state)
                    
                    status.text("Stage 3: Resolving deadlines...")
                    progress_bar.progress(50)
                    orchestrator.state = resolve_deadlines(orchestrator.state)
                    
                    status.text("Stage 4: Running validation...")
                    progress_bar.progress(66)
                    orchestrator.state = validate_state(orchestrator.state)
                    
                    status.text("Stage 5: Generating messages...")
                    progress_bar.progress(83)
                    orchestrator.state = generate_messages(orchestrator.state)
                    
                    status.text("Stage 6: Simulating emails...")
                    progress_bar.progress(95)
                    orchestrator.state = simulate_email_triggers(orchestrator.state)
                    
                    status.text("Generating final output...")
                    progress_bar.progress(100)
                    final_output = orchestrator._generate_final_output()
                    
                    st.session_state['final_output'] = final_output
                    st.session_state['processing_complete'] = True
                    
                    status.success("✓ Processing complete!")
                    
                except Exception as e:
                    st.error(f"Error processing meeting: {str(e)}")
                    st.exception(e)
    
    with tab3:
        st.header("Results")
        
        if 'processing_complete' not in st.session_state or not st.session_state['processing_complete']:
            st.info("Run the agent to see results")
            return
        
        final_output = st.session_state['final_output']
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Action Items", len(final_output.action_items))
        
        with col2:
            st.metric("Decisions", len(final_output.decisions))
        
        with col3:
            st.metric("Risks", len(final_output.risks))
        
        with col4:
            needs_review = sum(1 for a in final_output.action_items if a.needs_review)
            st.metric("Needs Review", needs_review)
        
        st.divider()
        
        # Action Items
        st.subheader("📋 Action Items")
        
        for action in final_output.action_items:
            with st.expander(f"{action.id}: {action.description}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Owner:**", action.owner_name or "Unassigned")
                    st.write("**Email:**", action.owner_email or "N/A")
                    st.write("**Role:**", action.owner_role or "N/A")
                
                with col2:
                    st.write("**Deadline Text:**", action.deadline_text or "None")
                    st.write("**Deadline Date:**", str(action.deadline_date) if action.deadline_date else "Not resolved")
                    if action.confidence:
                        st.write("**Confidence:**", f"{action.confidence:.2%}")
                
                if action.needs_review:
                    st.warning("⚠️ **Needs Review:** " + ", ".join(action.validation_notes))
                
                if action.evidence:
                    st.write("**Evidence:**")
                    for evidence in action.evidence:
                        st.text(evidence)
        
        st.divider()
        
        # Decisions
        st.subheader("✅ Decisions")
        
        for decision in final_output.decisions:
            with st.expander(f"{decision.id}: {decision.description}"):
                if decision.made_by:
                    st.write("**Made by:**", decision.made_by)
                if decision.evidence:
                    st.write("**Evidence:**")
                    for evidence in decision.evidence:
                        st.text(evidence)
        
        st.divider()
        
        # Risks
        st.subheader("⚠️ Risks & Open Questions")
        
        for risk in final_output.risks:
            with st.expander(f"{risk.id}: {risk.description}"):
                st.write("**Category:**", risk.category)
                if risk.mentioned_by:
                    st.write("**Mentioned by:**", risk.mentioned_by)
                if risk.evidence:
                    st.write("**Evidence:**")
                    for evidence in risk.evidence:
                        st.text(evidence)
        
        st.divider()
        
        # Follow-up Messages
        st.subheader("📧 Follow-up Messages")
        
        for message in final_output.follow_up_messages:
            with st.expander(f"To: {message.to_name} ({message.to_email})"):
                st.write("**Subject:**", message.subject)
                st.text_area("Body", value=message.body, height=200, disabled=True)
                st.write(f"**Action Items:** {', '.join(message.action_items)}")
        
        st.divider()
        
        # Email Triggers
        st.subheader("📤 Email Triggers (Simulated)")
        
        for trigger in final_output.email_triggers:
            st.info(f"**[{trigger.status.upper()}]** To: {trigger.to_name} <{trigger.to}> | Subject: {trigger.subject} | Triggered: {trigger.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.divider()
        
        # Download outputs
        st.subheader("💾 Download Outputs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON download
            json_output = json.dumps({
                "action_items": [a.model_dump(mode='json') for a in final_output.action_items],
                "decisions": [d.model_dump(mode='json') for d in final_output.decisions],
                "risks": [r.model_dump(mode='json') for r in final_output.risks],
                "follow_up_messages": [m.model_dump(mode='json') for m in final_output.follow_up_messages],
                "metadata": final_output.metadata
            }, indent=2, default=str)
            
            st.download_button(
                label="📥 Download JSON",
                data=json_output,
                file_name="meeting_output.json",
                mime="application/json"
            )
        
        with col2:
            # Summary download
            st.download_button(
                label="📥 Download Summary",
                data=final_output.meeting_summary,
                file_name="meeting_summary.txt",
                mime="text/plain"
            )


if __name__ == "__main__":
    main()
