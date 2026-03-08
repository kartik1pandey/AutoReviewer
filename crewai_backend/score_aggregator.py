"""
Robust Score Aggregation System
Prevents N/A scores by extracting and validating numeric scores
"""

import re
from typing import Dict, Any, Optional, List

def extract_score_from_text(text: str, score_name: str = "") -> Optional[float]:
    """
    Extract numeric score from text using multiple patterns
    
    Args:
        text: Text containing score
        score_name: Name of score to look for (e.g., "novelty", "soundness")
        
    Returns:
        Float score between 0-10, or None if not found
    """
    if not text or not isinstance(text, str):
        return None
    
    # Pattern 1: "Score: 7.5" or "Score: 7/10"
    patterns = [
        rf"{score_name}.*?score.*?(\d+\.?\d*)\s*/?\s*10",
        rf"score.*?(\d+\.?\d*)\s*/?\s*10",
        rf"{score_name}.*?(\d+\.?\d*)\s*/\s*10",
        rf"(\d+\.?\d*)\s*/\s*10",
        rf"score.*?(\d+\.?\d*)",
        rf"{score_name}.*?(\d+\.?\d*)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                score = float(match.group(1))
                # Normalize to 0-10 scale
                if score > 10:
                    score = score / 10
                if 0 <= score <= 10:
                    return round(score, 1)
            except (ValueError, IndexError):
                continue
    
    return None

def extract_all_scores(agent_reviews: Dict[str, str]) -> Dict[str, float]:
    """
    Extract scores from all agent reviews
    
    Args:
        agent_reviews: Dictionary of agent name -> review text
        
    Returns:
        Dictionary of score name -> numeric score
    """
    scores = {}
    
    # Score mappings
    score_mappings = {
        'plagiarism': ['plagiarism', 'similarity', 'originality'],
        'ai_detection': ['ai', 'detection', 'authenticity'],
        'methodology': ['methodology', 'soundness', 'method'],
        'results': ['results', 'consistency', 'experiments'],
        'formatting': ['formatting', 'format', 'compliance']
    }
    
    for agent_name, review_text in agent_reviews.items():
        if not review_text or review_text == "No review available":
            continue
        
        # Try to extract score for this agent
        search_terms = score_mappings.get(agent_name, [agent_name])
        
        for term in search_terms:
            score = extract_score_from_text(review_text, term)
            if score is not None:
                scores[agent_name] = score
                break
        
        # If no score found, try generic extraction
        if agent_name not in scores:
            score = extract_score_from_text(review_text)
            if score is not None:
                scores[agent_name] = score
    
    return scores

def calculate_weighted_score(scores: Dict[str, float]) -> float:
    """
    Calculate weighted average score
    
    Args:
        scores: Dictionary of score name -> numeric score
        
    Returns:
        Weighted average score (0-10)
    """
    if not scores:
        return 5.0  # Default neutral score
    
    # Weights for different aspects
    weights = {
        'plagiarism': 0.25,
        'ai_detection': 0.15,
        'methodology': 0.30,
        'results': 0.20,
        'formatting': 0.10
    }
    
    weighted_sum = 0
    total_weight = 0
    
    for score_name, score_value in scores.items():
        weight = weights.get(score_name, 0.2)  # Default weight
        weighted_sum += score_value * weight
        total_weight += weight
    
    if total_weight == 0:
        return sum(scores.values()) / len(scores)
    
    return round(weighted_sum / total_weight, 1)

def extract_recommendation(text: str) -> str:
    """
    Extract recommendation from text
    
    Args:
        text: Text containing recommendation
        
    Returns:
        One of: Accept, Revise, Reject, or Review
    """
    if not text or not isinstance(text, str):
        return "Review"
    
    text_lower = text.lower()
    
    # Check for explicit recommendations
    if 'accept' in text_lower and 'reject' not in text_lower:
        return "Accept"
    elif 'reject' in text_lower:
        return "Reject"
    elif 'revise' in text_lower or 'revision' in text_lower:
        return "Revise"
    elif 'resubmit' in text_lower:
        return "Revise"
    
    return "Review"

def extract_detailed_scores(agent_reviews: Dict[str, str], final_assessment: str) -> Dict[str, float]:
    """
    Extract detailed dimension scores
    
    Args:
        agent_reviews: Dictionary of agent reviews
        final_assessment: Final assessment text
        
    Returns:
        Dictionary with novelty, soundness, experiments, formatting scores
    """
    detailed = {
        'novelty': 5.0,
        'soundness': 5.0,
        'experiments': 5.0,
        'formatting': 5.0
    }
    
    # Try to extract from final assessment first
    for dimension in detailed.keys():
        score = extract_score_from_text(final_assessment, dimension)
        if score is not None:
            detailed[dimension] = score
    
    # Map agent reviews to dimensions
    if 'methodology' in agent_reviews:
        score = extract_score_from_text(agent_reviews['methodology'], 'soundness')
        if score is not None:
            detailed['soundness'] = score
    
    if 'results' in agent_reviews:
        score = extract_score_from_text(agent_reviews['results'], 'experiments')
        if score is not None:
            detailed['experiments'] = score
    
    if 'formatting' in agent_reviews:
        score = extract_score_from_text(agent_reviews['formatting'], 'format')
        if score is not None:
            detailed['formatting'] = score
    
    # Novelty from plagiarism (inverse)
    if 'plagiarism' in agent_reviews:
        score = extract_score_from_text(agent_reviews['plagiarism'])
        if score is not None:
            # High plagiarism = low novelty
            detailed['novelty'] = max(0, 10 - score)
    
    return detailed

def aggregate_scores(agent_reviews: Dict[str, str], final_assessment: str) -> Dict[str, Any]:
    """
    Main aggregation function - never returns N/A
    
    Args:
        agent_reviews: Dictionary of agent name -> review text
        final_assessment: Final assessment text
        
    Returns:
        Dictionary with overall_score, recommendation, detailed_scores, issues
    """
    # Extract all numeric scores
    extracted_scores = extract_all_scores(agent_reviews)
    
    # Calculate overall score
    overall_score = calculate_weighted_score(extracted_scores)
    
    # Extract recommendation
    recommendation = extract_recommendation(final_assessment)
    
    # If no recommendation found, infer from score
    if recommendation == "Review":
        if overall_score >= 7.5:
            recommendation = "Accept"
        elif overall_score >= 5.0:
            recommendation = "Revise"
        else:
            recommendation = "Reject"
    
    # Extract detailed scores
    detailed_scores = extract_detailed_scores(agent_reviews, final_assessment)
    
    # Extract issues
    issues = extract_issues(agent_reviews, final_assessment)
    
    return {
        'overall_score': overall_score,
        'recommendation': recommendation,
        'detailed_scores': detailed_scores,
        'issues': issues,
        'extracted_scores': extracted_scores  # For debugging
    }

def extract_issues(agent_reviews: Dict[str, str], final_assessment: str) -> List[Dict[str, str]]:
    """
    Extract issues from reviews
    
    Args:
        agent_reviews: Dictionary of agent reviews
        final_assessment: Final assessment text
        
    Returns:
        List of issues with category and description
    """
    issues = []
    
    # Keywords that indicate issues
    issue_keywords = [
        'missing', 'absent', 'lack', 'insufficient', 'weak',
        'unclear', 'poor', 'inadequate', 'limited', 'fail'
    ]
    
    # Check final assessment
    if final_assessment:
        lines = final_assessment.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in issue_keywords):
                if len(line.strip()) > 20:  # Meaningful issue
                    issues.append({
                        'category': 'General',
                        'description': line.strip()[:200]
                    })
    
    # Check agent reviews
    for agent_name, review in agent_reviews.items():
        if not review:
            continue
        
        # Look for flagged sections
        if 'flag' in review.lower() or 'issue' in review.lower():
            lines = review.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in issue_keywords):
                    if len(line.strip()) > 20:
                        issues.append({
                            'category': agent_name.replace('_', ' ').title(),
                            'description': line.strip()[:200]
                        })
    
    # Limit to top 10 issues
    return issues[:10]

def safe_aggregate(agent_reviews: Dict[str, str], final_assessment: str) -> Dict[str, Any]:
    """
    Safe wrapper with fallback
    
    Args:
        agent_reviews: Dictionary of agent reviews
        final_assessment: Final assessment text
        
    Returns:
        Aggregated scores (never fails)
    """
    try:
        return aggregate_scores(agent_reviews, final_assessment)
    except Exception as e:
        print(f"⚠️  Score aggregation error: {e}")
        # Return safe defaults
        return {
            'overall_score': 5.0,
            'recommendation': 'Review',
            'detailed_scores': {
                'novelty': 5.0,
                'soundness': 5.0,
                'experiments': 5.0,
                'formatting': 5.0
            },
            'issues': [{
                'category': 'System',
                'description': 'Score aggregation encountered an error. Manual review recommended.'
            }],
            'extracted_scores': {}
        }
