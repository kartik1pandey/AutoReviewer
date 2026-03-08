"""
Main entry point for CrewAI AutoReviewer
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crew_system import CrewAIReviewerSystem

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_paper.pdf>")
        print("\nExample: python main.py sample_paper.pdf")
        print("\nMake sure to set GROQ_API_KEY environment variable!")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export GROQ_API_KEY='your-api-key-here'  # Linux/Mac")
        print("  set GROQ_API_KEY=your-api-key-here       # Windows")
        sys.exit(1)
    
    try:
        # Initialize system
        system = CrewAIReviewerSystem()
        
        # Review paper
        report = system.review_paper(pdf_path)
        
        # Print report
        system.print_report(report)
        
        # Save report
        output_file = pdf_path.replace('.pdf', '_crewai_review.json')
        system.save_report(report, output_file)
        
    except Exception as e:
        print(f"❌ Error during review: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
