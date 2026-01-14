"""
Quick test script to verify the agent works
Run this after setting up your API key to test the system
"""
import os
import sys

def test_configuration():
    """Test that configuration is valid"""
    print("Testing configuration...")
    try:
        import config
        config.validate_config()
        print("✓ Configuration valid")
        print(f"  - Model: {config.OPENROUTER_MODEL}")
        print(f"  - Reference Date: {config.REFERENCE_DATE}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_imports():
    """Test that all modules can be imported"""
    print("\nTesting imports...")
    modules = [
        "models",
        "orchestrator",
        "stages.stage1_extraction",
        "stages.stage2_owner_resolution",
        "stages.stage3_deadline_resolution",
        "stages.stage4_validation_agent",
        "stages.stage5_message_generator",
        "stages.stage6_email_simulator"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            return False
    
    return True


def test_data_files():
    """Test that required data files exist"""
    print("\nTesting data files...")
    files = [
        "data/people.json",
        "data/sprint_planning.txt",
        "data/product_sync.txt",
        "data/incident_review.txt"
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} not found")
            all_exist = False
    
    return all_exist


def run_quick_test():
    """Run a quick end-to-end test"""
    print("\nRunning quick end-to-end test...")
    print("(This will use a small amount of your API credits)")
    
    response = input("Proceed? (y/n): ")
    if response.lower() != 'y':
        print("Test skipped")
        return True
    
    try:
        from orchestrator import run_agent
        
        print("\nProcessing sprint_planning.txt...")
        result = run_agent(
            transcript_path="data/sprint_planning.txt",
            people_path="data/people.json"
        )
        
        print("\n" + "=" * 60)
        print("TEST RESULTS:")
        print("=" * 60)
        print(f"✓ Action Items: {len(result.action_items)}")
        print(f"✓ Decisions: {len(result.decisions)}")
        print(f"✓ Risks: {len(result.risks)}")
        print(f"✓ Follow-up Messages: {len(result.follow_up_messages)}")
        print(f"✓ Email Triggers: {len(result.email_triggers)}")
        
        print("\nOutputs saved to outputs/ directory")
        print("✓ All tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("AI MEETING AGENT - SYSTEM TEST")
    print("=" * 60)
    
    # Run tests
    config_ok = test_configuration()
    if not config_ok:
        print("\n⚠️  Please fix configuration errors before proceeding")
        print("   Update your .env file with a valid OPENAI_API_KEY")
        sys.exit(1)
    
    imports_ok = test_imports()
    if not imports_ok:
        print("\n⚠️  Please fix import errors")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)
    
    data_ok = test_data_files()
    if not data_ok:
        print("\n⚠️  Some data files are missing")
        print("   But the system can still work with custom inputs")
    
    # Optional end-to-end test
    print("\n" + "=" * 60)
    run_quick_test()


if __name__ == "__main__":
    main()
