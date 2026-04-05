"""
ENTRO-AI Architecture Module
Architecture-specific entropy scaling exponents (n)
Builds on ENTROPIA (E-LAB-01) · DOI: 10.5281/zenodo.19416737
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass

# Architecture exponent database (Eq. 13)
ARCHITECTURES: Dict[str, Dict] = {
    "transformer_llm": {
        "n": 1.63,
        "n_measured": 1.63,
        "r2": 0.981,
        "E_a": 0.58,  # eV
        "description": "Transformer LLM (GPT-class)",
        "physical_mechanism": "Attention head entropy grows as O(L²)"
    },
    "bert": {
        "n": 1.58,
        "n_measured": 1.57,
        "r2": 0.983,
        "E_a": 0.55,
        "description": "BERT-class Encoder",
        "physical_mechanism": "Bidirectional context entropy accumulation"
    },
    "vit": {
        "n": 1.74,
        "n_measured": 1.74,
        "r2": 0.976,
        "E_a": 0.62,
        "description": "CNN / Vision Transformer",
        "physical_mechanism": "Feature map routing under batch saturation"
    },
    "neuromorphic": {
        "n": 1.42,
        "n_measured": 1.44,
        "r2": 0.971,
        "E_a": 0.45,
        "description": "Neuromorphic SNN",
        "physical_mechanism": "Spike timing entropy — lowest dissipation rate"
    },
    "von_neumann": {
        "n": 1.85,
        "n_measured": 1.87,
        "r2": 0.989,
        "E_a": 0.60,
        "description": "Von Neumann (baseline from ENTROPIA)",
        "physical_mechanism": "Generic packet routing"
    }
}


@dataclass
class ArchitectureInfo:
    """Information about an architecture's thermodynamic properties"""
    name: str
    n: float
    n_measured: float
    r2: float
    E_a: float
    description: str
    physical_mechanism: str


def get_scaling_exponent(architecture: str) -> float:
    """
    Get entropy scaling exponent n for given architecture
    
    Args:
        architecture: Architecture name (transformer_llm, bert, vit, neuromorphic, von_neumann)
    
    Returns:
        Scaling exponent n
    
    Raises:
        ValueError: If architecture not found
    """
    if architecture not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture: {architecture}. Available: {list(ARCHITECTURES.keys())}")
    
    return ARCHITECTURES[architecture]["n"]


def get_activation_energy(architecture: str) -> float:
    """
    Get activation energy E_a for given architecture
    
    Args:
        architecture: Architecture name
    
    Returns:
        Activation energy in eV
    """
    if architecture not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture: {architecture}")
    
    return ARCHITECTURES[architecture]["E_a"]


def get_architecture_info(architecture: str) -> ArchitectureInfo:
    """
    Get complete information about an architecture
    
    Args:
        architecture: Architecture name
    
    Returns:
        ArchitectureInfo dataclass
    """
    if architecture not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture: {architecture}")
    
    data = ARCHITECTURES[architecture]
    return ArchitectureInfo(
        name=architecture,
        n=data["n"],
        n_measured=data["n_measured"],
        r2=data["r2"],
        E_a=data["E_a"],
        description=data["description"],
        physical_mechanism=data["physical_mechanism"]
    )


def list_architectures() -> list:
    """List all available architectures"""
    return list(ARCHITECTURES.keys())


def get_critical_exponent(architecture: str) -> float:
    """
    Calculate critical exponent β = 1/(n-1)
    
    Args:
        architecture: Architecture name
    
    Returns:
        Critical exponent β
    """
    n = get_scaling_exponent(architecture)
    return 1.0 / (n - 1.0)


def compare_architectures() -> Dict[str, Dict]:
    """
    Compare all architectures' thermodynamic properties
    """
    comparison = {}
    for name in ARCHITECTURES:
        info = get_architecture_info(name)
        comparison[name] = {
            "n": info.n,
            "β": get_critical_exponent(name),
            "E_a_eV": info.E_a,
            "R²": info.r2,
            "description": info.description
        }
    return comparison


# Convenience constants
TRANSFORMER_N = 1.63
BERT_N = 1.58
VIT_N = 1.74
NEUROMORPHIC_N = 1.42
VON_NEUMANN_N = 1.85

# Best architecture thermodynamically
BEST_ARCHITECTURE = "neuromorphic"
BEST_N = NEUROMORPHIC_N
