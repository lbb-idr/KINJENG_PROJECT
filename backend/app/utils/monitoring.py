"""
Lightweight metrics collector for MiroFish
Tracks request counts, latencies, errors
"""
import time
import threading
from collections import defaultdict

class MetricsCollector:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def init(self):
        if self._initialized:
            return
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        self.endpoint_stats = defaultdict(lambda: {'count': 0, 'errors': 0, 'total_latency': 0.0})
        self.llm_calls = 0
        self.llm_errors = 0
        self._initialized = True
    
    def record_request(self, endpoint, latency, error=False):
        self.request_count += 1
        self.total_latency += latency
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['total_latency'] += latency
        if error:
            self.error_count += 1
            stats['errors'] += 1
    
    def record_llm_call(self, error=False):
        self.llm_calls += 1
        if error:
            self.llm_errors += 1
    
    def get_metrics(self):
        stats = {}
        for endpoint, data in self.endpoint_stats.items():
            avg_latency = data['total_latency'] / data['count'] if data['count'] > 0 else 0
            stats[endpoint] = {
                'count': data['count'],
                'errors': data['errors'],
                'avg_latency_ms': round(avg_latency * 1000, 2)
            }
        uptime = time.time() - self.start_time
        avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0
        return {
            'uptime_seconds': round(uptime, 2),
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'avg_latency_ms': round(avg_latency * 1000, 2),
            'llm_calls': self.llm_calls,
            'llm_errors': self.llm_errors,
            'endpoints': stats,
        }

metrics = MetricsCollector()
