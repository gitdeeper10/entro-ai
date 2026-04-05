"""
EDT Resource Scheduler
Integrates with inference engine to apply interventions
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class SchedulerAction(Enum):
    """Actions that can be taken by the scheduler"""
    NONE = "none"
    REDUCE_BATCH_SIZE = "reduce_batch_size"
    ENABLE_INT8 = "enable_int8_quantization"
    ROUTE_SMALLER_MODEL = "route_to_smaller_model"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"


@dataclass
class SchedulerConfig:
    """Configuration for the resource scheduler"""
    default_batch_size: int = 32
    min_batch_size: int = 4
    default_quantization: str = "fp16"
    default_model: str = "default"
    fallback_model: str = "small"
    graceful_timeout_seconds: int = 30


class EDTScheduler:
    """
    Resource scheduler that applies EDT interventions
    to the inference engine
    """
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.current_batch_size = self.config.default_batch_size
        self.current_quantization = self.config.default_quantization
        self.current_model = self.config.default_model
        self.is_quantization_enabled = False
        self.is_shutdown_initiated = False
        
        # Callbacks for external integration
        self._callbacks: Dict[SchedulerAction, list] = {
            action: [] for action in SchedulerAction
        }
    
    def register_callback(self, action: SchedulerAction, callback: Callable[[Dict], None]):
        """Register callback for when an action is taken"""
        self._callbacks[action].append(callback)
    
    def _trigger_callbacks(self, action: SchedulerAction, data: Dict):
        """Trigger all callbacks for an action"""
        for callback in self._callbacks[action]:
            try:
                callback(data)
            except Exception as e:
                print(f"[Scheduler] Callback error for {action}: {e}")
    
    def apply_level1_soft(self) -> Dict:
        """
        Level 1: Reduce batch size by 40%
        Returns: Action result
        """
        new_batch_size = int(self.current_batch_size * 0.6)
        new_batch_size = max(new_batch_size, self.config.min_batch_size)
        
        old_batch_size = self.current_batch_size
        self.current_batch_size = new_batch_size
        
        result = {
            "action": SchedulerAction.REDUCE_BATCH_SIZE.value,
            "old_batch_size": old_batch_size,
            "new_batch_size": new_batch_size,
            "reduction_percent": (1 - new_batch_size/old_batch_size) * 100
        }
        
        self._trigger_callbacks(SchedulerAction.REDUCE_BATCH_SIZE, result)
        return result
    
    def apply_level2_medium(self) -> Dict:
        """
        Level 2: Enable INT8 dynamic quantization
        Returns: Action result
        """
        old_quantization = self.current_quantization
        self.current_quantization = "int8"
        self.is_quantization_enabled = True
        
        result = {
            "action": SchedulerAction.ENABLE_INT8.value,
            "old_quantization": old_quantization,
            "new_quantization": "int8",
            "estimated_memory_reduction": 0.35
        }
        
        self._trigger_callbacks(SchedulerAction.ENABLE_INT8, result)
        return result
    
    def apply_level3_hard(self) -> Dict:
        """
        Level 3: Route to smaller model variant
        Returns: Action result
        """
        old_model = self.current_model
        self.current_model = self.config.fallback_model
        
        result = {
            "action": SchedulerAction.ROUTE_SMALLER_MODEL.value,
            "old_model": old_model,
            "new_model": self.config.fallback_model,
            "estimated_quality_reduction": 0.15
        }
        
        self._trigger_callbacks(SchedulerAction.ROUTE_SMALLER_MODEL, result)
        return result
    
    def apply_level4_critical(self) -> Dict:
        """
        Level 4: Graceful shutdown + failover
        Returns: Action result
        """
        if self.is_shutdown_initiated:
            return {"action": SchedulerAction.GRACEFUL_SHUTDOWN.value, "already_initiated": True}
        
        self.is_shutdown_initiated = True
        
        result = {
            "action": SchedulerAction.GRACEFUL_SHUTDOWN.value,
            "timeout_seconds": self.config.graceful_timeout_seconds,
            "message": "Initiating graceful shutdown"
        }
        
        self._trigger_callbacks(SchedulerAction.GRACEFUL_SHUTDOWN, result)
        return result
    
    def apply_recovery(self) -> Dict:
        """
        Recovery: Restore previous configuration
        Returns: Action result
        """
        result = {
            "action": "recovery",
            "batch_size_restored": self.current_batch_size != self.config.default_batch_size,
            "quantization_restored": self.is_quantization_enabled,
            "model_restored": self.current_model != self.config.default_model
        }
        
        # Restore defaults
        self.current_batch_size = self.config.default_batch_size
        self.current_quantization = self.config.default_quantization
        self.current_model = self.config.default_model
        self.is_quantization_enabled = False
        self.is_shutdown_initiated = False
        
        return result
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            "current_batch_size": self.current_batch_size,
            "current_quantization": self.current_quantization,
            "current_model": self.current_model,
            "is_quantization_enabled": self.is_quantization_enabled,
            "is_shutdown_initiated": self.is_shutdown_initiated,
            "default_batch_size": self.config.default_batch_size,
            "min_batch_size": self.config.min_batch_size,
            "fallback_model": self.config.fallback_model
        }


# Singleton instance
_default_scheduler: Optional[EDTScheduler] = None


def get_scheduler() -> EDTScheduler:
    """Get global scheduler instance"""
    global _default_scheduler
    if _default_scheduler is None:
        _default_scheduler = EDTScheduler()
    return _default_scheduler
