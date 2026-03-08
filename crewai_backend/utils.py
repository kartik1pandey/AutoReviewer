"""
Utility functions for CrewAI AutoReviewer
Handles text truncation and rate limiting
"""

import time
from functools import wraps
from typing import Dict, Any

# Token estimation: ~4 characters per token (conservative estimate)
CHARS_PER_TOKEN = 4

# Groq free tier limits
GROQ_FREE_TIER_TPM = 12000  # Tokens per minute
GROQ_SAFE_TOKENS_PER_REQUEST = 3000  # Safe limit per request (leave room for response)

def estimate_tokens(text: str) -> int:
    """
    Estimate number of tokens in text
    Conservative estimate: 1 token ≈ 4 characters
    """
    return len(text) // CHARS_PER_TOKEN

def truncate_text(text: str, max_tokens: int = GROQ_SAFE_TOKENS_PER_REQUEST, 
                  preserve_start: bool = True) -> str:
    """
    Truncate text to fit within token limit
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        preserve_start: If True, keep beginning; if False, keep end
        
    Returns:
        Truncated text with indicator
    """
    if not text:
        return ""
    
    estimated_tokens = estimate_tokens(text)
    
    if estimated_tokens <= max_tokens:
        return text
    
    # Calculate max characters
    max_chars = max_tokens * CHARS_PER_TOKEN
    
    if preserve_start:
        truncated = text[:max_chars]
        return truncated + "\n\n[... Text truncated for token limit ...]"
    else:
        truncated = text[-max_chars:]
        return "[... Text truncated for token limit ...]\n\n" + truncated

def smart_truncate_sections(sections: Dict[str, str], 
                            max_total_tokens: int = GROQ_SAFE_TOKENS_PER_REQUEST) -> Dict[str, str]:
    """
    Intelligently truncate paper sections to fit within token limit
    Prioritizes important sections
    
    Args:
        sections: Dictionary of section_name -> content
        max_total_tokens: Maximum total tokens across all sections
        
    Returns:
        Truncated sections dictionary
    """
    if not sections:
        return {}
    
    # Priority order for sections (most important first)
    priority_order = [
        'abstract',
        'introduction',
        'conclusion',
        'methodology',
        'method',
        'experiments',
        'results',
        'discussion',
        'related work'
    ]
    
    # Calculate current total tokens
    total_tokens = sum(estimate_tokens(content) for content in sections.values())
    
    if total_tokens <= max_total_tokens:
        return sections
    
    # Allocate tokens proportionally with priority weighting
    truncated_sections = {}
    remaining_tokens = max_total_tokens
    
    # Sort sections by priority
    sorted_sections = []
    for priority_key in priority_order:
        for section_key, content in sections.items():
            if priority_key in section_key.lower() and section_key not in [s[0] for s in sorted_sections]:
                sorted_sections.append((section_key, content))
                break
    
    # Add remaining sections
    for section_key, content in sections.items():
        if section_key not in [s[0] for s in sorted_sections]:
            sorted_sections.append((section_key, content))
    
    # Allocate tokens with priority weighting
    for i, (section_key, content) in enumerate(sorted_sections):
        # Higher priority sections get more tokens
        weight = 1.0 / (i + 1)  # Decreasing weight
        section_tokens = estimate_tokens(content)
        
        # Allocate proportional tokens
        allocated_tokens = min(
            int(remaining_tokens * weight / sum(1.0/(j+1) for j in range(i, len(sorted_sections)))),
            section_tokens
        )
        
        if allocated_tokens > 0:
            truncated_sections[section_key] = truncate_text(content, allocated_tokens)
            remaining_tokens -= allocated_tokens
        
        if remaining_tokens <= 0:
            break
    
    return truncated_sections

def create_paper_summary(paper_data: Dict[str, Any], 
                        max_tokens: int = GROQ_SAFE_TOKENS_PER_REQUEST) -> str:
    """
    Create a concise summary of paper for analysis
    
    Args:
        paper_data: Parsed paper data
        max_tokens: Maximum tokens for summary
        
    Returns:
        Formatted paper summary
    """
    summary_parts = []
    
    # Title (always include)
    title = paper_data.get('title', 'Unknown Title')
    summary_parts.append(f"Title: {title}")
    
    # Abstract (high priority)
    abstract = paper_data.get('abstract', '')
    if abstract:
        abstract_truncated = truncate_text(abstract, max_tokens // 3)
        summary_parts.append(f"\nAbstract:\n{abstract_truncated}")
    
    # Key sections (truncated)
    sections = paper_data.get('sections', {})
    if sections:
        remaining_tokens = max_tokens - estimate_tokens('\n'.join(summary_parts))
        truncated_sections = smart_truncate_sections(sections, remaining_tokens)
        
        for section_name, content in truncated_sections.items():
            summary_parts.append(f"\n{section_name.title()}:\n{content}")
    
    # Metadata
    metadata = []
    if paper_data.get('figures_count', 0) > 0:
        metadata.append(f"Figures: {paper_data['figures_count']}")
    if paper_data.get('tables_count', 0) > 0:
        metadata.append(f"Tables: {paper_data['tables_count']}")
    if paper_data.get('references'):
        metadata.append(f"References: {len(paper_data['references'])}")
    
    if metadata:
        summary_parts.append(f"\nMetadata: {', '.join(metadata)}")
    
    return '\n'.join(summary_parts)

def rate_limit_delay(delay_seconds: float = 5.0):
    """
    Decorator to add delay between function calls for rate limiting
    
    Args:
        delay_seconds: Seconds to wait between calls
    """
    def decorator(func):
        last_call_time = [0]  # Use list to make it mutable in closure
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Calculate time since last call
            current_time = time.time()
            time_since_last_call = current_time - last_call_time[0]
            
            # Wait if needed
            if time_since_last_call < delay_seconds:
                wait_time = delay_seconds - time_since_last_call
                print(f"⏳ Rate limiting: waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            
            # Update last call time
            last_call_time[0] = time.time()
            
            # Call function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def chunk_text_for_analysis(text: str, chunk_size_tokens: int = 2000, 
                            overlap_tokens: int = 200) -> list:
    """
    Split text into overlapping chunks for analysis
    
    Args:
        text: Text to chunk
        chunk_size_tokens: Size of each chunk in tokens
        overlap_tokens: Overlap between chunks in tokens
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunk_size_chars = chunk_size_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size_chars
        chunk = text[start:end]
        
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap_chars
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    return chunks

def format_token_info(text: str) -> str:
    """
    Get formatted token information for text
    
    Args:
        text: Text to analyze
        
    Returns:
        Formatted string with token info
    """
    tokens = estimate_tokens(text)
    chars = len(text)
    return f"{tokens:,} tokens (~{chars:,} chars)"
