"""
Connection pooling and caching utilities for AutoTestify
Improves performance and stability through efficient resource management
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import threading
from typing import Dict, Any, Optional
import json
import hashlib
import os
import logging

class ConnectionPoolManager:
    """Manages HTTP connection pools for better performance and reliability"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sessions = {}
        self.lock = threading.Lock()
    
    def get_session(self, service_name: str = 'default') -> requests.Session:
        """Get or create a session with connection pooling and retry logic"""
        with self.lock:
            if service_name not in self.sessions:
                session = requests.Session()
                
                # Configure retry strategy
                retry_strategy = Retry(
                    total=3,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
                    backoff_factor=1
                )
                
                # Configure HTTP adapter with connection pooling
                adapter = HTTPAdapter(
                    pool_connections=10,
                    pool_maxsize=20,
                    max_retries=retry_strategy,
                    pool_block=False
                )
                
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                
                # Set default headers
                session.headers.update({
                    'User-Agent': 'AutoTestify/1.0 (Automated Testing Platform)',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                })
                
                # Set default timeout
                session.timeout = 30
                
                self.sessions[service_name] = session
                self.logger.info(f"Created new session for {service_name}")
            
            return self.sessions[service_name]
    
    def close_all_sessions(self):
        """Close all active sessions"""
        with self.lock:
            for service_name, session in self.sessions.items():
                try:
                    session.close()
                    self.logger.info(f"Closed session for {service_name}")
                except Exception as e:
                    self.logger.error(f"Error closing session for {service_name}: {e}")
            self.sessions.clear()

class CacheManager:
    """Simple file-based cache for API responses and analysis results"""
    
    def __init__(self, cache_dir: str = 'cache', max_age_seconds: int = 3600):
        self.cache_dir = cache_dir
        self.max_age = max_age_seconds
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Clean old cache entries on startup
        self._cleanup_expired_cache()
    
    def _get_cache_key(self, key: str) -> str:
        """Generate a safe cache key from input"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get the full path for a cache file"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached data if it exists and is not expired"""
        cache_key = self._get_cache_key(key)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            if not os.path.exists(cache_path):
                return None
            
            # Check if cache is expired
            cache_age = time.time() - os.path.getmtime(cache_path)
            if cache_age > self.max_age:
                os.remove(cache_path)
                return None
            
            # Load cached data
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                self.logger.debug(f"Cache hit for key: {key[:50]}...")
                return cached_data['data']
                
        except Exception as e:
            self.logger.error(f"Error reading cache for key {key}: {e}")
            # Remove corrupted cache file
            try:
                os.remove(cache_path)
            except:
                pass
            return None
    
    def set(self, key: str, data: Any) -> bool:
        """Store data in cache"""
        cache_key = self._get_cache_key(key)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_data = {
                'timestamp': time.time(),
                'key': key,
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, default=str, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Cached data for key: {key[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching data for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached data"""
        cache_key = self._get_cache_key(key)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
                self.logger.debug(f"Deleted cache for key: {key[:50]}...")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting cache for key {key}: {e}")
            return False
    
    def clear_all(self) -> int:
        """Clear all cached data"""
        cleared_count = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
                    cleared_count += 1
            
            self.logger.info(f"Cleared {cleared_count} cache entries")
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return cleared_count
    
    def _cleanup_expired_cache(self):
        """Remove expired cache entries"""
        cleaned_count = 0
        try:
            current_time = time.time()
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > self.max_age:
                        os.remove(file_path)
                        cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired cache entries")
                
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f)) 
                for f in cache_files
            )
            
            return {
                'total_entries': len(cache_files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_directory': self.cache_dir,
                'max_age_seconds': self.max_age
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}

class RateLimiter:
    """Simple rate limiter to prevent API abuse"""
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limits"""
        with self.lock:
            current_time = time.time()
            
            # Clean old entries
            if identifier in self.requests:
                self.requests[identifier] = [
                    req_time for req_time in self.requests[identifier]
                    if current_time - req_time < self.time_window
                ]
            else:
                self.requests[identifier] = []
            
            # Check if under limit
            if len(self.requests[identifier]) < self.max_requests:
                self.requests[identifier].append(current_time)
                return True
            else:
                self.logger.warning(f"Rate limit exceeded for {identifier}")
                return False
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        with self.lock:
            current_time = time.time()
            
            if identifier not in self.requests:
                return self.max_requests
            
            # Clean old entries
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < self.time_window
            ]
            
            return max(0, self.max_requests - len(self.requests[identifier]))

# Global instances
connection_pool = ConnectionPoolManager()
cache_manager = CacheManager()
rate_limiter = RateLimiter()

def get_cached_or_fetch(cache_key: str, fetch_function, *args, **kwargs):
    """Helper function to get cached data or fetch and cache new data"""
    # Try to get from cache first
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Fetch new data
    try:
        fresh_data = fetch_function(*args, **kwargs)
        # Cache the result
        cache_manager.set(cache_key, fresh_data)
        return fresh_data
    except Exception as e:
        logging.getLogger(__name__).error(f"Error fetching data for cache key {cache_key}: {e}")
        raise

def cleanup_resources():
    """Cleanup all resources on application shutdown"""
    connection_pool.close_all_sessions()
    logging.getLogger(__name__).info("Cleaned up all resources")

# Register cleanup function
import atexit
atexit.register(cleanup_resources)