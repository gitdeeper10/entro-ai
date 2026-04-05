"""
ENTRO-AI EDT Controller Module
Entropy-Driven Throttling (EDT) for AI inference
Builds on ENTROPIA (E-LAB-01) · DOI: 10.5281/zenodo.19416737
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import IntEnum


class EDTLevel(IntEnum):
    """EDT intervention levels"""
    NONE = 0
    L1_SOFT = 1      # Reduce batch size
    L2_MEDIUM = 2    # INT8 quantization
    L3_HARD = 3      # Route to smaller model
    L4_CRITICAL = 4  # Graceful shutdown


@dataclass
class EDTIntervention:
    """Definition of an EDT intervention"""
    level: EDTLevel
    threshold: float
    action: str
    psi_reduction: float  # η_EDT
    reversibility_seconds: int
    description: str


# Intervention definitions (from Section 3.1)
INTERVENTIONS = {
    EDTLevel.L1_SOFT: EDTIntervention(
        level=EDTLevel.L1_SOFT,
        threshold=1.5,
        action="reduce_batch_size",
        psi_reduction=0.31,
        reversibility_seconds=30,
        description="Reduce batch size by 40%"
    ),
    EDTLevel.L2_MEDIUM: EDTIntervention(
        level=EDTLevel.L2_MEDIUM,
        threshold=1.7,
        action="enable_int8_quantization",
        psi_reduction=0.47,
        reversibility_seconds=60,
        description="Enable INT8 dynamic quantization"
    ),
    EDTLevel.L3_HARD: EDTIntervention(
        level=EDTLevel.L3_HARD,
        threshold=1.85,
        action="route_to_smaller_model",
        psi_reduction=0.68,
        reversibility_seconds=None,  # Manual confirmation required
        description="Route to smaller model variant"
    ),
    EDTLevel.L4_CRITICAL: EDTIntervention(
        level=EDTLevel.L4_CRITICAL,
        threshold=2.0,
        action="graceful_shutdown",
        psi_reduction=1.0,
        reversibility_seconds=None,  # Full restart required
        description="Graceful shutdown + failover"
    )
}


def get_edt_level(
    psi: float,
    threshold_l1: float = 1.5,
    threshold_l2: float = 1.7,
    threshold_l3: float = 1.85,
    threshold_l4: float = 2.0
) -> EDTLevel:
    """
    Determine EDT intervention level based on Ψ
    
    Args:
        psi: Current dissipation coefficient
        threshold_l1: Level 1 threshold
        threshold_l2: Level 2 threshold
        threshold_l3: Level 3 threshold
        threshold_l4: Level 4 threshold
    
    Returns:
        EDTLevel enum value
    """
    if psi >= threshold_l4:
        return EDTLevel.L4_CRITICAL
    elif psi >= threshold_l3:
        return EDTLevel.L3_HARD
    elif psi >= threshold_l2:
        return EDTLevel.L2_MEDIUM
    elif psi >= threshold_l1:
        return EDTLevel.L1_SOFT
    else:
        return EDTLevel.NONE


def get_intervention(level: EDTLevel) -> Optional[EDTIntervention]:
    """Get intervention definition for a level"""
    return INTERVENTIONS.get(level)


def compute_psi_after_intervention(
    psi_before: float,
    level: EDTLevel,
    current_intervention_magnitude: float = 0.0
) -> float:
    """
    Compute expected Ψ after applying intervention (Eq. 16 simplified)
    
    Ψ_after = Ψ_before - η_EDT × I(t)
    
    Args:
        psi_before: Ψ before intervention
        level: EDT level to apply
        current_intervention_magnitude: Currently applied magnitude (0-1)
    
    Returns:
        Expected Ψ after intervention
    """
    intervention = get_intervention(level)
    if intervention is None:
        return psi_before
    
    # Total intervention magnitude (additive)
    total_magnitude = current_intervention_magnitude + intervention.psi_reduction
    total_magnitude = min(total_magnitude, 1.0)  # Cap at 1.0
    
    psi_after = psi_before - intervention.psi_reduction
    return max(psi_after, 0.0)


class EDTController:
    """
    Entropy-Driven Throttling Controller
    Maintains Ψ within operational band [0.7, 1.8]
    """
    
    # Operational band
    PSI_MIN_OPERATIONAL = 0.7
    PSI_MAX_OPERATIONAL = 1.8
    PSI_RECOVERY_THRESHOLD = 1.3
    
    def __init__(
        self,
        architecture: str = "transformer_llm",
        psi_l1: float = 1.5,
        psi_l2: float = 1.7,
        psi_l3: float = 1.85,
        psi_critical: float = 2.0,
        update_interval_ms: int = 10,
        auto_recover: bool = True
    ):
        """
        Initialize EDT Controller
        
        Args:
            architecture: Model architecture
            psi_l1: Level 1 threshold (soft)
            psi_l2: Level 2 threshold (medium)
            psi_l3: Level 3 threshold (hard)
            psi_critical: Level 4 threshold (critical)
            update_interval_ms: Control loop update interval (milliseconds)
            auto_recover: Automatically recover when Ψ < recovery threshold
        """
        self.architecture = architecture
        self.thresholds = {
            "l1": psi_l1,
            "l2": psi_l2,
            "l3": psi_l3,
            "critical": psi_critical
        }
        self.update_interval = update_interval_ms / 1000.0
        self.auto_recover = auto_recover
        
        # State
        self.current_level = EDTLevel.NONE
        self.current_psi = 0.0
        self.current_intervention_magnitude = 0.0
        self.is_running = False
        self._thread = None
        self._callbacks: Dict[EDTLevel, list] = {
            level: [] for level in EDTLevel
        }
        
        # Intervention history
        self.history: list = []
        
        # Recovery timer
        self.recovery_start_time: Optional[float] = None
    
    def register_callback(
        self,
        level: EDTLevel,
        callback: Callable[[EDTLevel, EDTIntervention], None]
    ):
        """
        Register callback for when an intervention level is triggered
        
        Args:
            level: EDT level to trigger callback
            callback: Function to call with (level, intervention)
        """
        self._callbacks[level].append(callback)
    
    def _trigger_callbacks(self, level: EDTLevel):
        """Trigger all callbacks for a level"""
        intervention = get_intervention(level)
        if intervention is None:
            return
        
        for callback in self._callbacks[level]:
            try:
                callback(level, intervention)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def update_psi(self, psi: float, timestamp: Optional[float] = None) -> EDTLevel:
        """
        Update current Ψ and determine required intervention
        
        Args:
            psi: Current dissipation coefficient
            timestamp: Current timestamp (seconds)
        
        Returns:
            Required EDT level
        """
        self.current_psi = psi
        
        # Determine required level
        required_level = get_edt_level(
            psi,
            threshold_l1=self.thresholds["l1"],
            threshold_l2=self.thresholds["l2"],
            threshold_l3=self.thresholds["l3"],
            threshold_l4=self.thresholds["critical"]
        )
        
        # Check for recovery
        if self.auto_recover and self.current_level != EDTLevel.NONE:
            if psi < self.PSI_RECOVERY_THRESHOLD:
                if self.recovery_start_time is None:
                    self.recovery_start_time = timestamp or time.time()
                
                # Gradual recovery over 120 seconds
                recovery_duration = 120.0
                elapsed = (timestamp or time.time()) - self.recovery_start_time
                
                if elapsed >= recovery_duration:
                    # Full recovery
                    required_level = EDTLevel.NONE
                    self.recovery_start_time = None
            else:
                # Ψ increased again, cancel recovery
                self.recovery_start_time = None
        else:
            self.recovery_start_time = None
        
        # Handle level changes
        if required_level != self.current_level:
            # Exit old level
            if self.current_level != EDTLevel.NONE:
                self._on_exit_level(self.current_level)
            
            # Enter new level
            if required_level != EDTLevel.NONE:
                self._on_enter_level(required_level)
            
            self.current_level = required_level
        
        # Update intervention magnitude
        intervention = get_intervention(self.current_level)
        if intervention:
            self.current_intervention_magnitude = intervention.psi_reduction
        else:
            self.current_intervention_magnitude = 0.0
        
        # Record history
        self.history.append({
            "timestamp": timestamp or time.time(),
            "psi": psi,
            "level": self.current_level,
            "intervention_magnitude": self.current_intervention_magnitude
        })
        
        # Keep last 1000 entries
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        return self.current_level
    
    def _on_enter_level(self, level: EDTLevel):
        """Called when entering an intervention level"""
        intervention = get_intervention(level)
        if intervention:
            print(f"[EDT] Entering Level {level.value}: {intervention.description}")
            self._trigger_callbacks(level)
    
    def _on_exit_level(self, level: EDTLevel):
        """Called when exiting an intervention level"""
        intervention = get_intervention(level)
        if intervention:
            print(f"[EDT] Exiting Level {level.value}: {intervention.description}")
    
    def get_current_intervention(self) -> Optional[EDTIntervention]:
        """Get currently active intervention"""
        return get_intervention(self.current_level)
    
    def is_intervention_active(self) -> bool:
        """Check if any intervention is active"""
        return self.current_level != EDTLevel.NONE
    
    def get_predicted_psi_after_intervention(self) -> float:
        """Get predicted Ψ after current intervention"""
        return compute_psi_after_intervention(
            self.current_psi,
            self.current_level,
            self.current_intervention_magnitude
        )
    
    def start(self):
        """Start the EDT control loop in background thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self._thread = threading.Thread(target=self._control_loop, daemon=True)
        self._thread.start()
        print("[EDT] Controller started")
    
    def stop(self):
        """Stop the EDT control loop"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print("[EDT] Controller stopped")
    
    def _control_loop(self):
        """Main control loop (runs in background)"""
        while self.is_running:
            # In real implementation, this would read from telemetry
            # For now, just sleep
            time.sleep(self.update_interval)
    
    def get_status(self) -> Dict:
        """Get controller status"""
        return {
            "architecture": self.architecture,
            "current_psi": self.current_psi,
            "current_level": self.current_level,
            "current_intervention": self.get_current_intervention().description if self.get_current_intervention() else None,
            "intervention_magnitude": self.current_intervention_magnitude,
            "predicted_psi": self.get_predicted_psi_after_intervention(),
            "is_active": self.is_intervention_active(),
            "is_running": self.is_running,
            "history_length": len(self.history),
            "thresholds": self.thresholds
        }


# Convenience function
def create_edt_controller(
    architecture: str = "transformer_llm",
    auto_start: bool = False
) -> EDTController:
    """
    Create and optionally start an EDT controller
    
    Args:
        architecture: Model architecture
        auto_start: Automatically start the controller
    
    Returns:
        EDTController instance
    """
    controller = EDTController(architecture=architecture)
    if auto_start:
        controller.start()
    return controller
