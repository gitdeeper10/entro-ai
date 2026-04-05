"""
ENTRO-AI v2.0.0
General Theory of Computational System Stability
Builds on ENTROPIA (E-LAB-01) · DOI: 10.5281/zenodo.19416737

Key Changes in v2.0.0:
- Ψ as vector (not scalar)
- dΨ/dt mandatory
- V_eff as min of ALL constraints
- Distributed EDT support
- General system monitor (not just LLMs)
"""

__version__ = "2.0.0"
__author__ = "Samir Baladi"
__email__ = "gitdeeper@gmail.com"
__license__ = "MIT"

ENTROPIA_DOI = "10.5281/zenodo.19416737"

# v2.0.0 exports
from entro_ai.core_v2 import (
    GeneralSystemMonitor,
    SystemStressVector,
    ComponentStress,
    SystemTopology,
    CollapseRisk,
    compute_veff_general,
    compute_psi_component,
    create_perplexity_monitor
)

from entro_ai.distributed_edt import (
    MetaEDTController,
    ComponentEDTController,
    ComponentIntervention,
    ComponentAction,
    create_perplexity_edt
)

# Legacy exports (v1.x compatibility)
from entro_ai.core import EntroAIMonitor as LegacyEntroAIMonitor
from entro_ai.architecture import get_scaling_exponent, ARCHITECTURES
from entro_ai.coherence import compute_coherence, kappa_to_bertscore
from entro_ai.edt_controller import EDTController as LegacyEDTController

__all__ = [
    # v2.0.0
    "GeneralSystemMonitor",
    "SystemStressVector", 
    "ComponentStress",
    "SystemTopology",
    "CollapseRisk",
    "compute_veff_general",
    "compute_psi_component",
    "create_perplexity_monitor",
    "MetaEDTController",
    "ComponentEDTController",
    "ComponentIntervention",
    "ComponentAction",
    "create_perplexity_edt",
    # Legacy
    "LegacyEntroAIMonitor",
    "get_scaling_exponent",
    "ARCHITECTURES",
    "compute_coherence",
    "kappa_to_bertscore",
    "LegacyEDTController",
    "ENTROPIA_DOI"
]
