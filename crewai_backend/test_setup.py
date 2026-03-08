"""
Test script to verify CrewAI + Groq setup
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    try:
        from crewai import Agent, Task, Crew, LLM
        print("✅ CrewAI imports successful")
    except Exception as e:
        print(f"❌ CrewAI import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ dotenv import successful")
    except Exception as e:
        print(f"❌ dotenv import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from config import GROQ_API_KEY, GROQ_MODEL, LLM_CONFIG
        
        if not GROQ_API_KEY:
            print("❌ GROQ_API_KEY not set in .env file")
            return False
        
        print(f"✅ GROQ_API_KEY: {GROQ_API_KEY[:10]}...")
        print(f"✅ GROQ_MODEL: {GROQ_MODEL}")
        print(f"✅ LLM_CONFIG: {LLM_CONFIG}")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_llm():
    """Test LLM initialization"""
    print("\nTesting LLM initialization...")
    try:
        from config import GROQ_API_KEY, GROQ_MODEL
        from crewai import LLM
        
        # Set environment variable
        os.environ["GROQ_API_KEY"] = GROQ_API_KEY
        
        # Initialize LLM
        llm = LLM(
            model=f"groq/{GROQ_MODEL}",
            temperature=0.1
        )
        
        print(f"✅ LLM initialized: {llm}")
        return True
    except Exception as e:
        print(f"❌ LLM initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent():
    """Test agent creation"""
    print("\nTesting agent creation...")
    try:
        from agents import create_document_parser_agent
        
        agent = create_document_parser_agent()
        print(f"✅ Agent created: {agent.role}")
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tools():
    """Test tool imports"""
    print("\nTesting tool imports...")
    try:
        from tools.pdf_parser_tool import pdf_parser_tool
        from tools.text_analysis_tool import text_analysis_tool
        from tools.similarity_tool import similarity_tool
        from tools.methodology_validator_tool import methodology_validator_tool
        
        print(f"✅ pdf_parser_tool: {pdf_parser_tool.name}")
        print(f"✅ text_analysis_tool: {text_analysis_tool.name}")
        print(f"✅ similarity_tool: {similarity_tool.name}")
        print(f"✅ methodology_validator_tool: {methodology_validator_tool.name}")
        
        return True
    except Exception as e:
        print(f"❌ Tool import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("CrewAI + Groq Setup Test")
    print("="*70)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("LLM", test_llm),
        ("Tools", test_tools),
        ("Agent", test_agent),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("Test Results:")
    print("="*70)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready.")
        print("\nYou can now run:")
        print("  python main.py path/to/paper.pdf")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
