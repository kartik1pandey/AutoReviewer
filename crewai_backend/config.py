"""
Configuration for CrewAI-based AutoReviewer
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Fast and free tier friendly

# Agent Configuration
AGENT_CONFIG = {
    "verbose": False,  # Reduce verbosity to save tokens
    "allow_delegation": False,
    "max_iter": 2,  # Reduced from 3 to save tokens
    "max_rpm": 10,
}

# LLM Configuration
LLM_CONFIG = {
    "model": GROQ_MODEL,
    "temperature": 0.1,
    "max_tokens": 512,  # Reduced to 512 to fit free tier better
}

# Task Configuration
TASK_CONFIG = {
    "async_execution": False,
}

# Review Thresholds
THRESHOLDS = {
    "plagiarism_similarity": 0.85,
    "ai_perplexity": 50,
    "ai_burstiness": 0.3,
    "min_references": 5,
    "min_abstract_length": 100,
    "accept_score": 7.5,
    "revise_score": 5.0,
}
