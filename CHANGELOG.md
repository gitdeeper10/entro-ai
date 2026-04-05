# ENTRO-AI Changelog

All notable changes to the ENTRO-AI framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Builds on ENTROPIA (E-LAB-01):** [10.5281/zenodo.19416737](https://doi.org/10.5281/zenodo.19416737)

---

## [2.0.0] - 2026-04-05

### 🎉 Major Release: General Theory of Computational System Stability

This release represents a fundamental shift from "LLM analysis tool" to **general theory of computational system stability**. The framework now applies to ANY information processing system under constraints.

### ✨ Added

#### Core Theoretical Breakthroughs

- **Ψ as Vector (not scalar)**: System stress represented as vector across components
- **dΨ/dt Mandatory**: Rate of change is now required, not optional
- **V_eff Generalization**: `V_eff = min(all_constraints_in_pipeline)` - works for any system
- **Adaptive Risk Levels**: Risk assessment adapts to rate of change (fast change = tighter thresholds)
- **Position + Velocity + Acceleration**: Complete dynamic state tracking

#### New Components

- **`DynamicsTracker`** - Unified dynamics tracker for any system component
  - Normalizes Ψ values (logistic, log, or linear methods)
  - Computes derivatives (velocity, acceleration) with smoothing
  - Calculates unsaturated risk scores
  - Maintains history for all components

- **`AdaptiveEDTController`** - Adaptive EDT with graduated interventions
  - Maps risk levels (STABLE → CAUTION → WARNING → CRITICAL → IMMINENT) to EDT levels (0-4)
  - Adaptive thresholds that tighten during rapid change
  - Preventive control (not reactive)

- **`CleanSystemMonitor`** - Clean implementation without monkey patching
  - Uses unified DynamicsTracker
  - No duplicate code
  - Easy to extend for new systems

#### Risk Level System

| Level | Risk Score | EDT | Description |
|-------|------------|-----|-------------|
| STABLE | < 0.3 | 0 | Normal operation |
| CAUTION | 0.3 - 0.6 | 1 | Elevated stress, monitor |
| WARNING | 0.6 - 1.0 | 2 | Significant stress, prepare |
| CRITICAL | 1.0 - 1.5 | 3 | Rapid deterioration |
| IMMINENT | > 1.5 | 4 | Collapse imminent |

#### Smoothing & Stability

- Minimum dt of 0.5 seconds to avoid unrealistic spikes
- dΨ/dt capped at [-5, 5] range
- d²Ψ/dt² capped at [-2, 2] range
- No more panic-driven risk saturation

### 🔧 Changed

- **Refactored from 3 duplicate functions to single `DynamicsTracker` class**
- **Fixed `dt` undefined bug** - now properly calculated from timestamps
- **Fixed `_component_dynamics` missing attribute**
- **Replaced monkey patching with clean inheritance**
- **Documented all risk thresholds** (no more magic numbers)

### 🗑️ Removed

- `create_dynamic_perplexity_monitor` (replaced by CleanSystemMonitor)
- `create_enhanced_perplexity_monitor` (replaced by CleanSystemMonitor)
- `create_corrected_perplexity_monitor` (replaced by CleanSystemMonitor)
- `ComponentStressWithDynamics` (replaced by DynamicsTracker + DynamicState)

### 📊 Validation Results (Perplexity AI Case Study)

| Utilization | Ψ_norm | dΨ/dt | Risk | Level |
|-------------|--------|-------|------|-------|
| 0.50 | 0.116 | +0.00 | 0.116 | STABLE |
| 0.60 | 0.190 | +0.15 | 0.132 | STABLE |
| 0.70 | 0.308 | +0.24 | 0.226 | STABLE |
| 0.80 | 0.510 | +0.40 | 0.381 | CAUTION |
| 0.85 | 0.672 | +0.32 | 0.417 | CAUTION |
| 0.90 | 0.911 | +0.48 | 0.598 | CAUTION |
| 0.93 | 1.116 | +0.41 | 0.661 | WARNING |
| 0.95 | 1.294 | +0.36 | 0.736 | WARNING |
| 0.97 | 1.520 | +0.45 | 0.887 | WARNING |
| 0.98 | 1.657 | +0.27 | 0.897 | WARNING |

### 🧠 Theoretical Significance

**ENTRO-AI v2.0.0 is no longer:**
> An LLM analysis tool

**ENTRO-AI v2.0.0 is now:**
> A General Theory of Computational System Stability

The framework now:
- Reads system behavior rather than overreacting to spikes
- Balances sensitivity with stability
- Provides preventive (not emergency) control
- Works for ANY system with constraints (search, scraper, LLM, routing, citation, latency)

### 🚀 Upgrading from v1.x

```python
# Old way (v1.x)
from entro_ai.core import EntroAIMonitor
monitor = EntroAIMonitor(architecture="transformer_llm")

# New way (v2.0.0)
from entro_ai.core_v2 import create_clean_perplexity_monitor
monitor = create_clean_perplexity_monitor()
# Or for custom systems:
from entro_ai.dynamics import DynamicsTracker
tracker = DynamicsTracker()
state = tracker.update("component", psi_raw, utilization)
```

---

[1.0.0] - 2026-04-04

Initial Release (Legacy)

· Core framework for LLM inference monitoring
· Architecture-specific entropy scaling exponents (n)
· EDT controller with 4 levels
· 1,247 validation runs
· 91.4% collapse detection accuracy
· 67.3% hallucination reduction

See CHANGELOG_v1.md for full v1.0.0 details

---

🔮 Roadmap

v2.1.0 (Q2 2026)

· WebSocket real-time streaming for dynamics
· Grafana dashboard integration
· Additional normalization methods
· Auto-calibration from historical data

v2.2.0 (Q3 2026)

· Multi-system coordination (meta-EDT)
· ML-based threshold optimization
· Export to Prometheus metrics
· Kubernetes operator

v3.0.0 (2027)

· Quantum system support (E-LAB-06)
· Biological neural networks (E-LAB-07)
· Climate models (E-LAB-08)

---

🙏 Acknowledgments

· ENTROPIA (E-LAB-01) - Foundational thermodynamic framework
· Perplexity AI - Case study that revealed the need for v2.0.0
· Open-source scientific computing community

---

For complete details, see the ENTRO-AI Research Paper.

"Artificial intelligence that understands its own thermodynamic limits is not weaker. It is, for the first time, physically honest."
