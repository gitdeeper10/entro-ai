"""
ENTRO-AI Dynamics Module
Unified dynamics tracker for all systems
"""

import math
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    """Standardized risk levels across all systems"""
    STABLE = 0
    CAUTION = 1
    WARNING = 2
    CRITICAL = 3
    IMMINENT = 4


@dataclass
class DynamicState:
    """Complete dynamic state of a component"""
    # Raw values
    psi_raw: float
    utilization: float
    
    # Normalized values
    psi_norm: float          # [0, 2.0] after normalization
    
    # Derivatives
    dpsi_dt: float           # First derivative (velocity)
    d2psi_dt2: float         # Second derivative (acceleration)
    
    # Risk assessment
    risk_score: float        # Unsaturated risk (can be > 1)
    risk_level: RiskLevel    # Discrete level
    time_to_critical: float  # Seconds until Ψ_norm = 2.0
    
    # Metadata
    timestamp: float
    is_bottleneck: bool = False


class DynamicsTracker:
    """
    Unified dynamics tracker for any system component
    
    Responsibilities:
    - Normalize Ψ values
    - Compute derivatives (velocity, acceleration)
    - Calculate risk scores
    - Maintain history for all components
    """
    
    # Default thresholds (calibrated from Perplexity data)
    DEFAULT_RISK_THRESHOLDS = {
        RiskLevel.CAUTION: 0.3,    # Risk > 0.3 → Caution
        RiskLevel.WARNING: 0.6,    # Risk > 0.6 → Warning
        RiskLevel.CRITICAL: 1.0,   # Risk > 1.0 → Critical
        RiskLevel.IMMINENT: 1.5,   # Risk > 1.5 → Imminent
    }
    
    # Weights for risk calculation
    RISK_WEIGHTS = {
        "position": 1.0,      # Weight for Ψ_norm/2.0
        "velocity": 0.5,      # Weight for |dΨ/dt| × dt
        "acceleration": 0.3,  # Weight for max(0, d²Ψ/dt²) × dt²
    }
    
    def __init__(
        self,
        normalization_method: str = "logistic",
        normalization_reference: float = 10.0,
        risk_thresholds: Optional[Dict[RiskLevel, float]] = None,
        risk_weights: Optional[Dict[str, float]] = None,
        history_size: int = 10
    ):
        """
        Initialize dynamics tracker
        
        Args:
            normalization_method: "logistic", "log", or "linear"
            normalization_reference: Reference value for normalization
            risk_thresholds: Custom risk thresholds
            risk_weights: Custom weights for position/velocity/acceleration
            history_size: Number of historical values to keep
        """
        self.normalization_method = normalization_method
        self.normalization_reference = normalization_reference
        self.risk_thresholds = risk_thresholds or self.DEFAULT_RISK_THRESHOLDS
        self.risk_weights = risk_weights or self.RISK_WEIGHTS
        self.history_size = history_size
        
        # Per-component history
        self._psi_history: Dict[str, List[float]] = {}
        self._timestamp_history: Dict[str, List[float]] = {}
        self._last_state: Dict[str, DynamicState] = {}
    
    def _normalize_psi(self, psi_raw: float) -> float:
        """Normalize raw Ψ to [0, 2.0] range"""
        if self.normalization_method == "logistic":
            # Logistic saturation: 2.0 * (1 - 1/(1 + ψ/ref))
            return 2.0 * (1.0 - 1.0 / (1.0 + psi_raw / self.normalization_reference))
        elif self.normalization_method == "log":
            log_max = math.log(1 + self.normalization_reference * 10)
            return 2.0 * math.log(1 + psi_raw) / log_max
        elif self.normalization_method == "linear":
            scale = self.normalization_reference * 2
            return min(2.0, psi_raw / scale)
        else:
            raise ValueError(f"Unknown normalization: {self.normalization_method}")
    
    def _compute_risk(self, psi_norm: float, dpsi_dt: float, d2psi_dt2: float, dt: float) -> float:
        """
        Compute unsaturated risk score
        
        Risk = position_risk + velocity_contrib + acceleration_contrib
        
        position_risk = (Ψ_norm / 2.0) × weight_position
        velocity_contrib = |dΨ/dt| × dt × weight_velocity
        acceleration_contrib = max(0, d²Ψ/dt²) × dt² × weight_acceleration
        """
        position_risk = (psi_norm / 2.0) * self.risk_weights["position"]
        velocity_contrib = abs(dpsi_dt) * dt * self.risk_weights["velocity"]
        acceleration_contrib = max(0.0, d2psi_dt2) * dt * dt * self.risk_weights["acceleration"]
        
        return position_risk + velocity_contrib + acceleration_contrib
    
    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """Convert risk score to discrete level"""
        if risk_score >= self.risk_thresholds[RiskLevel.IMMINENT]:
            return RiskLevel.IMMINENT
        elif risk_score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_thresholds[RiskLevel.WARNING]:
            return RiskLevel.WARNING
        elif risk_score >= self.risk_thresholds[RiskLevel.CAUTION]:
            return RiskLevel.CAUTION
        else:
            return RiskLevel.STABLE
    
    def _compute_time_to_critical(self, psi_norm: float, dpsi_dt: float) -> float:
        """Seconds until Ψ_norm reaches 2.0"""
        if dpsi_dt <= 0 or psi_norm >= 2.0:
            return float('inf')
        return (2.0 - psi_norm) / max(0.001, dpsi_dt)
    
    def update(
        self,
        component: str,
        psi_raw: float,
        utilization: float,
        timestamp: Optional[float] = None
    ) -> DynamicState:
        """
        Update dynamics for a component
        
        Args:
            component: Component name
            psi_raw: Raw Ψ value (can be very large)
            utilization: Current utilization (0-1)
            timestamp: Current timestamp (seconds)
        
        Returns:
            DynamicState with complete dynamics
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Initialize history for new component
        if component not in self._psi_history:
            self._psi_history[component] = []
            self._timestamp_history[component] = []
        
        # Normalize Ψ
        psi_norm = self._normalize_psi(psi_raw)
        
        # Store in history
        self._psi_history[component].append(psi_norm)
        self._timestamp_history[component].append(timestamp)
        
        # Trim history
        if len(self._psi_history[component]) > self.history_size:
            self._psi_history[component] = self._psi_history[component][-self.history_size:]
            self._timestamp_history[component] = self._timestamp_history[component][-self.history_size:]
        
        # Calculate derivatives
        dpsi_dt = 0.0
        d2psi_dt2 = 0.0
        dt = 1.0
        
        if len(self._psi_history[component]) >= 2:
            prev_psi = self._psi_history[component][-2]
            prev_time = self._timestamp_history[component][-2]
            dt = max(0.001, timestamp - prev_time)
            dpsi_dt = (psi_norm - prev_psi) / dt
            
            # Second derivative
            if len(self._psi_history[component]) >= 3:
                prev_prev_psi = self._psi_history[component][-3]
                prev_prev_time = self._timestamp_history[component][-3]
                dt_prev = max(0.001, prev_time - prev_prev_time)
                dpsi_dt_prev = (prev_psi - prev_prev_psi) / dt_prev
                d2psi_dt2 = (dpsi_dt - dpsi_dt_prev) / dt
        
        # Compute risk
        risk_score = self._compute_risk(psi_norm, dpsi_dt, d2psi_dt2, dt)
        risk_level = self._get_risk_level(risk_score)
        time_to_critical = self._compute_time_to_critical(psi_norm, dpsi_dt)
        
        state = DynamicState(
            psi_raw=psi_raw,
            utilization=utilization,
            psi_norm=psi_norm,
            dpsi_dt=dpsi_dt,
            d2psi_dt2=d2psi_dt2,
            risk_score=risk_score,
            risk_level=risk_level,
            time_to_critical=time_to_critical,
            timestamp=timestamp
        )
        
        self._last_state[component] = state
        return state
    
    def get_state(self, component: str) -> Optional[DynamicState]:
        """Get last known state for a component"""
        return self._last_state.get(component)
    
    def get_all_states(self) -> Dict[str, DynamicState]:
        """Get all component states"""
        return self._last_state.copy()
    
    def get_bottleneck(self) -> Optional[str]:
        """Identify bottleneck component (highest risk score)"""
        if not self._last_state:
            return None
        return max(self._last_state.keys(), key=lambda c: self._last_state[c].risk_score)
    
    def reset(self, component: Optional[str] = None):
        """Reset history for a component or all"""
        if component:
            self._psi_history.pop(component, None)
            self._timestamp_history.pop(component, None)
            self._last_state.pop(component, None)
        else:
            self._psi_history.clear()
            self._timestamp_history.clear()
            self._last_state.clear()


# Factory function
def create_tracker(
    normalization_reference: float = 10.0,
    caution_threshold: float = 0.3,
    warning_threshold: float = 0.6,
    critical_threshold: float = 1.0,
    imminent_threshold: float = 1.5
) -> DynamicsTracker:
    """Create a configured dynamics tracker"""
    thresholds = {
        RiskLevel.CAUTION: caution_threshold,
        RiskLevel.WARNING: warning_threshold,
        RiskLevel.CRITICAL: critical_threshold,
        RiskLevel.IMMINENT: imminent_threshold,
    }
    return DynamicsTracker(risk_thresholds=thresholds)


if __name__ == "__main__":
    # Test the unified tracker
    tracker = create_tracker()
    
    print("=== UNIFIED DYNAMICS TRACKER TEST ===")
    print()
    
    # Simulate scraper overload
    for util in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97, 0.98]:
        # Simulate Ψ_raw (simplified model)
        psi_raw = 10.0 * (util / (1.0 - util)) ** 1.63
        
        state = tracker.update("scraper", psi_raw, util)
        
        print(f"util={util:.2f} | Ψ_norm={state.psi_norm:.3f} | dΨ/dt={state.dpsi_dt:+.3f} | risk={state.risk_score:.3f} | level={state.risk_level.name}")
    
    print()
    print(f"Bottleneck: {tracker.get_bottleneck()}")

    def update(
        self,
        component: str,
        psi_raw: float,
        utilization: float,
        timestamp: Optional[float] = None
    ) -> DynamicState:
        """
        Update dynamics for a component
        
        Args:
            component: Component name
            psi_raw: Raw Ψ value (can be very large)
            utilization: Current utilization (0-1)
            timestamp: Current timestamp (seconds)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Initialize history for new component
        if component not in self._psi_history:
            self._psi_history[component] = []
            self._timestamp_history[component] = []
        
        # Normalize Ψ
        psi_norm = self._normalize_psi(psi_raw)
        
        # Store in history
        self._psi_history[component].append(psi_norm)
        self._timestamp_history[component].append(timestamp)
        
        # Trim history
        if len(self._psi_history[component]) > self.history_size:
            self._psi_history[component] = self._psi_history[component][-self.history_size:]
            self._timestamp_history[component] = self._timestamp_history[component][-self.history_size:]
        
        # Calculate derivatives with MINIMUM DT
        dpsi_dt = 0.0
        d2psi_dt2 = 0.0
        dt = 1.0
        
        if len(self._psi_history[component]) >= 2:
            prev_psi = self._psi_history[component][-2]
            prev_time = self._timestamp_history[component][-2]
            raw_dt = timestamp - prev_time
            
            # Minimum dt of 0.5 seconds to avoid unrealistic spikes
            dt = max(0.5, raw_dt)
            dpsi_dt = (psi_norm - prev_psi) / dt
            
            # Cap dΨ/dt at reasonable values
            dpsi_dt = max(-5.0, min(5.0, dpsi_dt))
            
            # Second derivative
            if len(self._psi_history[component]) >= 3:
                prev_prev_psi = self._psi_history[component][-3]
                prev_prev_time = self._timestamp_history[component][-3]
                raw_dt_prev = max(0.5, prev_time - prev_prev_time)
                dpsi_dt_prev = (prev_psi - prev_prev_psi) / raw_dt_prev
                dpsi_dt_prev = max(-5.0, min(5.0, dpsi_dt_prev))
                d2psi_dt2 = (dpsi_dt - dpsi_dt_prev) / dt
                d2psi_dt2 = max(-2.0, min(2.0, d2psi_dt2))
        
        # Compute risk
        risk_score = self._compute_risk(psi_norm, dpsi_dt, d2psi_dt2, dt)
        risk_level = self._get_risk_level(risk_score)
        time_to_critical = self._compute_time_to_critical(psi_norm, dpsi_dt)
        
        state = DynamicState(
            psi_raw=psi_raw,
            utilization=utilization,
            psi_norm=psi_norm,
            dpsi_dt=dpsi_dt,
            d2psi_dt2=d2psi_dt2,
            risk_score=risk_score,
            risk_level=risk_level,
            time_to_critical=time_to_critical,
            timestamp=timestamp
        )
        
        self._last_state[component] = state
        return state

    def _get_adaptive_risk_level(
        self, 
        risk_score: float, 
        dpsi_dt: float,
        d2psi_dt2: float
    ) -> RiskLevel:
        """
        Adaptive risk level based on rate of change
        
        إذا كان التغير سريعًا → تشديد العتبات
        إذا كان التغير بطيئًا → عتبات طبيعية
        """
        # Calculate adaptive factor based on velocity
        # dpsi_dt > 0.5 → fast change → tighten thresholds
        # dpsi_dt < 0.1 → slow change → normal thresholds
        adaptive_factor = 1.0
        
        if dpsi_dt > 0.5:
            # Fast change: reduce thresholds by 20%
            adaptive_factor = 0.8
        elif dpsi_dt < 0.1:
            # Slow change: normal thresholds
            adaptive_factor = 1.0
        else:
            # Linear interpolation
            adaptive_factor = 1.0 - (dpsi_dt - 0.1) * 0.5
        
        # Apply adaptive factor to thresholds
        adapted_thresholds = {
            RiskLevel.CAUTION: self.risk_thresholds[RiskLevel.CAUTION] * adaptive_factor,
            RiskLevel.WARNING: self.risk_thresholds[RiskLevel.WARNING] * adaptive_factor,
            RiskLevel.CRITICAL: self.risk_thresholds[RiskLevel.CRITICAL] * adaptive_factor,
            RiskLevel.IMMINENT: self.risk_thresholds[RiskLevel.IMMINENT] * adaptive_factor,
        }
        
        # Determine level with adapted thresholds
        if risk_score >= adapted_thresholds[RiskLevel.IMMINENT]:
            return RiskLevel.IMMINENT
        elif risk_score >= adapted_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= adapted_thresholds[RiskLevel.WARNING]:
            return RiskLevel.WARNING
        elif risk_score >= adapted_thresholds[RiskLevel.CAUTION]:
            return RiskLevel.CAUTION
        else:
            return RiskLevel.STABLE
    
    def update(
        self,
        component: str,
        psi_raw: float,
        utilization: float,
        timestamp: Optional[float] = None
    ) -> DynamicState:
        """
        Update dynamics for a component with ADAPTIVE thresholds
        """
        # ... (previous code remains the same until risk calculation) ...
        
        # Re-implement the core update with adaptive logic
        if timestamp is None:
            timestamp = time.time()
        
        if component not in self._psi_history:
            self._psi_history[component] = []
            self._timestamp_history[component] = []
        
        psi_norm = self._normalize_psi(psi_raw)
        
        self._psi_history[component].append(psi_norm)
        self._timestamp_history[component].append(timestamp)
        
        if len(self._psi_history[component]) > self.history_size:
            self._psi_history[component] = self._psi_history[component][-self.history_size:]
            self._timestamp_history[component] = self._timestamp_history[component][-self.history_size:]
        
        # Calculate derivatives
        dpsi_dt = 0.0
        d2psi_dt2 = 0.0
        dt = 1.0
        
        if len(self._psi_history[component]) >= 2:
            prev_psi = self._psi_history[component][-2]
            prev_time = self._timestamp_history[component][-2]
            raw_dt = timestamp - prev_time
            dt = max(0.5, raw_dt)
            dpsi_dt = (psi_norm - prev_psi) / dt
            dpsi_dt = max(-5.0, min(5.0, dpsi_dt))
            
            if len(self._psi_history[component]) >= 3:
                prev_prev_psi = self._psi_history[component][-3]
                prev_prev_time = self._timestamp_history[component][-3]
                raw_dt_prev = max(0.5, prev_time - prev_prev_time)
                dpsi_dt_prev = (prev_psi - prev_prev_psi) / raw_dt_prev
                dpsi_dt_prev = max(-5.0, min(5.0, dpsi_dt_prev))
                d2psi_dt2 = (dpsi_dt - dpsi_dt_prev) / dt
                d2psi_dt2 = max(-2.0, min(2.0, d2psi_dt2))
        
        # Compute risk score
        risk_score = self._compute_risk(psi_norm, dpsi_dt, d2psi_dt2, dt)
        
        # ADAPTIVE risk level (new!)
        risk_level = self._get_adaptive_risk_level(risk_score, dpsi_dt, d2psi_dt2)
        
        time_to_critical = self._compute_time_to_critical(psi_norm, dpsi_dt)
        
        state = DynamicState(
            psi_raw=psi_raw,
            utilization=utilization,
            psi_norm=psi_norm,
            dpsi_dt=dpsi_dt,
            d2psi_dt2=d2psi_dt2,
            risk_score=risk_score,
            risk_level=risk_level,
            time_to_critical=time_to_critical,
            timestamp=timestamp
        )
        
        self._last_state[component] = state
        return state

