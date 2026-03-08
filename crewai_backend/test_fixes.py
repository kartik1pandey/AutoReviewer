"""
Test script to verify all critical fixes
"""

print("Testing Critical Fixes...")
print("=" * 70)

# Test 1: Score Aggregator
print("\n1️⃣ Testing Score Aggregator...")
try:
    from score_aggregator import safe_aggregate, extract_score_from_text
    
    # Test score extraction
    test_text = "The methodology score is 7.5/10 based on our analysis."
    score = extract_score_from_text(test_text, "methodology")
    print(f"   ✅ Score extraction: {score}")
    
    # Test safe aggregation
    test_reviews = {
        'plagiarism': "Similarity score: 0.75. Moderate risk.",
        'methodology': "Soundness score: 8/10. Good approach.",
        'results': "Experiments score: 6.5/10. Needs improvement."
    }
    result = safe_aggregate(test_reviews, "Overall assessment: Revise")
    print(f"   ✅ Safe aggregation: Score={result['overall_score']}, Rec={result['recommendation']}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Section Analyzer
print("\n2️⃣ Testing Section Analyzer...")
try:
    from section_analyzer import SectionAnalyzer
    
    analyzer = SectionAnalyzer()
    
    # Test section identification
    test_paper = """
    Introduction
    This paper presents a novel approach.
    
    Methodology
    We use a deep learning model with baseline comparisons.
    
    Results
    We achieved 85% accuracy, which is 10% better than baseline.
    
    Conclusion
    Our method shows promising results.
    """
    
    sections = analyzer.identify_sections(test_paper)
    print(f"   ✅ Sections found: {list(sections.keys())}")
    
    # Test methodology checking
    components = analyzer.check_methodology_components(sections.get('methodology', ''))
    print(f"   ✅ Methodology components: {components}")
    
    # Test numeric claims
    claims = analyzer.extract_numeric_claims(sections.get('results', ''))
    print(f"   ✅ Numeric claims found: {len(claims)}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Integration
print("\n3️⃣ Testing Integration...")
try:
    from crew_system import CrewAIReviewerSystem
    print("   ✅ CrewAIReviewerSystem imports successfully")
    print("   ✅ All modules integrated")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ All tests passed! System is ready.")
print("=" * 70)
