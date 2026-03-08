"""
Advanced Rate Limiter for Groq API
Tracks requests and enforces conservative limits
"""

import time
from datetime import datetime, timedelta
from typing import Optional

class RateLimiter:
    """
    Rate limiter for Groq API free tier
    
    Groq Free Tier Limits:
    - 30 requests per minute
    - 6,000 tokens per minute
    - 14,400 tokens per day
    """
    
    def __init__(self):
        self.requests = []  # List of (timestamp, tokens) tuples
        self.max_requests_per_minute = 25  # Conservative (actual: 30)
        self.max_tokens_per_minute = 5000  # Conservative (actual: 6000)
        self.max_tokens_per_day = 12000  # Conservative (actual: 14400)
        
    def _clean_old_requests(self):
        """Remove requests older than 1 minute"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        self.requests = [
            (ts, tokens) for ts, tokens in self.requests
            if ts > one_minute_ago
        ]
    
    def _get_recent_stats(self) -> tuple:
        """Get recent request and token counts"""
        self._clean_old_requests()
        
        if not self.requests:
            return 0, 0
        
        request_count = len(self.requests)
        token_count = sum(tokens for _, tokens in self.requests)
        
        return request_count, token_count
    
    def can_make_request(self, estimated_tokens: int = 1500) -> tuple[bool, Optional[int]]:
        """
        Check if we can make a request
        
        Args:
            estimated_tokens: Estimated tokens for this request
            
        Returns:
            (can_proceed, wait_seconds)
        """
        request_count, token_count = self._get_recent_stats()
        
        # Check request limit
        if request_count >= self.max_requests_per_minute:
            # Calculate wait time
            oldest_request = min(ts for ts, _ in self.requests)
            wait_seconds = 60 - (datetime.now() - oldest_request).seconds
            return False, max(wait_seconds, 1)
        
        # Check token limit
        if token_count + estimated_tokens > self.max_tokens_per_minute:
            # Calculate wait time
            oldest_request = min(ts for ts, _ in self.requests)
            wait_seconds = 60 - (datetime.now() - oldest_request).seconds
            return False, max(wait_seconds, 1)
        
        return True, None
    
    def record_request(self, tokens: int = 1500):
        """Record a successful request"""
        self.requests.append((datetime.now(), tokens))
    
    def wait_if_needed(self, estimated_tokens: int = 1500) -> int:
        """
        Wait if necessary to respect rate limits
        
        Args:
            estimated_tokens: Estimated tokens for this request
            
        Returns:
            Seconds waited
        """
        can_proceed, wait_seconds = self.can_make_request(estimated_tokens)
        
        if not can_proceed:
            print(f"  ⏳ Rate limit protection: waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
            return wait_seconds
        
        return 0
    
    def get_stats(self) -> dict:
        """Get current rate limit statistics"""
        request_count, token_count = self._get_recent_stats()
        
        return {
            'requests_last_minute': request_count,
            'tokens_last_minute': token_count,
            'requests_remaining': self.max_requests_per_minute - request_count,
            'tokens_remaining': self.max_tokens_per_minute - token_count,
            'utilization': {
                'requests': f"{(request_count / self.max_requests_per_minute) * 100:.1f}%",
                'tokens': f"{(token_count / self.max_tokens_per_minute) * 100:.1f}%"
            }
        }

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
