"""
ENTRO-AI Adaptive EDT Controller
Uses dynamic risk levels for graduated intervention
"""

from typing import Dict, Optional
from entro_ai.dynamics import DynamicsTracker, RiskLevel, create_tracker


class AdaptiveEDTController:
    """
    Adaptive EDT Controller that responds to risk levels
    """
    
    # Mapping from risk level to EDT intervention
    EDT_MAPPING = {
        RiskLevel.STABLE: 0,
        RiskLevel.CAUTION: 1,
        RiskLevel.WARNING: 2,
        RiskLevel.CRITICAL: 3,
        RiskLevel.IMMINENT: 4,
    }
    
    # Intervention descriptions
    INTERVENTIONS = {
        0: "🟢 No action - System stable",
        1: "🔵 Caution - Reduce batch size by 20%",
        2: "🟡 Warning - Reduce batch size by 40%, monitor",
        3: "🟠 Critical - Enable INT8 quantization",
        4: "🔴 Imminent - Route to smaller model, prepare failover",
    }
    
    def __init__(self, tracker: DynamicsTracker):
        self.tracker = tracker
    
    def get_intervention(self, component: str) -> int:
        """Get EDT level for a component based on its risk level"""
        state = self.tracker.get_state(component)
        if not state:
            return 0
        return self.EDT_MAPPING.get(state.risk_level, 0)
    
    def get_all_interventions(self) -> Dict[str, int]:
        """Get EDT levels for all components"""
        interventions = {}
        for component in self.tracker.get_all_states().keys():
            interventions[component] = self.get_intervention(component)
        return interventions
    
    def get_global_intervention(self) -> int:
        """Get highest EDT level across all components"""
        interventions = self.get_all_interventions()
        return max(interventions.values()) if interventions else 0
    
    def get_description(self, level: int) -> str:
        """Get human-readable description for EDT level"""
        return self.INTERVENTIONS.get(level, "Unknown level")


def create_adaptive_controller() -> AdaptiveEDTController:
    """Create an adaptive EDT controller with default tracker"""
    tracker = create_tracker()
    return AdaptiveEDTController(tracker)


if __name__ == "__main__":
    # Test the adaptive controller
    controller = create_adaptive_controller()
    
    print("=== ADAPTIVE EDT CONTROLLER ===")
    print()
    
    # Simulate different risk levels
    test_risks = [
        ("Stable", RiskLevel.STABLE),
        ("Caution", RiskLevel.CAUTION),
        ("Warning", RiskLevel.WARNING),
        ("Critical", RiskLevel.CRITICAL),
        ("Imminent", RiskLevel.IMMINENT),
    ]
    
    for name, level in test_risks:
        edt_level = controller.EDT_MAPPING[level]
        print(f"{name:10} → EDT Level {edt_level}: {controller.get_description(edt_level)}")
