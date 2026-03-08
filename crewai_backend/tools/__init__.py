"""
Tools for CrewAI agents
"""

from .pdf_parser_tool import pdf_parser_tool
from .text_analysis_tool import text_analysis_tool
from .similarity_tool import similarity_tool
from .methodology_validator_tool import methodology_validator_tool

__all__ = [
    "pdf_parser_tool",
    "text_analysis_tool",
    "similarity_tool",
    "methodology_validator_tool"
]
