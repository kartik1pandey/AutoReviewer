"""
CrewAI Tasks for AutoReviewer
Defines specific tasks for each agent
"""

from crewai import Task
from config import TASK_CONFIG

def create_parsing_task(agent, pdf_path: str):
    """Task for parsing PDF"""
    return Task(
        description=f"""
        Parse the research paper PDF at: {pdf_path}
        
        Extract the following information:
        1. Paper title
        2. Abstract
        3. All major sections (introduction, methodology, experiments, results, conclusion)
        4. References/bibliography
        5. Count of figures and tables
        6. Metadata (word count, page count)
        
        Use the PDF Parser tool to extract this information.
        Return a structured summary of all extracted components.
        """,
        agent=agent,
        expected_output="Structured paper data with title, abstract, sections, references, and metadata",
        **TASK_CONFIG
    )

def create_plagiarism_detection_task(agent, paper_text: str):
    """Task for plagiarism detection"""
    return Task(
        description=f"""
        Analyze the following paper text for potential plagiarism:
        
        {paper_text[:1000]}... [truncated]
        
        Use the Similarity Analyzer tool to:
        1. Chunk the text into 500-word segments
        2. Calculate similarity scores for each chunk
        3. Flag any chunks with similarity > 0.85
        4. Report average and maximum similarity
        
        Provide a detailed plagiarism analysis report with:
        - Overall similarity assessment
        - Number of high-similarity chunks
        - Specific flagged sections
        - Recommendation (pass/fail)
        """,
        agent=agent,
        expected_output="Plagiarism analysis with similarity scores and flagged sections",
        **TASK_CONFIG
    )

def create_ai_detection_task(agent, paper_text: str):
    """Task for AI content detection"""
    return Task(
        description=f"""
        Analyze the following paper text for AI-generated content:
        
        {paper_text[:1000]}... [truncated]
        
        Use the Text Analysis tool to calculate:
        1. Perplexity (text predictability) - Low (<50) indicates AI-generated
        2. Burstiness (style variation) - Low (<0.3) indicates uniform AI style
        3. Overall AI probability score
        
        Provide a detailed AI detection report with:
        - Perplexity score and interpretation
        - Burstiness score and interpretation
        - AI probability (0-1 scale)
        - Specific indicators of AI generation
        - Final assessment (human-written/AI-generated/mixed)
        """,
        agent=agent,
        expected_output="AI detection analysis with perplexity, burstiness, and probability scores",
        **TASK_CONFIG
    )

def create_methodology_review_task(agent, methodology_text: str, experiments_text: str):
    """Task for methodology review"""
    return Task(
        description=f"""
        Review the research methodology for scientific soundness.
        
        Methodology Section:
        {methodology_text[:500]}... [truncated]
        
        Experiments Section:
        {experiments_text[:500]}... [truncated]
        
        Use the Methodology Validator tool to check for:
        1. Clear problem definition
        2. Baseline comparisons
        3. Ablation studies
        4. Dataset description
        
        Provide a detailed methodology review with:
        - Presence/absence of each required component
        - Quality assessment of methodology
        - Missing elements
        - Score (0-10)
        - Recommendations for improvement
        """,
        agent=agent,
        expected_output="Methodology review with component checklist and quality score",
        **TASK_CONFIG
    )

def create_results_validation_task(agent, results_text: str, has_tables: bool, has_figures: bool):
    """Task for results validation"""
    return Task(
        description=f"""
        Validate the results section for consistency and evidence.
        
        Results Section:
        {results_text[:500]}... [truncated]
        
        Tables present: {has_tables}
        Figures present: {has_figures}
        
        Analyze:
        1. Extract all numeric claims (percentages, metrics)
        2. Check if claims are supported by tables/figures
        3. Identify any unsupported claims
        4. Check for repeated or suspicious metrics
        
        Provide a results validation report with:
        - List of numeric claims
        - Evidence support assessment
        - Consistency score (0-10)
        - Flagged issues
        - Recommendations
        """,
        agent=agent,
        expected_output="Results validation with claims analysis and consistency score",
        **TASK_CONFIG
    )

def create_formatting_check_task(agent, paper_data: dict):
    """Task for formatting compliance"""
    return Task(
        description=f"""
        Check the paper for formatting compliance with conference standards.
        
        Paper Data:
        - Title: {paper_data.get('title', 'N/A')}
        - Abstract length: {len(paper_data.get('abstract', ''))} characters
        - Sections: {list(paper_data.get('sections', {}).keys())}
        - References: {len(paper_data.get('references', []))} citations
        - Figures: {paper_data.get('figures_count', 0)}
        - Tables: {paper_data.get('tables_count', 0)}
        
        Check compliance with:
        1. Title length ≥ 10 characters
        2. Abstract length ≥ 100 characters
        3. References ≥ 5 citations
        4. Required sections: introduction, method, experiments, conclusion
        
        Provide a formatting compliance report with:
        - Pass/fail for each requirement
        - Missing sections
        - Compliance score (0-10)
        - Specific violations
        """,
        agent=agent,
        expected_output="Formatting compliance report with pass/fail checklist",
        **TASK_CONFIG
    )

def create_aggregation_task(agent, all_reviews: dict):
    """Task for aggregating all reviews"""
    return Task(
        description=f"""
        Synthesize all agent reviews into a comprehensive final assessment.
        
        Review Data:
        {str(all_reviews)[:1000]}... [truncated]
        
        Aggregate:
        1. Calculate overall score (average of all agent scores)
        2. Collect all issues from all agents
        3. Estimate novelty score based on introduction
        4. Generate final recommendation:
           - Accept: score ≥ 7.5
           - Revise: score ≥ 5.0
           - Reject: score < 5.0
        
        Provide a comprehensive final review with:
        - Overall score (0-10)
        - Recommendation (Accept/Revise/Reject)
        - Detailed scores by dimension (novelty, soundness, experiments, formatting)
        - Complete list of issues
        - Summary of strengths and weaknesses
        - Actionable feedback for authors
        """,
        agent=agent,
        expected_output="Comprehensive final review with overall score and recommendation",
        **TASK_CONFIG
    )
