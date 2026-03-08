"""
CrewAI-based AutoReviewer System
Multi-agent paper review using CrewAI and Groq
"""

from crewai import Crew, Process
import json
import time
import re
from datetime import datetime
import PyPDF2
from agents import (
    create_document_parser_agent,
    create_plagiarism_detector_agent,
    create_ai_content_detector_agent,
    create_methodology_reviewer_agent,
    create_results_validator_agent,
    create_formatting_checker_agent,
    create_review_aggregator_agent
)
from tasks import (
    create_parsing_task,
    create_plagiarism_detection_task,
    create_ai_detection_task,
    create_methodology_review_task,
    create_results_validation_task,
    create_formatting_check_task,
    create_aggregation_task
)
from utils import (
    truncate_text,
    smart_truncate_sections,
    create_paper_summary,
    estimate_tokens,
    format_token_info
)
from score_aggregator import safe_aggregate
from section_analyzer import SectionAnalyzer
from rate_limiter import get_rate_limiter

class CrewAIReviewerSystem:
    """
    CrewAI-based paper review system
    Uses multiple specialized agents with Groq LLM
    """
    
    def __init__(self):
        """Initialize all agents"""
        print("🤖 Initializing CrewAI AutoReviewer System...")
        
        self.parser_agent = create_document_parser_agent()
        self.plagiarism_agent = create_plagiarism_detector_agent()
        self.ai_detector_agent = create_ai_content_detector_agent()
        self.methodology_agent = create_methodology_reviewer_agent()
        self.results_agent = create_results_validator_agent()
        self.formatting_agent = create_formatting_checker_agent()
        self.aggregator_agent = create_review_aggregator_agent()
        
        # Initialize rate limiter
        self.rate_limiter = get_rate_limiter()
        
        print("✅ All agents initialized")
        print("✅ Rate limiter active")
    
    def _generate_fallback_review(self, agent_name: str, error_msg: str) -> str:
        """Generate fallback review when agent fails"""
        fallbacks = {
            'plagiarism': """
**Plagiarism Analysis (Fallback)**

Due to rate limiting, automated plagiarism detection could not be completed.

**Manual Review Recommended:**
- Check for proper citations
- Verify originality of key claims
- Compare with similar papers in the field

**Score:** 7.0/10 (Default - requires manual verification)
""",
            'ai_detection': """
**AI Content Detection (Fallback)**

Due to rate limiting, automated AI detection could not be completed.

**Manual Review Recommended:**
- Check writing style consistency
- Verify technical depth
- Look for unusual patterns

**Score:** 7.0/10 (Default - requires manual verification)
""",
            'methodology': """
**Methodology Review (Fallback)**

Due to rate limiting, automated methodology review could not be completed.

**Manual Review Recommended:**
- Verify problem definition is clear
- Check for baseline comparisons
- Ensure dataset is well-described
- Look for ablation studies

**Score:** 7.0/10 (Default - requires manual verification)
""",
            'results': """
**Results Validation (Fallback)**

Due to rate limiting, automated results validation could not be completed.

**Manual Review Recommended:**
- Verify all numeric claims are supported
- Check for statistical significance
- Ensure tables/figures support claims
- Look for reproducibility information

**Score:** 7.0/10 (Default - requires manual verification)
""",
            'formatting': """
**Formatting Compliance (Fallback)**

Due to rate limiting, automated formatting check could not be completed.

**Manual Review Recommended:**
- Check section structure
- Verify reference format
- Ensure figures/tables are properly labeled
- Check for required sections

**Score:** 7.0/10 (Default - requires manual verification)
"""
        }
        
        return fallbacks.get(agent_name, f"Review unavailable due to: {error_msg[:100]}")
    
    def review_paper(self, pdf_path: str) -> dict:
        """
        Review a research paper using CrewAI agents
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Comprehensive review report
        """
        print(f"\n📄 Starting review of: {pdf_path}")
        print("="*70)
        
        # Stage 1: Parse PDF directly (no agent needed)
        print("\n🔍 Stage 1: Parsing PDF with PyPDF2...")
        paper_data = self._parse_pdf_directly(pdf_path)
        print(f"✅ Parsed: {paper_data.get('title', 'Unknown')}")
        print(f"   Abstract: {len(paper_data.get('abstract', ''))} chars")
        print(f"   Sections: {len(paper_data.get('sections', {}))} found")
        print(f"   References: {len(paper_data.get('references', []))} found")
        
        # Stage 2: Parallel Analysis with truncated text
        print("\n🔍 Stage 2: Running specialized agents...")
        
        # Prepare truncated text for analysis
        abstract = paper_data.get('abstract', '')
        sections = paper_data.get('sections', {})
        
        # Truncate sections intelligently
        truncated_sections = smart_truncate_sections(sections, max_total_tokens=2000)
        
        # Create concise full text for analysis
        full_text_parts = []
        if abstract:
            full_text_parts.append(truncate_text(abstract, max_tokens=500))
        
        for section_name, content in truncated_sections.items():
            full_text_parts.append(f"{section_name}: {content[:1000]}")  # Limit each section
        
        full_text = "\n\n".join(full_text_parts)
        
        print(f"📊 Text prepared: {format_token_info(full_text)}")
        
        # Create all analysis tasks with truncated text
        tasks = []
        
        # Plagiarism detection
        print("  → Plagiarism detection...")
        plagiarism_text = truncate_text(full_text, max_tokens=1500)
        plagiarism_task = create_plagiarism_detection_task(
            self.plagiarism_agent,
            plagiarism_text
        )
        tasks.append(plagiarism_task)
        
        # AI content detection
        print("  → AI content detection...")
        ai_detection_text = truncate_text(full_text, max_tokens=1500)
        ai_detection_task = create_ai_detection_task(
            self.ai_detector_agent,
            ai_detection_text
        )
        tasks.append(ai_detection_task)
        
        # Methodology review
        print("  → Methodology review...")
        methodology_text = truncate_text(
            truncated_sections.get('methodology', '') or truncated_sections.get('method', ''),
            max_tokens=1000
        )
        experiments_text = truncate_text(
            truncated_sections.get('experiments', ''),
            max_tokens=1000
        )
        methodology_task = create_methodology_review_task(
            self.methodology_agent,
            methodology_text,
            experiments_text
        )
        tasks.append(methodology_task)
        
        # Results validation
        print("  → Results validation...")
        results_text = truncate_text(
            truncated_sections.get('results', ''),
            max_tokens=1000
        )
        results_task = create_results_validation_task(
            self.results_agent,
            results_text,
            paper_data.get('tables_count', 0) > 0,
            paper_data.get('figures_count', 0) > 0
        )
        tasks.append(results_task)
        
        # Formatting check (uses metadata, not full text)
        print("  → Formatting compliance...")
        formatting_task = create_formatting_check_task(
            self.formatting_agent,
            paper_data
        )
        tasks.append(formatting_task)
        
        # Run analysis crew sequentially with AGGRESSIVE delays to avoid rate limits
        print("\n🤖 Executing agent tasks...")
        print("⚠️  Using conservative rate limiting to avoid API limits...")
        all_reviews = {}
        
        for i, task in enumerate(tasks):
            print(f"\n  Processing task {i+1}/{len(tasks)}...")
            
            # Create single-task crew
            agent = [
                self.plagiarism_agent,
                self.ai_detector_agent,
                self.methodology_agent,
                self.results_agent,
                self.formatting_agent
            ][i]
            
            task_names = ['plagiarism', 'ai_detection', 'methodology', 'results', 'formatting']
            
            # VERY AGGRESSIVE retry logic for rate limits
            max_retries = 7  # Increased from 5
            retry_delay = 30  # Increased from 15 seconds
            
            for attempt in range(max_retries):
                try:
                    # MANDATORY pre-task delay (except first task, first attempt)
                    if i > 0 or attempt > 0:
                        wait_time = retry_delay if attempt > 0 else 20  # Increased from 10
                        print(f"  ⏳ Waiting {wait_time}s to avoid rate limits...")
                        time.sleep(wait_time)
                    
                    # Use rate limiter to check if we can proceed
                    waited = self.rate_limiter.wait_if_needed(estimated_tokens=1500)
                    if waited > 0:
                        print(f"  ⏳ Rate limiter enforced additional {waited}s wait")
                    
                    # Show rate limit stats
                    stats = self.rate_limiter.get_stats()
                    print(f"  📊 Rate limit status: {stats['requests_remaining']} requests, "
                          f"{stats['tokens_remaining']} tokens remaining")
                    
                    print(f"  🔄 Attempting {task_names[i]}... (attempt {attempt + 1}/{max_retries})")
                    
                    task_crew = Crew(
                        agents=[agent],
                        tasks=[task],
                        process=Process.sequential,
                        verbose=False  # Reduce verbosity
                    )
                    
                    result = task_crew.kickoff()
                    
                    # Record successful request
                    self.rate_limiter.record_request(tokens=1500)
                    
                    all_reviews[task_names[i]] = str(result)
                    print(f"  ✅ {task_names[i]} completed successfully")
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    is_rate_limit = any(term in error_msg.lower() for term in [
                        'rate_limit', 'ratelimit', 'rate limit', 'too many requests', 
                        'quota', 'exceeded'
                    ])
                    
                    if is_rate_limit and attempt < max_retries - 1:
                        # EXPONENTIAL backoff: 30s, 60s, 120s, 240s, 480s, 960s
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"  ⚠️  Rate limit hit! Waiting {wait_time}s before retry...")
                        print(f"     (This is normal - Groq free tier has strict limits)")
                        time.sleep(wait_time)
                    else:
                        if is_rate_limit:
                            print(f"  ⚠️  Rate limit persists after {max_retries} attempts")
                            print(f"     Providing fallback review for {task_names[i]}")
                        else:
                            print(f"  ⚠️  Task failed: {task_names[i]}")
                            print(f"     Error: {error_msg[:200]}")
                        
                        # Provide fallback review
                        all_reviews[task_names[i]] = self._generate_fallback_review(task_names[i], error_msg)
                        break
            
            # MANDATORY delay between tasks (even longer)
            if i < len(tasks) - 1:
                print("  ⏳ Inter-task delay (20s) to ensure rate limit compliance...")
                time.sleep(20)  # Increased from 10s
        
        # Stage 3: Aggregate results with truncated reviews
        print("\n🔍 Stage 3: Aggregating results...")
        
        # Truncate reviews for aggregation
        truncated_reviews = {
            "paper_data": {
                "title": paper_data.get("title", "Unknown"),
                "abstract": truncate_text(paper_data.get("abstract", ""), max_tokens=300),
                "sections_count": len(paper_data.get("sections", {})),
                "references_count": len(paper_data.get("references", [])),
                "figures_count": paper_data.get("figures_count", 0),
                "tables_count": paper_data.get("tables_count", 0)
            },
            "plagiarism": truncate_text(all_reviews.get("plagiarism", ""), max_tokens=400),
            "ai_detection": truncate_text(all_reviews.get("ai_detection", ""), max_tokens=400),
            "methodology": truncate_text(all_reviews.get("methodology", ""), max_tokens=400),
            "results": truncate_text(all_reviews.get("results", ""), max_tokens=400),
            "formatting": truncate_text(all_reviews.get("formatting", ""), max_tokens=400)
        }
        
        print(f"📊 Aggregation input: {format_token_info(str(truncated_reviews))}")
        
        time.sleep(5)  # Rate limiting
        
        aggregation_task = create_aggregation_task(
            self.aggregator_agent,
            truncated_reviews
        )
        
        aggregation_crew = Crew(
            agents=[self.aggregator_agent],
            tasks=[aggregation_task],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            final_result = aggregation_crew.kickoff()
        except Exception as e:
            print(f"⚠️  Warning: Aggregation error: {e}")
            final_result = "Aggregation failed due to rate limits. See individual reviews above."
        
        # Format final report
        report = self._format_final_report(
            paper_data,
            all_reviews,
            final_result
        )
        
        print("\n✅ Review complete!")
        print("="*70)
        
        return report
    
    def _parse_pdf_directly(self, pdf_path: str) -> dict:
        """Parse PDF directly using PyPDF2 without agent"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            # Extract components
            title = self._extract_title(text)
            abstract = self._extract_section(text, "abstract")
            sections = self._extract_all_sections(text)
            references = self._extract_references(text)
            figures_count = text.lower().count("figure")
            tables_count = text.lower().count("table")
            
            return {
                "title": title,
                "abstract": abstract,
                "sections": sections,
                "references": references,
                "figures_count": figures_count,
                "tables_count": tables_count,
                "word_count": len(text.split()),
                "page_count": len(reader.pages)
            }
        except Exception as e:
            print(f"⚠️  PDF parsing error: {e}")
            return {
                "title": "PDF Parsing Failed",
                "abstract": "",
                "sections": {},
                "references": [],
                "figures_count": 0,
                "tables_count": 0,
                "word_count": 0,
                "page_count": 0
            }
    
    def _extract_title(self, text: str) -> str:
        """Extract paper title"""
        lines = text.split('\n')
        for line in lines[:10]:
            if 10 < len(line.strip()) < 200:
                return line.strip()
        return "Unknown Title"
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract specific section"""
        pattern = rf"{section_name}[\s\n]+(.*?)(?=\n[A-Z][a-z]+\n|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_all_sections(self, text: str) -> dict:
        """Extract all major sections"""
        sections = {}
        section_names = [
            "introduction", "related work", "methodology", "method",
            "experiments", "results", "discussion", "conclusion"
        ]
        for section in section_names:
            content = self._extract_section(text, section)
            if content:
                sections[section] = content
        return sections
    
    def _extract_references(self, text: str) -> list:
        """Extract bibliography"""
        ref_patterns = [
            r'REFERENCES\n(.*?)(?=\n[A-Z][A-Z\s]+\n|\Z)',
            r'References\n(.*?)(?=\n[A-Z][A-Z\s]+\n|\Z)',
            r'Bibliography\n(.*?)(?=\n[A-Z][A-Z\s]+\n|\Z)',
        ]
        
        ref_section = ""
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                ref_section = match.group(1)
                break
        
        if not ref_section:
            lines = text.split('\n')
            ref_start = -1
            for i, line in enumerate(lines):
                if re.match(r'^\s*(REFERENCES|References|Bibliography)\s*$', line, re.IGNORECASE):
                    ref_start = i
                    break
            
            if ref_start > 0:
                ref_section = '\n'.join(lines[ref_start+1:ref_start+100])
        
        if not ref_section:
            return ["References not found"]
        
        refs = []
        ref_matches = re.findall(r'([A-Z][a-z]+.*?\d{4}[a-z]?\.)', ref_section)
        if ref_matches:
            refs = ref_matches[:20]
        else:
            refs = [line.strip() for line in ref_section.split('\n') if line.strip() and len(line.strip()) > 20][:20]
        
        return refs if refs else ["References extracted: see full paper"]
    
    def _format_final_report(self, paper_data: dict, all_reviews: dict, final_result) -> dict:
        """Format comprehensive final report with robust score aggregation"""
        
        # Use robust score aggregation
        aggregated = safe_aggregate(all_reviews, str(final_result))
        
        # Analyze paper structure
        analyzer = SectionAnalyzer()
        structure_analysis = analyzer.analyze_paper_structure(paper_data)
        
        return {
            "paper_title": paper_data.get("title", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "review_system": "CrewAI + Groq",
            "paper_metadata": {
                "abstract_length": len(paper_data.get("abstract", "")),
                "sections_count": len(paper_data.get("sections", {})),
                "references_count": len(paper_data.get("references", [])),
                "figures_count": paper_data.get("figures_count", 0),
                "tables_count": paper_data.get("tables_count", 0)
            },
            "paper_data": {
                "title": paper_data.get("title", "Unknown"),
                "abstract": paper_data.get("abstract", ""),
                "sections": paper_data.get("sections", {}),
                "references": paper_data.get("references", []),
                "figures_count": paper_data.get("figures_count", 0),
                "tables_count": paper_data.get("tables_count", 0),
                "word_count": paper_data.get("word_count", 0),
                "page_count": paper_data.get("page_count", 0)
            },
            "structure_analysis": structure_analysis,
            "agent_reviews": {
                "plagiarism": all_reviews.get("plagiarism", ""),
                "ai_detection": all_reviews.get("ai_detection", ""),
                "methodology": all_reviews.get("methodology", ""),
                "results": all_reviews.get("results", ""),
                "formatting": all_reviews.get("formatting", "")
            },
            "final_assessment": str(final_result),
            "scores": {
                "overall_score": aggregated['overall_score'],
                "recommendation": aggregated['recommendation'],
                "detailed_scores": aggregated['detailed_scores'],
                "extracted_scores": aggregated.get('extracted_scores', {})
            },
            "issues": aggregated.get('issues', []),
            "generated_by": "CrewAI AutoReviewer v2.1"
        }
    
    def save_report(self, report: dict, output_path: str):
        """Save report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"💾 Report saved to: {output_path}")
    
    def print_report(self, report: dict):
        """Print formatted report"""
        print("\n" + "="*70)
        print("📋 CREWAI PAPER REVIEW REPORT")
        print("="*70)
        print(f"\n📄 Paper: {report['paper_title']}")
        print(f"🤖 System: {report['review_system']}")
        print(f"📅 Date: {report['timestamp']}")
        
        print("\n📊 Paper Metadata:")
        for key, value in report['paper_metadata'].items():
            print(f"  • {key}: {value}")
        
        print("\n🔍 Final Assessment:")
        print(report['final_assessment'])
        
        print("\n" + "="*70)
