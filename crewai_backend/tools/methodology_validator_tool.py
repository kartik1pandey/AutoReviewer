"""
Methodology Validator Tool for CrewAI
Validates research methodology and experimental design
"""

from crewai.tools import tool

@tool("Methodology Validator")
def methodology_validator_tool(methodology_text: str, experiments_text: str) -> dict:
    """
    Validates research methodology for scientific soundness.
    Checks for: problem definition, baseline comparisons, ablation studies, dataset description.
    Returns validation results and missing components.
    
    Args:
        methodology_text: Methodology section text
        experiments_text: Experiments section text
        
    Returns:
        Dictionary with validation results
    """
    try:
        combined_text = methodology_text + " " + experiments_text
        
        # Check required components
        has_problem = _check_keywords(
            methodology_text,
            ['problem', 'task', 'objective', 'goal']
        )
        
        has_baselines = _check_keywords(
            experiments_text,
            ['baseline', 'comparison', 'compared', 'versus']
        )
        
        has_ablation = _check_keywords(
            experiments_text,
            ['ablation', 'ablation study', 'component analysis']
        )
        
        has_dataset = _check_keywords(
            combined_text,
            ['dataset', 'data', 'corpus', 'benchmark']
        )
        
        # Calculate score
        score = 10.0
        missing_components = []
        
        if not has_problem:
            missing_components.append("problem definition")
            score -= 2.0
        
        if not has_baselines:
            missing_components.append("baseline comparisons")
            score -= 2.5
        
        if not has_ablation:
            missing_components.append("ablation study")
            score -= 2.0
        
        if not has_dataset:
            missing_components.append("dataset description")
            score -= 1.5
        
        return {
            "success": True,
            "score": max(0, score),
            "has_problem_definition": has_problem,
            "has_baselines": has_baselines,
            "has_ablation": has_ablation,
            "has_dataset": has_dataset,
            "missing_components": missing_components,
            "is_sound": score >= 7.0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _check_keywords(text: str, keywords: list) -> bool:
    """Check if any keyword exists in text"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)
