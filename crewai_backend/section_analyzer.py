"""
Section-Aware Analysis System
Identifies paper sections and runs targeted analysis
"""

import re
from typing import Dict, List, Optional

class SectionAnalyzer:
    """Analyzes paper structure and extracts sections"""
    
    # Common section names in research papers
    SECTION_PATTERNS = {
        'abstract': [r'abstract', r'summary'],
        'introduction': [r'introduction', r'background'],
        'related_work': [r'related\s+work', r'literature\s+review', r'prior\s+work'],
        'methodology': [r'method', r'approach', r'technique', r'algorithm'],
        'experiments': [r'experiment', r'evaluation', r'empirical'],
        'results': [r'result', r'finding', r'performance'],
        'discussion': [r'discussion', r'analysis'],
        'conclusion': [r'conclusion', r'summary', r'future\s+work'],
        'references': [r'reference', r'bibliography', r'citation']
    }
    
    def __init__(self):
        self.sections = {}
        self.section_order = []
    
    def identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify and extract sections from paper text
        
        Args:
            text: Full paper text
            
        Returns:
            Dictionary of section_name -> section_content
        """
        if not text:
            return {}
        
        # Split into lines
        lines = text.split('\n')
        
        # Find section headers
        section_starts = []
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            
            # Check if line is a section header
            for section_name, patterns in self.SECTION_PATTERNS.items():
                for pattern in patterns:
                    if re.match(rf'^{pattern}s?$', line_clean) or \
                       re.match(rf'^\d+\.?\s*{pattern}s?$', line_clean):
                        section_starts.append((i, section_name, line))
                        break
        
        # Extract section content
        sections = {}
        for idx, (start_line, section_name, header) in enumerate(section_starts):
            # Find end of section (next section or end of document)
            if idx < len(section_starts) - 1:
                end_line = section_starts[idx + 1][0]
            else:
                end_line = len(lines)
            
            # Extract content
            content_lines = lines[start_line + 1:end_line]
            content = '\n'.join(content_lines).strip()
            
            if content:
                sections[section_name] = content
                self.section_order.append(section_name)
        
        self.sections = sections
        return sections
    
    def get_section(self, section_name: str) -> Optional[str]:
        """Get specific section content"""
        return self.sections.get(section_name)
    
    def has_section(self, section_name: str) -> bool:
        """Check if section exists"""
        return section_name in self.sections
    
    def get_section_summary(self) -> Dict[str, int]:
        """Get summary of sections found"""
        return {
            name: len(content)
            for name, content in self.sections.items()
        }
    
    def check_methodology_components(self, methodology_text: str) -> Dict[str, bool]:
        """
        Check for key methodology components
        
        Args:
            methodology_text: Text from methodology section
            
        Returns:
            Dictionary of component -> present (bool)
        """
        if not methodology_text:
            return {
                'problem_definition': False,
                'baseline_comparison': False,
                'ablation_study': False,
                'dataset_description': False
            }
        
        text_lower = methodology_text.lower()
        
        return {
            'problem_definition': any(term in text_lower for term in [
                'problem', 'objective', 'goal', 'aim', 'task'
            ]),
            'baseline_comparison': any(term in text_lower for term in [
                'baseline', 'comparison', 'compare', 'versus', 'vs'
            ]),
            'ablation_study': any(term in text_lower for term in [
                'ablation', 'ablate', 'component analysis', 'contribution'
            ]),
            'dataset_description': any(term in text_lower for term in [
                'dataset', 'data set', 'corpus', 'benchmark'
            ])
        }
    
    def extract_numeric_claims(self, results_text: str) -> List[Dict[str, any]]:
        """
        Extract numeric claims from results section
        
        Args:
            results_text: Text from results section
            
        Returns:
            List of claims with numbers and context
        """
        if not results_text:
            return []
        
        claims = []
        sentences = re.split(r'[.!?]+', results_text)
        
        # Patterns for numeric claims
        number_patterns = [
            r'\d+\.?\d*%',  # Percentages
            r'\d+\.?\d*\s*(?:accuracy|precision|recall|f1)',  # Metrics
            r'\d+\.?\d*\s*(?:improvement|increase|decrease)',  # Changes
            r'\d+\.?\d*x\s*(?:faster|slower|better)',  # Comparisons
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if sentence contains numbers
            if re.search(r'\d', sentence):
                # Extract all numbers
                numbers = re.findall(r'\d+\.?\d*', sentence)
                
                if numbers:
                    claims.append({
                        'sentence': sentence[:200],  # Limit length
                        'numbers': numbers,
                        'has_comparison': any(term in sentence.lower() for term in [
                            'than', 'versus', 'vs', 'compared', 'outperform'
                        ])
                    })
        
        return claims
    
    def check_citation_presence(self, text: str) -> Dict[str, any]:
        """
        Check for citations in text
        
        Args:
            text: Text to check
            
        Returns:
            Dictionary with citation statistics
        """
        if not text:
            return {
                'has_citations': False,
                'citation_count': 0,
                'citation_density': 0.0
            }
        
        # Patterns for citations
        citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\([A-Z][a-z]+\s+et\s+al\.,?\s+\d{4}\)',  # (Smith et al., 2020)
            r'\([A-Z][a-z]+\s+and\s+[A-Z][a-z]+,?\s+\d{4}\)',  # (Smith and Jones, 2020)
            r'\([A-Z][a-z]+,?\s+\d{4}\)',  # (Smith, 2020)
        ]
        
        citation_count = 0
        for pattern in citation_patterns:
            citation_count += len(re.findall(pattern, text))
        
        word_count = len(text.split())
        citation_density = citation_count / word_count if word_count > 0 else 0
        
        return {
            'has_citations': citation_count > 0,
            'citation_count': citation_count,
            'citation_density': round(citation_density, 4)
        }
    
    def analyze_paper_structure(self, paper_data: Dict) -> Dict[str, any]:
        """
        Comprehensive paper structure analysis
        
        Args:
            paper_data: Dictionary with paper content
            
        Returns:
            Dictionary with structure analysis
        """
        # Identify sections
        full_text = paper_data.get('abstract', '') + '\n\n'
        for section_name, content in paper_data.get('sections', {}).items():
            full_text += f"\n{section_name}\n{content}\n"
        
        sections = self.identify_sections(full_text)
        
        # Analyze methodology
        methodology_text = sections.get('methodology', '')
        methodology_components = self.check_methodology_components(methodology_text)
        
        # Analyze results
        results_text = sections.get('results', '')
        numeric_claims = self.extract_numeric_claims(results_text)
        
        # Check citations
        citation_stats = self.check_citation_presence(full_text)
        
        return {
            'sections_found': list(sections.keys()),
            'section_count': len(sections),
            'has_methodology': 'methodology' in sections,
            'has_experiments': 'experiments' in sections,
            'has_results': 'results' in sections,
            'methodology_components': methodology_components,
            'numeric_claims_count': len(numeric_claims),
            'numeric_claims': numeric_claims[:5],  # Top 5
            'citation_stats': citation_stats,
            'structure_score': self._calculate_structure_score(sections, methodology_components)
        }
    
    def _calculate_structure_score(self, sections: Dict, methodology_components: Dict) -> float:
        """Calculate structure quality score"""
        score = 0.0
        
        # Required sections (2 points each)
        required = ['introduction', 'methodology', 'results', 'conclusion']
        for section in required:
            if section in sections:
                score += 2.0
        
        # Methodology components (0.5 points each)
        for component, present in methodology_components.items():
            if present:
                score += 0.5
        
        return min(10.0, score)
