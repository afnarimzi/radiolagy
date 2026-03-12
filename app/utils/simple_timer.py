"""
Simple timing utility for agent performance tracking
"""
import time
from functools import wraps
from typing import Dict, Any

class SimpleTimer:
    """Simple timer for tracking agent execution times"""
    
    def __init__(self):
        self.timings = {}
    
    def time_agent(self, agent_name: str):
        """Decorator to time agent execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Store timing
                if agent_name not in self.timings:
                    self.timings[agent_name] = []
                self.timings[agent_name].append(execution_time)
                
                print(f"⏱️  {agent_name} completed in {execution_time:.2f}s")
                return result
            return wrapper
        return decorator
    
    def get_timings(self) -> Dict[str, Any]:
        """Get all recorded timings"""
        return self.timings
    
    def reset(self):
        """Reset all timings"""
        self.timings = {}

# Global instance
simple_timer = SimpleTimer()