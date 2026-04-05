"""
Inference Stress Test Engine
Simulates LLM inference load for validation
"""

import time
import math
import random
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SimulationConfig:
    """Configuration for stress test simulation"""
    duration_seconds: int = 600
    initial_rho_ratio: float = 0.3
    max_rho_ratio: float = 2.0
    architecture: str = "transformer_llm"
    n_layers: int = 32
    d_model: int = 4096
    kv_cache_gb: float = 40.0
    context_length: int = 8192
    update_interval_ms: int = 10


@dataclass
class SimulationStep:
    """Single simulation step result"""
    timestamp: float
    rho_ratio: float
    psi: float
    kappa: float
    token_rate: float
    kv_cache_used: float
    gpu_mem_util: float
    edt_level: int
    is_collapsed: bool


class StressTestEngine:
    """
    Simulates inference load to validate ENTRO-AI predictions
    """
    
    # Architecture-specific noise parameters
    ARCHITECTURE_NOISE = {
        "transformer_llm": 0.08,
        "bert": 0.06,
        "vit": 0.07,
        "neuromorphic": 0.04
    }
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.steps: List[SimulationStep] = []
        self._is_running = False
        self._callbacks: List[Callable] = []
        
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from entro_ai.core import EntroAIMonitor
        
        self.monitor = EntroAIMonitor(
            architecture=config.architecture,
            n_layers=config.n_layers,
            d_model=config.d_model,
            kv_cache_gb=config.kv_cache_gb
        )
    
    def register_callback(self, callback: Callable[[SimulationStep], None]):
        """Register callback for each simulation step"""
        self._callbacks.append(callback)
    
    def _get_architecture_noise(self) -> float:
        """Get noise level for current architecture"""
        return self.ARCHITECTURE_NOISE.get(self.config.architecture, 0.07)
    
    def _simulate_telemetry(self, progress: float) -> Tuple[float, float, float, float]:
        """
        Simulate telemetry based on load progress
        
        Args:
            progress: 0 to 1 (0 = start, 1 = max load)
        
        Returns:
            (rho_ratio, kv_cache_used, gpu_mem_util, token_rate)
        """
        noise = self._get_architecture_noise()
        
        # Target rho_ratio increases linearly with progress
        target_rho = self.config.initial_rho_ratio + progress * (self.config.max_rho_ratio - self.config.initial_rho_ratio)
        
        # Add noise
        rho_ratio = target_rho + random.uniform(-noise, noise)
        rho_ratio = max(0.1, min(self.config.max_rho_ratio + 0.2, rho_ratio))
        
        # Correlated metrics
        kv_cache_used = min(0.95, rho_ratio * 0.9 + random.uniform(-0.05, 0.05))
        gpu_mem_util = min(0.95, rho_ratio * 0.85 + random.uniform(-0.05, 0.05))
        token_rate = 800 * rho_ratio + random.uniform(-50, 50)
        token_rate = max(50, token_rate)
        
        return rho_ratio, kv_cache_used, gpu_mem_util, token_rate
    
    def _check_collapse(self, psi: float, kappa: float) -> bool:
        """Check if system has collapsed"""
        return psi >= 2.0 or kappa <= 0.12
    
    def run(self) -> List[SimulationStep]:
        """
        Run stress test simulation
        
        Returns:
            List of simulation steps
        """
        self._is_running = True
        self.steps = []
        
        start_time = time.time()
        end_time = start_time + self.config.duration_seconds
        
        step_interval = self.config.update_interval_ms / 1000.0
        
        print(f"[Simulation] Starting stress test for {self.config.architecture}")
        print(f"  Duration: {self.config.duration_seconds}s")
        print(f"  Max ρ/ρ_c: {self.config.max_rho_ratio}")
        
        collapsed = False
        collapse_time = None
        
        while time.time() < end_time and self._is_running:
            timestamp = time.time()
            progress = (timestamp - start_time) / self.config.duration_seconds
            
            # Get simulated telemetry
            rho_ratio, kv_cache_used, gpu_mem_util, token_rate = self._simulate_telemetry(progress)
            
            # Update monitor
            state = self.monitor.update(
                kv_cache_used=kv_cache_used,
                attn_flops_util=rho_ratio * 0.8,
                token_rate=token_rate,
                context_length=self.config.context_length,
                gpu_mem_util=gpu_mem_util,
                timestamp=timestamp
            )
            
            # Check for collapse
            if not collapsed and self._check_collapse(state.psi, state.kappa):
                collapsed = True
                collapse_time = timestamp
                print(f"[Simulation] COLLAPSE detected at t={timestamp - start_time:.1f}s")
                print(f"  Ψ = {state.psi:.3f}, κ = {state.kappa:.3f}")
            
            step = SimulationStep(
                timestamp=timestamp - start_time,
                rho_ratio=state.rho_ratio,
                psi=state.psi,
                kappa=state.kappa,
                token_rate=token_rate,
                kv_cache_used=kv_cache_used,
                gpu_mem_util=gpu_mem_util,
                edt_level=state.edt_level,
                is_collapsed=collapsed
            )
            
            self.steps.append(step)
            
            # Trigger callbacks
            for callback in self._callbacks:
                try:
                    callback(step)
                except Exception as e:
                    print(f"Callback error: {e}")
            
            # Sleep for step interval
            time.sleep(step_interval)
        
        # Summary
        print(f"\n[Simulation] Complete")
        print(f"  Total steps: {len(self.steps)}")
        print(f"  Collapse detected: {collapsed}")
        if collapse_time:
            print(f"  Collapse at: {collapse_time - start_time:.1f}s")
        
        self._is_running = False
        return self.steps
    
    def stop(self):
        """Stop the simulation"""
        self._is_running = False
    
    def get_statistics(self) -> Dict:
        """Get simulation statistics"""
        if not self.steps:
            return {}
        
        psi_values = [s.psi for s in self.steps]
        kappa_values = [s.kappa for s in self.steps]
        
        collapse_steps = [s for s in self.steps if s.is_collapsed]
        
        return {
            "architecture": self.config.architecture,
            "total_steps": len(self.steps),
            "duration_seconds": self.config.duration_seconds,
            "max_psi": max(psi_values),
            "avg_psi": sum(psi_values) / len(psi_values),
            "min_kappa": min(kappa_values),
            "avg_kappa": sum(kappa_values) / len(kappa_values),
            "collapse_detected": len(collapse_steps) > 0,
            "collapse_time": collapse_steps[0].timestamp if collapse_steps else None,
            "edt_interventions": len([s for s in self.steps if s.edt_level > 0])
        }


def quick_test() -> Dict:
    """Run a quick test simulation"""
    config = SimulationConfig(
        duration_seconds=60,
        initial_rho_ratio=0.3,
        max_rho_ratio=1.8,
        architecture="transformer_llm"
    )
    
    engine = StressTestEngine(config)
    steps = engine.run()
    
    return engine.get_statistics()


if __name__ == "__main__":
    stats = quick_test()
    print(f"\nStatistics: {stats}")
