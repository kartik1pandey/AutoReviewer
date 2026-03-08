"""
Text Analysis Tool for CrewAI
Calculates perplexity, burstiness, and other text metrics
"""

from crewai.tools import tool
import re
import math
from collections import Counter

@tool("Text Analysis")
def text_analysis_tool(text: str, analysis_type: str = "all") -> dict:
    """
    Analyzes text for AI-generated content detection.
    Calculates perplexity (text predictability) and burstiness (style variation).
    Lower perplexity and burstiness indicate AI-generated text.
    
    Args:
        text: Text to analyze
        analysis_type: Type of analysis - 'perplexity', 'burstiness', or 'all'
        
    Returns:
        Dictionary with analysis results
    """
    try:
        results = {}
        
        if analysis_type in ["perplexity", "all"]:
            results["perplexity"] = _calculate_perplexity(text)
        
        if analysis_type in ["burstiness", "all"]:
            results["burstiness"] = _calculate_burstiness(text)
        
        if analysis_type == "all":
            results["word_count"] = len(text.split())
            results["sentence_count"] = len(re.split(r'[.!?]+', text))
            results["avg_word_length"] = sum(len(w) for w in text.split()) / max(len(text.split()), 1)
        
        results["success"] = True
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _calculate_perplexity(text: str) -> float:
    """
    Calculate perplexity using Shannon entropy
    Formula: Perplexity = 2^entropy
    """
    words = text.lower().split()
    if len(words) < 2:
        return 100.0
    
    word_freq = Counter(words)
    total = len(words)
    
    # Calculate entropy: H = -Σ(p * log2(p))
    entropy = -sum((count/total) * math.log2(count/total) 
                  for count in word_freq.values())
    
    # Perplexity = 2^entropy
    return round(2 ** entropy, 2)

def _calculate_burstiness(text: str) -> float:
    """
    Calculate burstiness (sentence length variation)
    Formula: Burstiness = variance / (mean + 1)
    """
    sentences = re.split(r'[.!?]+', text)
    lengths = [len(s.split()) for s in sentences if s.strip()]
    
    if len(lengths) < 2:
        return 0.5
    
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    
    return round(variance / (mean_len + 1), 3)
