"""
PDF Parser Tool for CrewAI
Extracts structured information from PDF papers
"""

from crewai.tools import tool
import PyPDF2
import re
from collections import Counter

@tool("PDF Parser")
def pdf_parser_tool(pdf_path: str) -> dict:
    """
    Extracts structured information from research paper PDFs.
    Returns title, abstract, sections (truncated), references, and metadata.
    Use this tool first to analyze any paper.
    
    Args:
        pdf_path: Path to the PDF file to parse
        
    Returns:
        Dictionary with extracted paper data (sections are truncated to 500 chars each)
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        
        # Extract components
        title = _extract_title(text)
        abstract = _extract_section(text, "abstract")
        sections = _extract_all_sections(text)
        references = _extract_references(text)
        figures_count = text.lower().count("figure")
        tables_count = text.lower().count("table")
        
        # Truncate sections to reduce token usage
        truncated_sections = {}
        for section_name, content in sections.items():
            if len(content) > 500:
                truncated_sections[section_name] = content[:500] + "... [truncated]"
            else:
                truncated_sections[section_name] = content
        
        # Truncate abstract if too long
        if len(abstract) > 500:
            abstract = abstract[:500] + "... [truncated]"
        
        return {
            "success": True,
            "title": title,
            "abstract": abstract,
            "sections": truncated_sections,
            "references": references[:10],  # Only first 10 references
            "figures_count": figures_count,
            "tables_count": tables_count,
            "word_count": len(text.split()),
            "page_count": len(reader.pages)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _extract_title(text: str) -> str:
    """Extract paper title"""
    lines = text.split('\n')
    for line in lines[:10]:
        if 10 < len(line.strip()) < 200:
            return line.strip()
    return "Unknown Title"

def _extract_section(text: str, section_name: str) -> str:
    """Extract specific section"""
    pattern = rf"{section_name}[\s\n]+(.*?)(?=\n[A-Z][a-z]+\n|\Z)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""

def _extract_all_sections(text: str) -> dict:
    """Extract all major sections"""
    sections = {}
    section_names = [
        "introduction", "related work", "methodology", "method",
        "experiments", "results", "discussion", "conclusion"
    ]
    for section in section_names:
        content = _extract_section(text, section)
        if content:
            sections[section] = content
    return sections

def _extract_references(text: str) -> list:
    """Extract bibliography"""
    # Try multiple patterns for references
    ref_patterns = [
        r'REFERENCES\n(.*?)(?=\n[A-Z][A-Z\s]+\n|\Z)',  # All caps REFERENCES
        r'References\n(.*?)(?=\n[A-Z][A-Z\s]+\n|\Z)',  # Title case References
        r'Bibliography\n(.*?)(?=\n[A-Z][A-Z\s]+\n|\Z)',  # Bibliography
    ]
    
    ref_section = ""
    for pattern in ref_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            ref_section = match.group(1)
            break
    
    if not ref_section:
        # Fallback: look for numbered references at the end
        lines = text.split('\n')
        ref_start = -1
        for i, line in enumerate(lines):
            if re.match(r'^\s*(REFERENCES|References|Bibliography)\s*$', line, re.IGNORECASE):
                ref_start = i
                break
        
        if ref_start > 0:
            ref_section = '\n'.join(lines[ref_start+1:ref_start+100])  # Get next 100 lines
    
    if not ref_section:
        return ["References not found in standard format"]
    
    # Extract individual references
    refs = []
    # Try to find author-year style references
    ref_matches = re.findall(r'([A-Z][a-z]+.*?\d{4}[a-z]?\.)', ref_section)
    if ref_matches:
        refs = ref_matches[:10]
    else:
        # Fallback: split by newlines and take non-empty lines
        refs = [line.strip() for line in ref_section.split('\n') if line.strip() and len(line.strip()) > 20][:10]
    
    return refs if refs else ["References extracted: see full paper"]
