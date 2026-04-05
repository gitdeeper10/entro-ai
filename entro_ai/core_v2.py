"""
ENTRO-AI v2.0.0
General Theory of Computational System Stability
Builds on ENTROPIA (E-LAB-01) · DOI: 10.5281/zenodo.19416737

Key Changes:
- Ψ as vector (not scalar)
- dΨ/dt mandatory
- V_eff as min of ALL constraints
- Distributed EDT support
"""

import math
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CollapseRisk(Enum):
    """Collapse risk level"""
    STABLE = "stable"
    WARNING = "warning"
    CRITICAL = "critical"
    IMMINENT = "imminent"


@dataclass
class ComponentStress:
    """Stress state of a single system component"""
    name: str
    psi: float                    # Current stress (0-∞)
    dpsi_dt: float                # Rate of change (per second)
    veff: float                   # Effective capacity
    utilization: float            # Current utilization (0-1)
    is_bottleneck: bool = False   # Is this the bottleneck?
    
    def distance_to_critical(self, psi_c: float = 2.0) -> float:
        """Distance to critical threshold"""
        return max(0, psi_c - self.psi)
    
    def time_to_critical(self, psi_c: float = 2.0) -> float:
        """Time until critical threshold (seconds)"""
        if self.dpsi_dt <= 0:
            return float('inf')
        return (psi_c - self.psi) / self.dpsi_dt
    
    def risk_level(self, psi_c: float = 2.0) -> CollapseRisk:
        """Determine risk level"""
        if self.psi >= psi_c:
            return CollapseRisk.IMMINENT
        elif self.psi >= psi_c * 0.9:
            return CollapseRisk.CRITICAL
        elif self.psi >= psi_c * 0.75:
            return CollapseRisk.WARNING
        else:
            return CollapseRisk.STABLE


@dataclass
class SystemStressVector:
    """
    Stress state of entire system as vector
    Ψ = (Ψ₁, Ψ₂, ..., Ψₙ) for n components
    """
    components: Dict[str, ComponentStress]
    timestamp: float
    bottleneck: Optional[str] = None
    overall_risk: CollapseRisk = CollapseRisk.STABLE
    
    def __post_init__(self):
        # Identify bottleneck (component with highest Ψ)
        if self.components:
            self.bottleneck = max(
                self.components.keys(),
                key=lambda k: self.components[k].psi
            )
            # Mark bottleneck
            if self.bottleneck:
                self.components[self.bottleneck].is_bottleneck = True
        
        # Determine overall risk
        max_psi = max((c.psi for c in self.components.values()), default=0)
        if max_psi >= 2.0:
            self.overall_risk = CollapseRisk.IMMINENT
        elif max_psi >= 1.8:
            self.overall_risk = CollapseRisk.CRITICAL
        elif max_psi >= 1.5:
            self.overall_risk = CollapseRisk.WARNING
        else:
            self.overall_risk = CollapseRisk.STABLE
    
    def max_psi(self) -> float:
        """Maximum Ψ across all components"""
        return max((c.psi for c in self.components.values()), default=0)
    
    def min_time_to_critical(self) -> float:
        """Minimum time to critical across all components"""
        return min((c.time_to_critical() for c in self.components.values()), default=float('inf'))
    
    def get_bottleneck_stress(self) -> Optional[ComponentStress]:
        """Get stress state of bottleneck component"""
        if self.bottleneck:
            return self.components.get(self.bottleneck)
        return None


@dataclass
class SystemTopology:
    """Topology of the information processing system"""
    name: str
    components: List[str]
    dependencies: Dict[str, List[str]]  # component -> list of dependencies
    parallel_paths: List[List[str]]      # independent parallel paths
    
    def get_downstream(self, component: str) -> List[str]:
        """Get components that depend on this component"""
        downstream = []
        for comp, deps in self.dependencies.items():
            if component in deps:
                downstream.append(comp)
        return downstream
    
    def get_upstream(self, component: str) -> List[str]:
        """Get components this component depends on"""
        return self.dependencies.get(component, [])


def compute_veff_general(constraints: Dict[str, float]) -> float:
    """
    General V_eff calculation for any system
    
    V_eff = min(constraints)
    
    Args:
        constraints: Dictionary of constraint name -> capacity
    
    Returns:
        Minimum capacity (bottleneck)
    """
    if not constraints:
        return float('inf')
    return min(constraints.values())


def compute_psi_component(
    utilization: float,
    veff_ratio: float = 1.0,
    scaling_exponent: float = 1.63
) -> float:
    """
    Compute Ψ for a single component
    
    Simplified model: Ψ ≈ utilization^scaling_exponent / (1 - utilization)
    
    Args:
        utilization: Current utilization (0-1)
        veff_ratio: V_eff / V_eff_max
        scaling_exponent: Architecture-specific n
    
    Returns:
        Ψ value (0-∞)
    """
    if utilization >= 0.99:
        return float('inf')
    
    # Avoid division by zero
    safe_util = min(utilization, 0.99)
    
    # Ψ grows super-linearly near capacity
    psi = (safe_util ** scaling_exponent) / (1.0 - safe_util)
    
    # Adjust for V_eff degradation
    psi = psi / max(0.1, veff_ratio)
    
    return psi


class GeneralSystemMonitor:
    """
    General monitor for ANY information processing system
    Supports arbitrary component hierarchies and topologies
    """
    
    # Default critical threshold (from ENTROPIA)
    PSI_CRITICAL = 2.0
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        CollapseRisk.WARNING: 1.5,
        CollapseRisk.CRITICAL: 1.8,
        CollapseRisk.IMMINENT: 2.0
    }
    
    def __init__(
        self,
        system_name: str,
        components: List[str],
        topology: Optional[SystemTopology] = None,
        scaling_exponents: Optional[Dict[str, float]] = None
    ):
        """
        Initialize general system monitor
        
        Args:
            system_name: Name of the system
            components: List of component names
            topology: System topology (dependencies, parallel paths)
            scaling_exponents: Per-component scaling exponents (default 1.63)
        """
        self.system_name = system_name
        self.components = components
        self.topology = topology
        self.scaling_exponents = scaling_exponents or {c: 1.63 for c in components}
        
        # Component state
        self._component_utilization: Dict[str, float] = {}
        self._component_veff: Dict[str, float] = {}
        self._last_psi: Dict[str, float] = {}
        self._last_time: float = 0.0
        
        # History
        self.history: List[SystemStressVector] = []
    
    def update_component(
        self,
        component: str,
        utilization: float,
        veff_ratio: float = 1.0,
        timestamp: Optional[float] = None
    ):
        """Update utilization for a single component"""
        if component not in self.components:
            raise ValueError(f"Unknown component: {component}")
        
        self._component_utilization[component] = utilization
        self._component_veff[component] = veff_ratio
    
    def get_component_psi(self, component: str, timestamp: float) -> Tuple[float, float]:
        """
        Get Ψ and dΨ/dt for a component
        
        Returns:
            (psi, dpsi_dt)
        """
        if component not in self.components:
            return 0.0, 0.0
        
        util = self._component_utilization.get(component, 0.0)
        veff_ratio = self._component_veff.get(component, 1.0)
        n = self.scaling_exponents.get(component, 1.63)
        
        psi = compute_psi_component(util, veff_ratio, n)
        
        # Calculate derivative
        dpsi_dt = 0.0
        if timestamp > 0 and component in self._last_psi:
            dt = timestamp - self._last_time
            if dt > 0:
                dpsi_dt = (psi - self._last_psi[component]) / dt
        
        return psi, dpsi_dt
    
    def get_system_state(self, timestamp: Optional[float] = None) -> SystemStressVector:
        """
        Get complete system stress vector
        
        Returns:
            SystemStressVector with Ψ for all components
        """
        if timestamp is None:
            timestamp = time.time()
        
        components_stress = {}
        
        for component in self.components:
            psi, dpsi_dt = self.get_component_psi(component, timestamp)
            
            components_stress[component] = ComponentStress(
                name=component,
                psi=psi,
                dpsi_dt=dpsi_dt,
                veff=self._component_veff.get(component, 1.0),
                utilization=self._component_utilization.get(component, 0.0)
            )
        
        # Save for next derivative calculation
        self._last_psi = {c: components_stress[c].psi for c in self.components}
        self._last_time = timestamp
        
        state = SystemStressVector(
            components=components_stress,
            timestamp=timestamp
        )
        
        # Store history
        self.history.append(state)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        return state
    
    def get_bottleneck(self) -> Optional[str]:
        """Get current bottleneck component"""
        state = self.get_system_state()
        return state.bottleneck
    
    def predict_collapse(self, horizon_seconds: float = 60.0) -> Dict:
        """
        Predict collapse within time horizon
        
        Returns:
            Dictionary with predictions
        """
        state = self.get_system_state()
        
        predictions = {}
        for component, stress in state.components.items():
            ttc = stress.time_to_critical()
            predictions[component] = {
                "psi": stress.psi,
                "time_to_critical": ttc,
                "will_collapse": ttc <= horizon_seconds,
                "risk_level": stress.risk_level().value
            }
        
        # Overall prediction
        min_ttc = min((p["time_to_critical"] for p in predictions.values()), default=float('inf'))
        
        return {
            "horizon_seconds": horizon_seconds,
            "will_collapse": min_ttc <= horizon_seconds,
            "time_to_collapse": min_ttc if min_ttc != float('inf') else None,
            "bottleneck": state.bottleneck,
            "component_predictions": predictions
        }


# Example: Perplexity AI configuration
PERPLEXITY_CONFIG = {
    "system_name": "Perplexity AI",
    "components": ["search", "scraper", "llm", "routing", "citation", "latency"],
    "topology": SystemTopology(
        name="Perplexity Pipeline",
        components=["search", "scraper", "llm", "routing", "citation", "latency"],
        dependencies={
            "search": [],
            "scraper": ["search"],
            "llm": ["scraper"],
            "routing": ["llm"],
            "citation": ["llm", "routing"],
            "latency": ["search", "scraper", "llm", "routing", "citation"]
        },
        parallel_paths=[["search", "scraper", "llm"], ["routing", "citation"]]
    ),
    "scaling_exponents": {
        "search": 1.65,
        "scraper": 1.70,
        "llm": 1.63,
        "routing": 1.55,
        "citation": 1.60,
        "latency": 1.75
    }
}


def create_perplexity_monitor() -> GeneralSystemMonitor:
    """Create a monitor configured for Perplexity AI"""
    return GeneralSystemMonitor(
        system_name=PERPLEXITY_CONFIG["system_name"],
        components=PERPLEXITY_CONFIG["components"],
        topology=PERPLEXITY_CONFIG["topology"],
        scaling_exponents=PERPLEXITY_CONFIG["scaling_exponents"]
    )


if __name__ == "__main__":
    # Test with Perplexity configuration
    monitor = create_perplexity_monitor()
    
    # Simulate scraper overload (Perplexity's critical incident)
    monitor.update_component("search", 0.75)
    monitor.update_component("scraper", 0.98)  # ← bottleneck
    monitor.update_component("llm", 0.70)
    monitor.update_component("routing", 0.65)
    monitor.update_component("citation", 0.60)
    monitor.update_component("latency", 0.80)
    
    state = monitor.get_system_state()
    predictions = monitor.predict_collapse(horizon_seconds=60)
    
    print("=" * 60)
    print(f"System: {monitor.system_name}")
    print("=" * 60)
    
    print("\nComponent Stress Vector (Ψ):")
    for component, stress in state.components.items():
        marker = "🔴 BOTTLENECK" if stress.is_bottleneck else ""
        print(f"  {component:12} | Ψ={stress.psi:.3f} | dΨ/dt={stress.dpsi_dt:+.3f} | {stress.utilization*100:.0f}% {marker}")
    
    print(f"\nBottleneck: {state.bottleneck}")
    print(f"Overall Risk: {state.overall_risk.value}")
    print(f"Time to collapse: {predictions['time_to_collapse']:.1f}s" if predictions['time_to_collapse'] else "No imminent collapse")

# ============================================================
# Ψ NORMALIZATION (Critical for cross-system comparison)
# ============================================================

def normalize_psi(
    psi_raw: float,
    method: str = "logistic",
    reference: float = 10.0,
    psi_c: float = 2.0
) -> float:
    """
    Normalize raw Ψ to comparable scale [0, psi_c]
    
    Methods:
        - "logistic": 2.0 * (1 - 1/(1 + psi_raw/reference))
        - "log": log(1 + psi_raw) / log(1 + max_expected)
        - "linear": min(psi_c, psi_raw / scale)
    
    Args:
        psi_raw: Raw Ψ value (can be very large)
        method: Normalization method
        reference: Reference value for logistic method
        psi_c: Critical threshold (default 2.0)
    
    Returns:
        Normalized Ψ in [0, psi_c]
    """
    if method == "logistic":
        # Logistic function: saturates at psi_c
        # Ψ_norm = psi_c * (1 - 1/(1 + ψ/ref))
        return psi_c * (1.0 - 1.0 / (1.0 + psi_raw / reference))
    
    elif method == "log":
        # Logarithmic compression
        max_expected = reference * 10
        log_max = math.log(1 + max_expected)
        return psi_c * math.log(1 + psi_raw) / log_max
    
    elif method == "linear":
        # Simple linear scaling with saturation
        scale = reference * 2
        return min(psi_c, psi_raw / scale)
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def psi_to_risk_level(
    psi_norm: float,
    psi_c: float = 2.0,
    thresholds: Dict[str, float] = None
) -> Tuple[CollapseRisk, str]:
    """
    Convert normalized Ψ to risk level with description
    
    Args:
        psi_norm: Normalized Ψ (0 to psi_c)
        psi_c: Critical threshold
        thresholds: Custom thresholds (warning, critical, imminent)
    
    Returns:
        (CollapseRisk, description)
    """
    if thresholds is None:
        thresholds = {
            "warning": 1.5,
            "critical": 1.8,
            "imminent": 2.0
        }
    
    if psi_norm >= thresholds["imminent"]:
        return CollapseRisk.IMMINENT, "⚠️ IMMINENT COLLAPSE - Immediate action required"
    elif psi_norm >= thresholds["critical"]:
        return CollapseRisk.CRITICAL, "🔴 CRITICAL - System near breaking point"
    elif psi_norm >= thresholds["warning"]:
        return CollapseRisk.WARNING, "🟡 WARNING - Stress elevated, monitor closely"
    else:
        return CollapseRisk.STABLE, "🟢 STABLE - Normal operation"


# تحديث ComponentStress ليشمل Ψ_norm
@dataclass
class ComponentStressNormalized(ComponentStress):
    """Component stress with normalized Ψ for cross-system comparison"""
    psi_raw: float = 0.0
    psi_norm: float = 0.0
    normalization_method: str = "logistic"
    
    def __post_init__(self):
        # Compute normalized Ψ
        self.psi_norm = normalize_psi(self.psi_raw, method=self.normalization_method)


def create_normalized_perplexity_monitor() -> GeneralSystemMonitor:
    """Create Perplexity monitor with Ψ normalization"""
    monitor = create_perplexity_monitor()
    
    # Override the get_system_state method to include normalized Ψ
    original_get_state = monitor.get_system_state
    
    def get_state_with_normalization(timestamp=None):
        state = original_get_state(timestamp)
        
        # Add normalized Ψ to each component
        for component, stress in state.components.items():
            stress.psi_raw = stress.psi
            stress.psi_norm = normalize_psi(stress.psi_raw, method="logistic")
        
        return state
    
    monitor.get_system_state = get_state_with_normalization
    return monitor


# اختبار التطبيع
if __name__ == "__main__" and "test_normalization" in locals():
    print("\n=== Ψ NORMALIZATION TEST ===")
    test_values = [0.5, 1.0, 1.9, 2.5, 5.0, 10.0, 20.0, 48.3, 100.0]
    
    print(f"{'Ψ_raw':>10} | {'Logistic':>10} | {'Log':>10} | {'Linear':>10} | {'Risk':>10}")
    print("-" * 55)
    
    for psi_raw in test_values:
        psi_logistic = normalize_psi(psi_raw, method="logistic", reference=10.0)
        psi_log = normalize_psi(psi_raw, method="log", reference=10.0)
        psi_linear = normalize_psi(psi_raw, method="linear", reference=10.0)
        risk, _ = psi_to_risk_level(psi_logistic)
        
        print(f"{psi_raw:10.1f} | {psi_logistic:10.3f} | {psi_log:10.3f} | {psi_linear:10.3f} | {risk.value:10}")

# ============================================================
# DYNAMIC RISK: Position + Velocity
# ============================================================

@dataclass
class DynamicRisk:
    """Dynamic risk combining position (Ψ_norm) and velocity (dΨ/dt)"""
    psi_norm: float          # Position in stability space [0, 2.0]
    dpsi_dt: float           # Velocity (change per second)
    risk_score: float        # Combined risk [0, 1]
    risk_level: CollapseRisk
    time_to_critical: float  # Seconds until Ψ_norm reaches 2.0
    is_accelerating: bool    # d²Ψ/dt² > 0


def compute_dynamic_risk(
    psi_norm: float,
    dpsi_dt: float,
    psi_c: float = 2.0,
    dt_history: List[float] = None
) -> DynamicRisk:
    """
    Compute dynamic risk from position and velocity
    
    Risk = (Ψ_norm/Ψ_c) * (1 + α * |dΨ/dt| * Δt)
    
    حيث α عامل حساسية للسرعة
    
    Args:
        psi_norm: Normalized Ψ [0, psi_c]
        dpsi_dt: Rate of change (per second)
        psi_c: Critical threshold
        dt_history: Historical dΨ/dt values for acceleration detection
    
    Returns:
        DynamicRisk with combined assessment
    """
    # Base risk from position
    position_risk = psi_norm / psi_c
    
    # Velocity multiplier (faster change = higher risk)
    # α = 0.5 means that dΨ/dt = 0.1 adds 5% to risk
    alpha = 0.5
    velocity_factor = 1.0 + alpha * abs(dpsi_dt) * 1.0  # Δt=1s assumed
    
    # Combined risk (capped at 1.0)
    risk_score = min(1.0, position_risk * velocity_factor)
    
    # Time to critical (if moving toward it)
    time_to_critical = float('inf')
    if dpsi_dt > 0 and psi_norm < psi_c:
        time_to_critical = (psi_c - psi_norm) / max(0.001, dpsi_dt)
    
    # Check for acceleration (if history provided)
    is_accelerating = False
    if dt_history and len(dt_history) >= 2:
        # d²Ψ/dt² > 0 means acceleration toward collapse
        d2psi_dt2 = dt_history[-1] - dt_history[-2]
        is_accelerating = d2psi_dt2 > 0.01  # Threshold for significance
    
    # Determine risk level
    if risk_score >= 0.9 or (psi_norm >= psi_c * 0.9 and dpsi_dt > 0):
        risk_level = CollapseRisk.IMMINENT
    elif risk_score >= 0.7 or (psi_norm >= psi_c * 0.8 and dpsi_dt > 0):
        risk_level = CollapseRisk.CRITICAL
    elif risk_score >= 0.4:
        risk_level = CollapseRisk.WARNING
    else:
        risk_level = CollapseRisk.STABLE
    
    return DynamicRisk(
        psi_norm=psi_norm,
        dpsi_dt=dpsi_dt,
        risk_score=risk_score,
        risk_level=risk_level,
        time_to_critical=time_to_critical,
        is_accelerating=is_accelerating
    )


def risk_to_edt_level(dynamic_risk: DynamicRisk) -> int:
    """
    Convert dynamic risk to EDT intervention level
    
    Args:
        dynamic_risk: DynamicRisk object
    
    Returns:
        EDT level (0-4)
    """
    # Imminent collapse → Level 4
    if dynamic_risk.risk_level == CollapseRisk.IMMINENT:
        return 4
    
    # Critical + accelerating → Level 3
    if dynamic_risk.risk_level == CollapseRisk.CRITICAL:
        if dynamic_risk.is_accelerating or dynamic_risk.time_to_critical < 30:
            return 3
        return 2
    
    # Warning → Level 1 or 2 based on velocity
    if dynamic_risk.risk_level == CollapseRisk.WARNING:
        if dynamic_risk.dpsi_dt > 0.05:
            return 2
        return 1
    
    # Stable → No intervention
    return 0


# تحديث ComponentStressNormalized ليشمل dynamic risk
@dataclass
class ComponentStressWithDynamics(ComponentStressNormalized):
    """Component stress with dynamic risk assessment"""
    dynamic_risk: Optional[DynamicRisk] = None
    dpsi_dt_history: List[float] = field(default_factory=list)
    
    def update_dynamics(self, timestamp: float, last_timestamp: Optional[float] = None):
        """Update dynamic risk based on time delta"""
        if last_timestamp and timestamp > last_timestamp:
            dt = timestamp - last_timestamp
            if dt > 0 and len(self.dpsi_dt_history) > 0:
                # Calculate current dΨ/dt
                current_dpsi_dt = (self.psi_norm - self.dpsi_dt_history[-1]) / dt
                self.dpsi_dt_history.append(current_dpsi_dt)
                
                # Keep last 10 values
                if len(self.dpsi_dt_history) > 10:
                    self.dpsi_dt_history = self.dpsi_dt_history[-10:]
                
                # Compute dynamic risk
                self.dynamic_risk = compute_dynamic_risk(
                    psi_norm=self.psi_norm,
                    dpsi_dt=current_dpsi_dt,
                    dt_history=self.dpsi_dt_history
                )


def create_dynamic_perplexity_monitor() -> GeneralSystemMonitor:
    """Create Perplexity monitor with dynamic risk assessment"""
    from entro_ai.core_v2 import create_perplexity_monitor
    
    monitor = create_perplexity_monitor()
    
    # Store history for each component
    monitor._psi_history = {}
    monitor._last_timestamp = 0
    
    original_get_state = monitor.get_system_state
    
    def get_state_with_dynamics(timestamp=None):
        import time
        if timestamp is None:
            timestamp = time.time()
        
        state = original_get_state(timestamp)
        
        # Add dynamics to each component
        for component, stress in state.components.items():
            if component not in monitor._psi_history:
                monitor._psi_history[component] = []
            
            # Store normalized Ψ history
            psi_norm = normalize_psi(stress.psi, method="logistic", reference=10.0)
            monitor._psi_history[component].append(psi_norm)
            
            # Keep last 10 values
            if len(monitor._psi_history[component]) > 10:
                monitor._psi_history[component] = monitor._psi_history[component][-10:]
            
            # Calculate dΨ/dt
            dpsi_dt = 0.0
            if len(monitor._psi_history[component]) >= 2 and monitor._last_timestamp > 0:
                dt = timestamp - monitor._last_timestamp
                if dt > 0:
                    dpsi_dt = (psi_norm - monitor._psi_history[component][-2]) / dt
            
            # Compute dynamic risk
            dynamic_risk = compute_dynamic_risk(
                psi_norm=psi_norm,
                dpsi_dt=dpsi_dt,
                dt_history=monitor._psi_history[component]
            )
            
            # Attach to stress object
            stress.dynamic_risk = dynamic_risk
            stress.dpsi_dt = dpsi_dt
        
        monitor._last_timestamp = timestamp
        return state
    
    monitor.get_system_state = get_state_with_dynamics
    return monitor

# ============================================================
# ENHANCED DYNAMIC RISK WITH ACCELERATION
# ============================================================

@dataclass
class EnhancedDynamicRisk:
    """Enhanced dynamic risk with acceleration and unsaturating risk"""
    psi_norm: float              # Position [0, 2.0]
    dpsi_dt: float               # Velocity (change per second)
    d2psi_dt2: float             # Acceleration (change of velocity)
    risk_score: float            # Unsaturated risk (0 to ∞)
    risk_normalized: float       # Normalized risk [0, 1] for display
    time_to_critical: float      # Seconds until Ψ_norm reaches 2.0
    is_accelerating: bool        # d²Ψ/dt² > threshold
    edt_level: int               # Direct EDT level (0-4)
    description: str             # Human-readable description


def compute_enhanced_risk(
    psi_norm: float,
    dpsi_dt: float,
    d2psi_dt2: float = 0.0,
    psi_c: float = 2.0,
    dt: float = 1.0,
    alpha: float = 0.5,      # وزن السرعة
    beta: float = 0.3        # وزن التسارع
) -> EnhancedDynamicRisk:
    """
    Compute enhanced dynamic risk with acceleration
    
    Risk = (Ψ_norm/Ψ_c) × (1 + α×|dΨ/dt|×Δt + β×max(0, d²Ψ/dt²)×Δt²)
    
    Args:
        psi_norm: Normalized Ψ [0, psi_c]
        dpsi_dt: Velocity (change per second)
        d2psi_dt2: Acceleration (change of velocity)
        psi_c: Critical threshold
        dt: Time delta (seconds)
        alpha: Velocity weight
        beta: Acceleration weight (only positive acceleration matters)
    
    Returns:
        EnhancedDynamicRisk with unsaturated risk
    """
    # Base risk from position
    position_risk = psi_norm / psi_c
    
    # Velocity contribution (always positive, absolute value)
    velocity_contrib = alpha * abs(dpsi_dt) * dt
    
    # Acceleration contribution (only positive acceleration increases risk)
    acceleration_contrib = 0.0
    is_accelerating = False
    if d2psi_dt2 > 0:
        acceleration_contrib = beta * d2psi_dt2 * dt * dt
        is_accelerating = True
    
    # Unsaturated risk (can be > 1.0)
    risk_score = position_risk * (1.0 + velocity_contrib + acceleration_contrib)
    
    # Normalized risk for display (saturates at 1.0 for UI)
    risk_normalized = min(1.0, risk_score / (1.0 + alpha * 2.0 + beta * 2.0))
    
    # Time to critical (if moving toward it)
    time_to_critical = float('inf')
    if dpsi_dt > 0 and psi_norm < psi_c:
        time_to_critical = (psi_c - psi_norm) / max(0.001, dpsi_dt)
    
    # EDT level based on unsaturated risk
    if risk_score >= 3.0:
        edt_level = 4
        description = "⚠️ IMMINENT COLLAPSE - Critical acceleration detected"
    elif risk_score >= 2.0:
        edt_level = 3
        description = "🔴 CRITICAL - Rapid deterioration"
    elif risk_score >= 1.2:
        edt_level = 2
        description = "🟡 WARNING - Significant stress increase"
    elif risk_score >= 0.7:
        edt_level = 1
        description = "🔵 CAUTION - Elevated stress"
    else:
        edt_level = 0
        description = "🟢 NORMAL - Stable operation"
    
    return EnhancedDynamicRisk(
        psi_norm=psi_norm,
        dpsi_dt=dpsi_dt,
        d2psi_dt2=d2psi_dt2,
        risk_score=risk_score,
        risk_normalized=risk_normalized,
        time_to_critical=time_to_critical,
        is_accelerating=is_accelerating,
        edt_level=edt_level,
        description=description
    )


def create_enhanced_perplexity_monitor():
    """Create Perplexity monitor with enhanced dynamics (position + velocity + acceleration)"""
    from entro_ai.core_v2 import create_perplexity_monitor
    
    monitor = create_perplexity_monitor()
    
    # Store history for each component
    monitor._psi_history = {}
    monitor._dpsi_history = {}
    monitor._last_timestamp = 0
    
    original_get_state = monitor.get_system_state
    
    def get_state_with_enhanced_dynamics(timestamp=None):
        import time
        if timestamp is None:
            timestamp = time.time()
        
        state = original_get_state(timestamp)
        
        for component, stress in state.components.items():
            if component not in monitor._psi_history:
                monitor._psi_history[component] = []
                monitor._dpsi_history[component] = []
            
            # Store normalized Ψ history
            psi_norm = normalize_psi(stress.psi, method="logistic", reference=10.0)
            monitor._psi_history[component].append(psi_norm)
            
            # Keep last 10 values
            if len(monitor._psi_history[component]) > 10:
                monitor._psi_history[component] = monitor._psi_history[component][-10:]
            
            # Calculate dΨ/dt and d²Ψ/dt²
            dpsi_dt = 0.0
            d2psi_dt2 = 0.0
            
            if len(monitor._psi_history[component]) >= 2 and monitor._last_timestamp > 0:
                dt = timestamp - monitor._last_timestamp
                if dt > 0:
                    dpsi_dt = (psi_norm - monitor._psi_history[component][-2]) / dt
                    monitor._dpsi_history[component].append(dpsi_dt)
                    
                    # Keep last 10 velocities
                    if len(monitor._dpsi_history[component]) > 10:
                        monitor._dpsi_history[component] = monitor._dpsi_history[component][-10:]
                    
                    # Calculate acceleration (d²Ψ/dt²)
                    if len(monitor._dpsi_history[component]) >= 2:
                        d2psi_dt2 = (dpsi_dt - monitor._dpsi_history[component][-2]) / dt
            
            # Compute enhanced dynamic risk
            enhanced_risk = compute_enhanced_risk(
                psi_norm=psi_norm,
                dpsi_dt=dpsi_dt,
                d2psi_dt2=d2psi_dt2,
                dt=dt if monitor._last_timestamp > 0 else 1.0
            )
            
            # Attach to stress object
            stress.enhanced_risk = enhanced_risk
            stress.dpsi_dt = dpsi_dt
            stress.d2psi_dt2 = d2psi_dt2
        
        monitor._last_timestamp = timestamp
        return state
    
    monitor.get_system_state = get_state_with_enhanced_dynamics
    return monitor

# ============================================================
# CORRECTED ENHANCED DYNAMIC RISK
# ============================================================

def compute_corrected_enhanced_risk(
    psi_norm: float,
    dpsi_dt: float,
    d2psi_dt2: float = 0.0,
    psi_c: float = 2.0,
    dt: float = 1.0,
    alpha: float = 0.5,      # وزن السرعة
    beta: float = 0.3        # وزن التسارع
) -> EnhancedDynamicRisk:
    """
    Compute enhanced dynamic risk - CORRECTED VERSION
    
    Risk = (Ψ_norm/Ψ_c) + α×|dΨ/dt|×dt + β×max(0, d²Ψ/dt²)×dt²
    
    هذا أفضل لأن المخاطر تتراكم (جمع) بدلاً من الضرب.
    """
    # Base risk from position
    position_risk = psi_norm / psi_c
    
    # Velocity contribution (always positive)
    velocity_contrib = alpha * abs(dpsi_dt) * dt
    
    # Acceleration contribution (only positive acceleration increases risk)
    acceleration_contrib = 0.0
    is_accelerating = False
    if d2psi_dt2 > 0:
        acceleration_contrib = beta * d2psi_dt2 * dt * dt
        is_accelerating = True
    
    # Unsaturated risk (sum of contributions)
    risk_score = position_risk + velocity_contrib + acceleration_contrib
    
    # Normalized risk for display (saturates at 1.0 for UI)
    risk_normalized = min(1.0, risk_score / 2.0)  # max expected ~2.0
    
    # Time to critical (if moving toward it)
    time_to_critical = float('inf')
    if dpsi_dt > 0 and psi_norm < psi_c:
        time_to_critical = (psi_c - psi_norm) / max(0.001, dpsi_dt)
    
    # EDT level based on unsaturated risk
    if risk_score >= 1.5:
        edt_level = 4
        description = "⚠️ IMMINENT COLLAPSE - Critical acceleration detected"
    elif risk_score >= 1.0:
        edt_level = 3
        description = "🔴 CRITICAL - Rapid deterioration"
    elif risk_score >= 0.6:
        edt_level = 2
        description = "🟡 WARNING - Significant stress increase"
    elif risk_score >= 0.3:
        edt_level = 1
        description = "🔵 CAUTION - Elevated stress"
    else:
        edt_level = 0
        description = "🟢 NORMAL - Stable operation"
    
    return EnhancedDynamicRisk(
        psi_norm=psi_norm,
        dpsi_dt=dpsi_dt,
        d2psi_dt2=d2psi_dt2,
        risk_score=risk_score,
        risk_normalized=risk_normalized,
        time_to_critical=time_to_critical,
        is_accelerating=is_accelerating,
        edt_level=edt_level,
        description=description
    )


def create_corrected_perplexity_monitor():
    """Create Perplexity monitor with CORRECTED enhanced dynamics"""
    from entro_ai.core_v2 import create_perplexity_monitor
    
    monitor = create_perplexity_monitor()
    
    # Store history for each component
    monitor._psi_history = {}
    monitor._dpsi_history = {}
    monitor._last_timestamp = 0
    
    original_get_state = monitor.get_system_state
    
    def get_state_with_corrected_dynamics(timestamp=None):
        import time
        if timestamp is None:
            timestamp = time.time()
        
        state = original_get_state(timestamp)
        
        for component, stress in state.components.items():
            if component not in monitor._psi_history:
                monitor._psi_history[component] = []
                monitor._dpsi_history[component] = []
            
            # Store normalized Ψ history
            psi_norm = normalize_psi(stress.psi, method="logistic", reference=10.0)
            monitor._psi_history[component].append(psi_norm)
            
            # Keep last 10 values
            if len(monitor._psi_history[component]) > 10:
                monitor._psi_history[component] = monitor._psi_history[component][-10:]
            
            # Calculate dΨ/dt and d²Ψ/dt²
            dpsi_dt = 0.0
            d2psi_dt2 = 0.0
            dt = 1.0
            
            if len(monitor._psi_history[component]) >= 2 and monitor._last_timestamp > 0:
                dt = timestamp - monitor._last_timestamp
                if dt > 0:
                    dpsi_dt = (psi_norm - monitor._psi_history[component][-2]) / dt
                    monitor._dpsi_history[component].append(dpsi_dt)
                    
                    if len(monitor._dpsi_history[component]) > 10:
                        monitor._dpsi_history[component] = monitor._dpsi_history[component][-10:]
                    
                    if len(monitor._dpsi_history[component]) >= 2:
                        d2psi_dt2 = (dpsi_dt - monitor._dpsi_history[component][-2]) / dt
            
            # Compute corrected enhanced dynamic risk
            enhanced_risk = compute_corrected_enhanced_risk(
                psi_norm=psi_norm,
                dpsi_dt=dpsi_dt,
                d2psi_dt2=d2psi_dt2,
                dt=dt
            )
            
            # Attach to stress object
            stress.enhanced_risk = enhanced_risk
            stress.dpsi_dt = dpsi_dt
            stress.d2psi_dt2 = d2psi_dt2
        
        monitor._last_timestamp = timestamp
        return state
    
    monitor.get_system_state = get_state_with_corrected_dynamics
    return monitor

# ============================================================
# CLEAN IMPLEMENTATION USING UNIFIED TRACKER
# ============================================================

from entro_ai.dynamics import DynamicsTracker, RiskLevel, DynamicState, create_tracker


class CleanSystemMonitor(GeneralSystemMonitor):
    """
    Clean implementation using unified DynamicsTracker
    No monkey patching, no duplicate code
    """
    
    def __init__(self, system_name: str, components: List[str], **kwargs):
        super().__init__(system_name, components, **kwargs)
        self.tracker = create_tracker()
        self._last_update_time = 0
    
    def update_component(
        self,
        component: str,
        utilization: float,
        veff_ratio: float = 1.0,
        timestamp: Optional[float] = None
    ):
        """Update component and compute dynamics"""
        if component not in self.components:
            raise ValueError(f"Unknown component: {component}")
        
        self._component_utilization[component] = utilization
        self._component_veff[component] = veff_ratio
        
        # Compute raw Ψ
        n = self.scaling_exponents.get(component, 1.63)
        psi_raw = compute_psi_component(utilization, veff_ratio, n)
        
        # Update dynamics tracker
        state = self.tracker.update(component, psi_raw, utilization, timestamp)
        
        # Store enhanced state
        self._component_dynamics[component] = state
    
    def get_system_state(self, timestamp: Optional[float] = None) -> SystemStressVector:
        """Get complete system state with dynamics"""
        if timestamp is None:
            timestamp = time.time()
        
        components_stress = {}
        
        for component in self.components:
            util = self._component_utilization.get(component, 0.0)
            veff = self._component_veff.get(component, 1.0)
            n = self.scaling_exponents.get(component, 1.63)
            
            psi_raw = compute_psi_component(util, veff, n)
            psi_norm = normalize_psi(psi_raw, method="logistic", reference=10.0)
            
            # Get dynamics if available
            dyn_state = self.tracker.get_state(component)
            dpsi_dt = dyn_state.dpsi_dt if dyn_state else 0.0
            risk_score = dyn_state.risk_score if dyn_state else 0.0
            
            components_stress[component] = ComponentStress(
                name=component,
                psi=psi_raw,
                dpsi_dt=dpsi_dt,
                veff=veff,
                utilization=util
            )
            components_stress[component].psi_norm = psi_norm
            components_stress[component].risk_score = risk_score
        
        return SystemStressVector(components=components_stress, timestamp=timestamp)


def create_clean_perplexity_monitor() -> CleanSystemMonitor:
    """Create clean Perplexity monitor using unified tracker"""
    from entro_ai.core_v2 import PERPLEXITY_CONFIG
    
    monitor = CleanSystemMonitor(
        system_name=PERPLEXITY_CONFIG["system_name"],
        components=PERPLEXITY_CONFIG["components"],
        scaling_exponents=PERPLEXITY_CONFIG["scaling_exponents"]
    )
    
    # Initialize components with default values
    for component in PERPLEXITY_CONFIG["components"]:
        monitor.update_component(component, 0.0)
    
    return monitor

class CleanSystemMonitor(GeneralSystemMonitor):
    """
    Clean implementation using unified DynamicsTracker
    No monkey patching, no duplicate code
    """
    
    def __init__(self, system_name: str, components: List[str], **kwargs):
        super().__init__(system_name, components, **kwargs)
        self.tracker = create_tracker()
        self._last_update_time = 0
        self._component_dynamics = {}  # <-- هذا كان مفقودًا
        self._component_utilization = {}  # <-- هذا أيضًا
        self._component_veff = {}  # <-- هذا أيضًا
    
    def update_component(
        self,
        component: str,
        utilization: float,
        veff_ratio: float = 1.0,
        timestamp: Optional[float] = None
    ):
        """Update component and compute dynamics"""
        if component not in self.components:
            raise ValueError(f"Unknown component: {component}")
        
        self._component_utilization[component] = utilization
        self._component_veff[component] = veff_ratio
        
        # Compute raw Ψ
        n = self.scaling_exponents.get(component, 1.63)
        psi_raw = compute_psi_component(utilization, veff_ratio, n)
        
        # Update dynamics tracker
        state = self.tracker.update(component, psi_raw, utilization, timestamp)
        
        # Store enhanced state
        self._component_dynamics[component] = state
    
    def get_system_state(self, timestamp: Optional[float] = None):
        """Get complete system state with dynamics"""
        if timestamp is None:
            timestamp = time.time()
        
        # Import here to avoid circular import
        from entro_ai.core_v2 import ComponentStress, SystemStressVector
        
        components_stress = {}
        
        for component in self.components:
            util = self._component_utilization.get(component, 0.0)
            veff = self._component_veff.get(component, 1.0)
            n = self.scaling_exponents.get(component, 1.63)
            
            psi_raw = compute_psi_component(util, veff, n)
            psi_norm = normalize_psi(psi_raw, method="logistic", reference=10.0)
            
            # Get dynamics if available
            dyn_state = self.tracker.get_state(component)
            dpsi_dt = dyn_state.dpsi_dt if dyn_state else 0.0
            risk_score = dyn_state.risk_score if dyn_state else 0.0
            
            # Create stress object
            stress = ComponentStress(
                name=component,
                psi=psi_raw,
                dpsi_dt=dpsi_dt,
                veff=veff,
                utilization=util
            )
            # Add extra attributes
            stress.psi_norm = psi_norm
            stress.risk_score = risk_score
            stress.dynamic_risk = dyn_state
            
            components_stress[component] = stress
        
        return SystemStressVector(components=components_stress, timestamp=timestamp)
    
    def get_bottleneck(self) -> Optional[str]:
        """Get current bottleneck component"""
        return self.tracker.get_bottleneck()
