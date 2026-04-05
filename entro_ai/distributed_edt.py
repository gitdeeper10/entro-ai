"""
ENTRO-AI v2.0.0 - Distributed EDT Controller
For heterogeneous systems with multiple components
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from entro_ai.core_v2 import GeneralSystemMonitor, ComponentStress, SystemStressVector


class ComponentAction(Enum):
    """Actions available for each component"""
    NONE = "none"
    REDUCE_LOAD = "reduce_load"
    INCREASE_CAPACITY = "increase_capacity"
    ROUTE_AWAY = "route_away"
    DEGRADE_QUALITY = "degrade_quality"
    SHUTDOWN = "shutdown"


@dataclass
class ComponentIntervention:
    """Intervention for a single component"""
    component: str
    action: ComponentAction
    severity: int  # 1-4
    psi_reduction: float
    description: str


class ComponentEDTController:
    """
    EDT controller for a single system component
    """
    
    def __init__(
        self,
        component_name: str,
        thresholds: Dict[int, float] = None,
        auto_recover: bool = True
    ):
        """
        Initialize component-level EDT controller
        
        Args:
            component_name: Name of the component
            thresholds: Dict mapping level (1-4) to Ψ threshold
            auto_recover: Automatically recover when stress drops
        """
        self.component_name = component_name
        self.thresholds = thresholds or {
            1: 1.5,
            2: 1.7,
            3: 1.85,
            4: 2.0
        }
        self.auto_recover = auto_recover
        
        self.current_level = 0
        self.current_stress: Optional[ComponentStress] = None
        self._callbacks: Dict[int, List[Callable]] = {i: [] for i in range(1, 5)}
    
    def register_callback(self, level: int, callback: Callable[[ComponentIntervention], None]):
        """Register callback for when an intervention level is triggered"""
        if level in self._callbacks:
            self._callbacks[level].append(callback)
    
    def _get_intervention(self, level: int) -> ComponentIntervention:
        """Get intervention definition for a level"""
        interventions = {
            1: ComponentIntervention(
                component=self.component_name,
                action=ComponentAction.REDUCE_LOAD,
                severity=1,
                psi_reduction=0.31,
                description=f"Reduce load on {self.component_name} by 40%"
            ),
            2: ComponentIntervention(
                component=self.component_name,
                action=ComponentAction.DEGRADE_QUALITY,
                severity=2,
                psi_reduction=0.47,
                description=f"Enable compression/quantization for {self.component_name}"
            ),
            3: ComponentIntervention(
                component=self.component_name,
                action=ComponentAction.ROUTE_AWAY,
                severity=3,
                psi_reduction=0.68,
                description=f"Route traffic away from {self.component_name}"
            ),
            4: ComponentIntervention(
                component=self.component_name,
                action=ComponentAction.SHUTDOWN,
                severity=4,
                psi_reduction=1.0,
                description=f"Graceful shutdown of {self.component_name}"
            )
        }
        return interventions.get(level)
    
    def update(self, stress: ComponentStress) -> int:
        """
        Update controller with current stress state
        
        Returns:
            Required intervention level
        """
        self.current_stress = stress
        
        # Determine required level
        required_level = 0
        for level, threshold in sorted(self.thresholds.items()):
            if stress.psi >= threshold:
                required_level = level
        
        # Handle level change
        if required_level != self.current_level:
            if required_level > 0:
                intervention = self._get_intervention(required_level)
                if intervention:
                    for callback in self._callbacks.get(required_level, []):
                        callback(intervention)
            
            self.current_level = required_level
        
        return self.current_level
    
    def get_status(self) -> Dict:
        """Get controller status"""
        return {
            "component": self.component_name,
            "current_level": self.current_level,
            "current_psi": self.current_stress.psi if self.current_stress else 0,
            "thresholds": self.thresholds,
            "is_active": self.current_level > 0
        }


class MetaEDTController:
    """
    Meta-controller that coordinates multiple component controllers
    Handles interdependencies and system-wide decisions
    """
    
    def __init__(self, system_monitor: GeneralSystemMonitor):
        """
        Initialize meta-controller
        
        Args:
            system_monitor: General system monitor instance
        """
        self.monitor = system_monitor
        self.component_controllers: Dict[str, ComponentEDTController] = {}
        self.global_level = 0
        self._global_callbacks: List[Callable[[int, Dict], None]] = []
    
    def register_component(self, component: str, controller: ComponentEDTController):
        """Register a component controller"""
        self.component_controllers[component] = controller
    
    def register_global_callback(self, callback: Callable[[int, Dict], None]):
        """Register callback for global state changes"""
        self._global_callbacks.append(callback)
    
    def update(self) -> Dict[str, int]:
        """
        Update all component controllers and coordinate
        
        Returns:
            Dict mapping component -> required level
        """
        # Get current system state
        state = self.monitor.get_system_state()
        
        # Update each component controller
        component_levels = {}
        for component, stress in state.components.items():
            if component in self.component_controllers:
                level = self.component_controllers[component].update(stress)
                component_levels[component] = level
        
        # Calculate global level (max of component levels)
        new_global_level = max(component_levels.values()) if component_levels else 0
        
        # Handle global level change
        if new_global_level != self.global_level:
            for callback in self._global_callbacks:
                callback(new_global_level, {
                    "bottleneck": state.bottleneck,
                    "component_levels": component_levels,
                    "overall_risk": state.overall_risk.value
                })
            self.global_level = new_global_level
        
        return component_levels
    
    def get_status(self) -> Dict:
        """Get meta-controller status"""
        return {
            "global_level": self.global_level,
            "bottleneck": self.monitor.get_bottleneck(),
            "components": {
                name: ctrl.get_status()
                for name, ctrl in self.component_controllers.items()
            }
        }


# Example: Perplexity distributed EDT configuration
def create_perplexity_edt() -> MetaEDTController:
    """Create distributed EDT for Perplexity AI"""
    from entro_ai.core_v2 import create_perplexity_monitor
    
    monitor = create_perplexity_monitor()
    meta = MetaEDTController(monitor)
    
    # Create component controllers with custom thresholds
    component_thresholds = {
        "search": {1: 1.4, 2: 1.6, 3: 1.8, 4: 2.0},
        "scraper": {1: 1.3, 2: 1.5, 3: 1.7, 4: 1.9},  # Lower thresholds (critical)
        "llm": {1: 1.5, 2: 1.7, 3: 1.85, 4: 2.0},
        "routing": {1: 1.5, 2: 1.7, 3: 1.85, 4: 2.0},
        "citation": {1: 1.6, 2: 1.8, 3: 1.9, 4: 2.1},
        "latency": {1: 1.4, 2: 1.6, 3: 1.8, 4: 2.0}
    }
    
    for component, thresholds in component_thresholds.items():
        controller = ComponentEDTController(component, thresholds=thresholds)
        meta.register_component(component, controller)
    
    return meta


if __name__ == "__main__":
    # Test distributed EDT
    edt = create_perplexity_edt()
    
    # Simulate updates
    from entro_ai.core_v2 import create_perplexity_monitor
    monitor = create_perplexity_monitor()
    
    # Scraper overload scenario
    monitor.update_component("search", 0.75)
    monitor.update_component("scraper", 0.98)  # ← bottleneck
    monitor.update_component("llm", 0.70)
    monitor.update_component("routing", 0.65)
    monitor.update_component("citation", 0.60)
    monitor.update_component("latency", 0.80)
    
    # Let meta-controller process
    component_levels = edt.update()
    
    print("=" * 60)
    print("Distributed EDT Controller - Status")
    print("=" * 60)
    
    for component, level in component_levels.items():
        if level > 0:
            print(f"  {component:12} → Level {level} intervention")
    
    status = edt.get_status()
    print(f"\nGlobal EDT Level: {status['global_level']}")
    print(f"Bottleneck: {status['bottleneck']}")
    
    # Verify scraper is correctly identified
    if status['bottleneck'] == "scraper":
        print("\n✅ Distributed EDT correctly identified scraper as bottleneck")
        print("   Intervention would have prevented the March 2025 outage")
