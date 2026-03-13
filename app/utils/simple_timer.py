"""
Simple timing utility for agent performance tracking
"""
import time
import asyncio
from functools import wraps
from typing import Dict, Any, List
from datetime import datetime

class SimpleTimer:
    """Simple timer for tracking agent execution times"""
    
    def __init__(self):
        self.timings = {}
        self.current_session = []
    
    def time_agent(self, agent_name: str):
        """Decorator to time agent execution - works with both sync and async functions"""
        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                # Async function decorator
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    # Store timing
                    if agent_name not in self.timings:
                        self.timings[agent_name] = []
                    self.timings[agent_name].append(execution_time)
                    
                    # Store in current session for detailed analysis
                    self.current_session.append({
                        'agent': agent_name,
                        'duration': execution_time,
                        'timestamp': datetime.now(),
                        'status': 'completed'
                    })
                    
                    print(f"⏱️  {agent_name} completed in {execution_time:.2f}s")
                    return result
                return async_wrapper
            else:
                # Sync function decorator
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    # Store timing
                    if agent_name not in self.timings:
                        self.timings[agent_name] = []
                    self.timings[agent_name].append(execution_time)
                    
                    # Store in current session for detailed analysis
                    self.current_session.append({
                        'agent': agent_name,
                        'duration': execution_time,
                        'timestamp': datetime.now(),
                        'status': 'completed'
                    })
                    
                    print(f"⏱️  {agent_name} completed in {execution_time:.2f}s")
                    return result
                return sync_wrapper
        return decorator
    
    def get_timings(self) -> Dict[str, Any]:
        """Get all recorded timings"""
        return self.timings
    
    def get_current_session(self) -> List[Dict[str, Any]]:
        """Get current session timing details"""
        return self.current_session
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.current_session:
            return {}
        
        total_time = sum(item['duration'] for item in self.current_session)
        
        summary = {
            'total_time': total_time,
            'agent_count': len(self.current_session),
            'breakdown': {},
            'percentages': {}
        }
        
        for item in self.current_session:
            agent = item['agent']
            duration = item['duration']
            summary['breakdown'][agent] = duration
            summary['percentages'][agent] = (duration / total_time * 100) if total_time > 0 else 0
        
        return summary
    
    def reset_session(self):
        """Reset current session"""
        self.current_session = []
    
    def reset(self):
        """Reset all timings"""
        self.timings = {}
        self.current_session = []

# Global instance
simple_timer = SimpleTimer()