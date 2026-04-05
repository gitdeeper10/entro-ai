"""
vLLM Adapter for EDT Controller
Integrates with vLLM inference engine
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Optional, Any


class VLLMAdapter:
    """
    Adapter for vLLM inference server
    Communicates with vLLM API to apply interventions
    """
    
    def __init__(self, engine_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize vLLM adapter
        
        Args:
            engine_url: vLLM API endpoint URL
            api_key: Optional API key for authentication
        """
        self.engine_url = engine_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to vLLM API"""
        url = f"{self.engine_url}{endpoint}"
        
        try:
            if method == "GET":
                with urllib.request.urlopen(url) as response:
                    return json.loads(response.read().decode())
            else:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode() if data else None,
                    headers=self.headers,
                    method=method
                )
                with urllib.request.urlopen(req) as response:
                    return json.loads(response.read().decode())
        except urllib.error.URLError as e:
            return {"error": str(e), "status": "unavailable"}
    
    def get_model_config(self) -> Dict:
        """Get current model configuration"""
        return self._make_request("GET", "/v1/model/config")
    
    def set_batch_size(self, batch_size: int) -> Dict:
        """
        Set max batch size for inference
        
        Args:
            batch_size: New batch size
        """
        return self._make_request("POST", "/v1/scheduler/config", {"max_batch_size": batch_size})
    
    def set_quantization(self, quantization: str) -> Dict:
        """
        Set quantization mode
        
        Args:
            quantization: "fp16", "int8", "int4"
        """
        return self._make_request("POST", "/v1/model/quantization", {"quantization": quantization})
    
    def get_metrics(self) -> Dict:
        """Get vLLM metrics"""
        return self._make_request("GET", "/metrics")
    
    def health_check(self) -> bool:
        """Check if vLLM is healthy"""
        result = self._make_request("GET", "/health")
        return result.get("status") == "ok"
    
    def get_kv_cache_usage(self) -> float:
        """Get KV-cache usage percentage (0-1)"""
        metrics = self.get_metrics()
        # Extract KV-cache usage from metrics
        if "kv_cache_usage" in metrics:
            return metrics["kv_cache_usage"]
        return 0.5  # Default fallback
    
    def get_token_rate(self) -> float:
        """Get current token generation rate"""
        metrics = self.get_metrics()
        if "token_rate" in metrics:
            return metrics["token_rate"]
        return 100.0  # Default fallback


class MockVLLMAdapter(VLLMAdapter):
    """Mock adapter for testing without vLLM"""
    
    def __init__(self):
        super().__init__(engine_url="http://localhost:8000")
        self._mock_config = {
            "max_batch_size": 32,
            "quantization": "fp16",
            "model": "llama-7b"
        }
        self._mock_metrics = {
            "kv_cache_usage": 0.6,
            "token_rate": 800,
            "gpu_mem_util": 0.65,
            "latency_ms": 45
        }
    
    def get_model_config(self) -> Dict:
        return self._mock_config
    
    def set_batch_size(self, batch_size: int) -> Dict:
        self._mock_config["max_batch_size"] = batch_size
        return {"success": True, "new_batch_size": batch_size}
    
    def set_quantization(self, quantization: str) -> Dict:
        self._mock_config["quantization"] = quantization
        return {"success": True, "new_quantization": quantization}
    
    def get_metrics(self) -> Dict:
        return self._mock_config | self._mock_metrics
    
    def health_check(self) -> bool:
        return True
    
    def get_kv_cache_usage(self) -> float:
        return self._mock_metrics["kv_cache_usage"]
    
    def get_token_rate(self) -> float:
        return self._mock_metrics["token_rate"]


def create_adapter(engine_url: str = "http://localhost:8000", mock: bool = False) -> VLLMAdapter:
    """Factory function to create adapter"""
    if mock:
        return MockVLLMAdapter()
    return VLLMAdapter(engine_url)
