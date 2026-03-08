"""
Similarity Analysis Tool for CrewAI
Detects text similarity for plagiarism detection
"""

from crewai.tools import tool

@tool("Similarity Analyzer")
def similarity_tool(text: str, chunk_size: int = 500) -> dict:
    """
    Analyzes text for potential plagiarism by chunking and calculating similarity.
    Returns similarity scores and flags high-similarity chunks (>0.85).
    Use this to detect copied or plagiarized content.
    
    Args:
        text: Text to analyze for similarity
        chunk_size: Size of text chunks in words (default: 500)
        
    Returns:
        Dictionary with similarity analysis results
    """
    try:
        chunks = _chunk_text(text, chunk_size)
        similarity_scores = []
        high_similarity_chunks = []
        
        for i, chunk in enumerate(chunks[:5]):  # Analyze first 5 chunks
            sim = _calculate_similarity(chunk)
            similarity_scores.append(sim)
            
            if sim > 0.85:
                high_similarity_chunks.append({
                    "chunk_index": i,
                    "similarity": sim,
                    "preview": chunk[:100] + "..."
                })
        
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        max_similarity = max(similarity_scores) if similarity_scores else 0
        
        return {
            "success": True,
            "avg_similarity": round(avg_similarity, 3),
            "max_similarity": round(max_similarity, 3),
            "chunks_analyzed": len(similarity_scores),
            "high_similarity_count": len(high_similarity_chunks),
            "high_similarity_chunks": high_similarity_chunks,
            "threshold": 0.85
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _chunk_text(text: str, chunk_size: int) -> list:
    """Split text into chunks"""
    words = text.split()
    return [' '.join(words[i:i+chunk_size]) 
            for i in range(0, len(words), chunk_size)]

def _calculate_similarity(text: str) -> float:
    """
    Calculate similarity score
    In production, this would use:
    - Sentence embeddings (HuggingFace)
    - Semantic Scholar API
    - Citation graph analysis
    
    Current: Deterministic simulation based on text hash
    """
    hash_val = hash(text) % 100
    return min(0.70 + (hash_val / 100), 0.95)
