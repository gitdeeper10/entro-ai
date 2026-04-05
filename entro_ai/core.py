"""
ENTRO-AI Core Module
Extended ENTROPIA equations for AI inference (Eq. 12-16)
Builds on ENTROPIA (E-LAB-01) · DOI: 10.5281/zenodo.19416737
"""

import math
from typing import Optional, Tuple, Dict
from dataclasses import dataclass, field

# Boltzmann constant (J/K)
K_B = 1.380649e-23
# Natural log of 2 for bit conversion
LN2 = 0.6931471805599453


@dataclass
class EntroAIState:
    """Thermodynamic state of an AI inference system"""
    rho_ratio: float = 0.0      # ρ/ρ_c
    psi: float = 0.0             # Dissipation coefficient
    kappa: float = 0.0           # Output coherence
    tau_collapse: float = 0.0    # Predicted time to collapse (seconds)
    edt_level: int = 0           # Current EDT intervention level (0-4)
    s_total: float = 0.0         # Total entropy (J/K)


def compute_veff_ai(
    kv_cache_gb: float,
    attn_flops_tflops: float,
    gpu_mem_bw_tbs: float,
    n_layers: int,
    d_model: int
) -> float:
    """
    Calculate effective processing volume for AI inference (Eq. 12)
    
    V_eff(AI) = min[M_KV, B_attn, B_mem] × N_layers × d_model
    
    Args:
        kv_cache_gb: KV-cache memory capacity (GB)
        attn_flops_tflops: Attention computation bandwidth (TFLOPS)
        gpu_mem_bw_tbs: GPU memory bandwidth (TB/s)
        n_layers: Number of transformer layers
        d_model: Model embedding dimension
    
    Returns:
        Effective processing volume
    """
    # Convert to consistent units (bytes, FLOP/s, bytes/s)
    m_kv = kv_cache_gb * 1e9  # GB to bytes
    b_attn = attn_flops_tflops * 1e12  # TFLOPS to FLOP/s
    b_mem = gpu_mem_bw_tbs * 1e12  # TB/s to bytes/s
    
    # Min of the three constraints
    bottleneck = min(m_kv, b_attn, b_mem)
    
    return bottleneck * n_layers * d_model


def compute_rho_ratio(
    token_rate: float,
    context_length: int,
    veff: float,
    rho_c: float = 1.0
) -> float:
    """
    Calculate data density ratio ρ/ρ_c
    
    Args:
        token_rate: Tokens per second
        context_length: Current context length in tokens
        veff: Effective processing volume
        rho_c: Critical throughput threshold
    
    Returns:
        ρ/ρ_c ratio
    """
    # Information density
    rho = (token_rate * context_length) / veff
    return rho / rho_c


def compute_psi(
    rho_ratio: float,
    s_total: float,
    s_max: float = 1.0
) -> float:
    """
    Calculate Dissipation Coefficient Ψ(ρ) (Eq. 9 from ENTROPIA)
    
    Ψ(ρ) = (S_total/S_max) × [1 − (ρ_c/ρ)²]⁻¹
    
    Args:
        rho_ratio: ρ/ρ_c ratio
        s_total: Current total entropy
        s_max: Maximum theoretical entropy
    
    Returns:
        Dissipation coefficient (dimensionless)
    """
    if rho_ratio >= 1.0:
        return float('inf')  # Super-critical regime
    
    # Normalized entropy
    s_norm = s_total / s_max
    
    # Divergence term (1 - (ρ_c/ρ)²)⁻¹ = (1 - 1/(ρ/ρ_c)²)⁻¹
    divergence = 1.0 / (1.0 - 1.0 / (rho_ratio * rho_ratio))
    
    return s_norm * divergence


def compute_kappa(
    psi: float,
    psi_c: float = 2.0
) -> float:
    """
    Calculate output coherence κ (Eq. 14)
    
    κ(ρ) = exp[−S_total / (k_B ln 2)]
    
    For operational use, κ ~ exp(−Ψ/Ψ_c)
    
    Args:
        psi: Dissipation coefficient
        psi_c: Critical threshold (default 2.0)
    
    Returns:
        Output coherence (0 = complete collapse, 1 = perfect coherence)
    """
    if psi >= psi_c:
        return 0.0
    
    # Exponential decay of coherence with Ψ
    return math.exp(-psi / psi_c)


def compute_tau_collapse(
    psi: float,
    dpsi_dt: float,
    psi_c: float = 2.0,
    min_tau: float = 1.0,
    max_tau: float = 3600.0
) -> float:
    """
    Calculate collapse lead time τ_collapse (Eq. 11)
    
    τ_collapse = (Ψ_c − Ψ(t)) / |dΨ/dt|
    
    Args:
        psi: Current dissipation coefficient
        dpsi_dt: Rate of change of Ψ (per second)
        psi_c: Critical threshold
        min_tau: Minimum lead time (seconds)
        max_tau: Maximum lead time (seconds)
    
    Returns:
        Predicted seconds until collapse
    """
    if psi >= psi_c:
        return 0.0
    
    if dpsi_dt <= 0:
        # Decreasing or stable Ψ → no imminent collapse
        return max_tau
    
    tau = (psi_c - psi) / abs(dpsi_dt)
    
    # Clamp to reasonable range
    return max(min_tau, min(tau, max_tau))


def get_edt_level(
    psi: float,
    threshold_l1: float = 1.5,
    threshold_l2: float = 1.7,
    threshold_l3: float = 1.85,
    threshold_l4: float = 2.0
) -> int:
    """
    Determine EDT intervention level based on Ψ
    
    Args:
        psi: Current dissipation coefficient
        threshold_l1: Level 1 threshold (soft intervention)
        threshold_l2: Level 2 threshold (medium intervention)
        threshold_l3: Level 3 threshold (hard intervention)
        threshold_l4: Level 4 threshold (critical)
    
    Returns:
        EDT level (0-4)
    """
    if psi >= threshold_l4:
        return 4  # Critical - graceful shutdown
    elif psi >= threshold_l3:
        return 3  # Hard - route to smaller model
    elif psi >= threshold_l2:
        return 2  # Medium - INT8 quantization
    elif psi >= threshold_l1:
        return 1  # Soft - reduce batch size
    else:
        return 0  # No intervention needed


class EntroAIMonitor:
    """
    Real-time entropy monitor for AI inference systems
    """
    
    # Architecture-specific constants
    ARCHITECTURE_PARAMS = {
        "transformer_llm": {"n": 1.63, "E_a": 0.58, "rho_c": 1.0},
        "bert": {"n": 1.58, "E_a": 0.55, "rho_c": 1.0},
        "vit": {"n": 1.74, "E_a": 0.62, "rho_c": 1.0},
        "neuromorphic": {"n": 1.42, "E_a": 0.45, "rho_c": 1.0},
        "von_neumann": {"n": 1.85, "E_a": 0.60, "rho_c": 1.0},
    }
    
    # EDT thresholds
    EDT_THRESHOLDS = {
        "l1": 1.5,
        "l2": 1.7,
        "l3": 1.85,
        "l4": 2.0
    }
    
    def __init__(
        self,
        architecture: str = "transformer_llm",
        n_layers: int = 32,
        d_model: int = 4096,
        kv_cache_gb: float = 40.0,
        gpu_mem_bw_tbs: float = 3.35,
        attn_flops_tflops: float = 1979.0,
        rho_c: float = 1.0
    ):
        """
        Initialize the entropy monitor
        
        Args:
            architecture: Model architecture type
            n_layers: Number of transformer layers
            d_model: Model dimension
            kv_cache_gb: KV-cache size in GB
            gpu_mem_bw_tbs: GPU memory bandwidth in TB/s
            attn_flops_tflops: Attention compute in TFLOPS
            rho_c: Critical threshold (normalized)
        """
        self.architecture = architecture
        self.n_layers = n_layers
        self.d_model = d_model
        self.rho_c = rho_c
        
        # Get architecture-specific exponent
        arch_params = self.ARCHITECTURE_PARAMS.get(architecture, self.ARCHITECTURE_PARAMS["transformer_llm"])
        self.n = arch_params["n"]
        self.E_a = arch_params["E_a"]
        
        # Calculate V_eff
        self.veff = compute_veff_ai(
            kv_cache_gb=kv_cache_gb,
            attn_flops_tflops=attn_flops_tflops,
            gpu_mem_bw_tbs=gpu_mem_bw_tbs,
            n_layers=n_layers,
            d_model=d_model
        )
        
        # State
        self.state = EntroAIState()
        self._last_psi = 0.0
        self._last_time = 0.0
    
    def update(
        self,
        kv_cache_used: float,
        attn_flops_util: float,
        token_rate: float,
        context_length: int,
        gpu_mem_util: float,
        timestamp: Optional[float] = None
    ) -> EntroAIState:
        """
        Update the thermodynamic state with current telemetry
        
        Args:
            kv_cache_used: KV-cache occupancy (0-1)
            attn_flops_util: Attention bandwidth utilization (0-1)
            token_rate: Current token generation rate
            context_length: Current context length in tokens
            gpu_mem_util: GPU memory utilization (0-1)
            timestamp: Current timestamp (seconds)
        
        Returns:
            Current EntroAIState
        """
        # Calculate current constraints
        m_kv_used = kv_cache_used * self.veff / (self.n_layers * self.d_model)
        b_attn_used = attn_flops_util
        b_mem_used = gpu_mem_util
        
        # Effective utilization
        util = min(m_kv_used, b_attn_used, b_mem_used)
        
        # Calculate ρ/ρ_c
        rho_ratio = compute_rho_ratio(
            token_rate=token_rate,
            context_length=context_length,
            veff=self.veff * util,
            rho_c=self.rho_c
        )
        
        # Estimate entropy (simplified model)
        s_total = rho_ratio * K_B * self.n * math.log(1.0 / max(0.01, 1.0 - rho_ratio))
        
        # Calculate Ψ
        psi = compute_psi(rho_ratio, s_total)
        
        # Calculate dΨ/dt if timestamp provided
        dpsi_dt = 0.0
        if timestamp is not None and self._last_time > 0:
            dt = timestamp - self._last_time
            if dt > 0:
                dpsi_dt = (psi - self._last_psi) / dt
        
        # Calculate τ_collapse
        tau_collapse = compute_tau_collapse(psi, dpsi_dt)
        
        # Calculate κ
        kappa = compute_kappa(psi)
        
        # Get EDT level
        edt_level = get_edt_level(psi, **self.EDT_THRESHOLDS)
        
        # Update state
        self.state = EntroAIState(
            rho_ratio=rho_ratio,
            psi=psi,
            kappa=kappa,
            tau_collapse=tau_collapse,
            edt_level=edt_level,
            s_total=s_total
        )
        
        # Store for next update
        self._last_psi = psi
        if timestamp is not None:
            self._last_time = timestamp
        
        return self.state
    
    def get_state(self) -> EntroAIState:
        """Get current thermodynamic state"""
        return self.state
    
    def is_critical(self) -> bool:
        """Check if system is in critical regime"""
        return self.state.psi >= self.EDT_THRESHOLDS["l4"]
    
    def time_to_collapse(self) -> float:
        """Get predicted time to collapse (seconds)"""
        return self.state.tau_collapse
    
    def coherence(self) -> float:
        """Get current output coherence κ"""
        return self.state.kappa


# Helper functions for backward compatibility
def compute_veff_from_config(config: Dict) -> float:
    """Calculate V_eff from configuration dictionary"""
    return compute_veff_ai(
        kv_cache_gb=config.get("kv_cache_gb", 40.0),
        attn_flops_tflops=config.get("attn_flops_tflops", 1979.0),
        gpu_mem_bw_tbs=config.get("gpu_mem_bw_tbs", 3.35),
        n_layers=config.get("n_layers", 32),
        d_model=config.get("d_model", 4096)
    )
