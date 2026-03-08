"""
CrewAI Agents for AutoReviewer
Each agent specializes in a specific review aspect
"""

import os
from crewai import Agent, LLM
from config import GROQ_API_KEY, LLM_CONFIG, AGENT_CONFIG
from tools.pdf_parser_tool import pdf_parser_tool
from tools.text_analysis_tool import text_analysis_tool
from tools.similarity_tool import similarity_tool
from tools.methodology_validator_tool import methodology_validator_tool

# Set Groq API key in environment
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Initialize LLM using CrewAI's native LLM class with Groq
llm = LLM(
    model=f"groq/{LLM_CONFIG['model']}",
    temperature=LLM_CONFIG["temperature"]
)

def create_document_parser_agent():
    """Agent for parsing and extracting paper structure"""
    return Agent(
        role="Document Parser Specialist",
        goal="Extract and structure information from research paper PDFs",
        backstory=(
            "You are an expert in document analysis and information extraction. "
            "Your specialty is parsing academic papers and extracting key components "
            "like title, abstract, sections, and references with high accuracy."
        ),
        tools=[pdf_parser_tool],
        llm=llm,
        **AGENT_CONFIG
    )

def create_plagiarism_detector_agent():
    """Agent for detecting plagiarism and similarity"""
    return Agent(
        role="Plagiarism Detection Expert",
        goal="Detect potential plagiarism and text similarity in research papers",
        backstory=(
            "You are a plagiarism detection specialist with expertise in text similarity analysis. "
            "You use advanced chunking and similarity algorithms to identify copied content. "
            "You flag any text with similarity above 85% as potentially plagiarized."
        ),
        tools=[similarity_tool],
        llm=llm,
        **AGENT_CONFIG
    )

def create_ai_content_detector_agent():
    """Agent for detecting AI-generated content"""
    return Agent(
        role="AI Content Detection Specialist",
        goal="Identify AI-generated text using perplexity and burstiness analysis",
        backstory=(
            "You are an AI content detection expert specializing in identifying machine-generated text. "
            "You use perplexity (text predictability) and burstiness (style variation) metrics. "
            "Low perplexity (<50) and low burstiness (<0.3) indicate AI-generated content. "
            "You provide detailed analysis with probability scores."
        ),
        tools=[text_analysis_tool],
        llm=llm,
        **AGENT_CONFIG
    )

def create_methodology_reviewer_agent():
    """Agent for reviewing research methodology"""
    return Agent(
        role="Methodology Review Expert",
        goal="Evaluate research methodology for scientific soundness and completeness",
        backstory=(
            "You are a senior researcher with expertise in experimental design and methodology. "
            "You evaluate papers based on: problem definition, baseline comparisons, "
            "ablation studies, and dataset description. You ensure research meets "
            "conference standards (NeurIPS, ICML, ACL)."
        ),
        tools=[methodology_validator_tool],
        llm=llm,
        **AGENT_CONFIG
    )

def create_results_validator_agent():
    """Agent for validating results and claims"""
    return Agent(
        role="Results Validation Specialist",
        goal="Verify consistency between claims and experimental results",
        backstory=(
            "You are an expert in experimental validation and results analysis. "
            "You check if claims are supported by evidence (tables, figures). "
            "You extract numeric claims and verify they match reported results. "
            "You flag any inconsistencies or unsupported claims."
        ),
        tools=[text_analysis_tool],  # Can analyze results text
        llm=llm,
        **AGENT_CONFIG
    )

def create_formatting_checker_agent():
    """Agent for checking formatting compliance"""
    return Agent(
        role="Formatting Compliance Officer",
        goal="Ensure paper meets conference formatting standards",
        backstory=(
            "You are a conference submission specialist who ensures papers meet "
            "formatting requirements. You check: title length (≥10 chars), "
            "abstract length (≥100 chars), reference count (≥5), and required sections "
            "(introduction, method, experiments, conclusion)."
        ),
        tools=[],  # Uses parsed data directly
        llm=llm,
        **AGENT_CONFIG
    )

def create_review_aggregator_agent():
    """Agent for aggregating all reviews"""
    return Agent(
        role="Senior Review Coordinator",
        goal="Synthesize all agent reviews into a comprehensive final assessment",
        backstory=(
            "You are a senior conference reviewer who coordinates and synthesizes "
            "multiple review perspectives. You aggregate scores, collect issues, "
            "estimate novelty, and generate final recommendations (Accept/Revise/Reject). "
            "Accept: score ≥7.5, Revise: score ≥5.0, Reject: score <5.0."
        ),
        tools=[],  # Synthesizes other agents' outputs
        llm=llm,
        verbose=True,
        allow_delegation=True,  # Can delegate to other agents
        max_iter=10
    )
