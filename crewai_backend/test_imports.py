"""
Test script to verify all imports work correctly
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")
print("="*50)

try:
    print("✓ Importing config...")
    from config import GROQ_API_KEY, LLM_CONFIG, AGENT_CONFIG
    print(f"  Model: {LLM_CONFIG['model']}")
    
    print("✓ Importing tools...")
    from tools.pdf_parser_tool import pdf_parser_tool
    from tools.text_analysis_tool import text_analysis_tool
    from tools.similarity_tool import similarity_tool
    from tools.methodology_validator_tool import methodology_validator_tool
    
    print("✓ Importing agents...")
    from agents import (
        create_document_parser_agent,
        create_plagiarism_detector_agent,
        create_ai_content_detector_agent,
        create_methodology_reviewer_agent,
        create_results_validator_agent,
        create_formatting_checker_agent,
        create_review_aggregator_agent
    )
    
    print("✓ Importing tasks...")
    from tasks import (
        create_parsing_task,
        create_plagiarism_detection_task,
        create_ai_detection_task,
        create_methodology_review_task,
        create_results_validation_task,
        create_formatting_check_task,
        create_aggregation_task
    )
    
    print("✓ Importing crew_system...")
    from crew_system import CrewAIReviewerSystem
    
    print("\n" + "="*50)
    print("✅ All imports successful!")
    print("="*50)
    
    # Test tool instantiation
    print("\nTesting tool instantiation...")
    print("✅ Tools are functions (decorated with @tool)")
    print(f"  pdf_parser_tool: {type(pdf_parser_tool)}")
    print(f"  text_analysis_tool: {type(text_analysis_tool)}")
    print(f"  similarity_tool: {type(similarity_tool)}")
    print(f"  methodology_validator_tool: {type(methodology_validator_tool)}")
    print("✅ All tools loaded successfully!")
    
    print("\n" + "="*50)
    print("🎉 Setup is working correctly!")
    print("="*50)
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
