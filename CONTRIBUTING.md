# Contributing to ENTRO-AI

Thank you for your interest in contributing to **ENTRO-AI**! This framework applies thermodynamic principles to make AI inference systems resistant to context collapse and hallucination.

**Builds on ENTROPIA (E-LAB-01):** [10.5281/zenodo.19416737](https://doi.org/10.5281/zenodo.19416737)

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Research Contributions](#research-contributions)
- [Contact](#contact)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment tool
- (Optional) NVIDIA GPU for model testing

### Fork and Clone

```bash
# Fork the repository on GitLab/GitHub, then:
git clone https://gitlab.com/gitdeeper10/entro-ai.git
cd entro-ai
```

Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
pre-commit install
```

Development Environment

Project Structure

```
entro-ai/
├── entro_ai/               # Main package
│   ├── core.py             # Extended ENTROPIA equations (Eq. 12-16)
│   ├── architecture.py     # Architecture-specific exponents (n)
│   ├── edt_controller.py   # Entropy-Driven Throttling
│   ├── coherence.py        # Output coherence κ
│   ├── predictor.py        # τ_collapse for AI
│   └── telemetry.py        # vLLM/TensorRT/Triton adapters
├── calibration/            # Architecture calibration tools
├── edt/                    # EDT microservice
├── dashboard/              # Ψ-Dashboard AI extension
├── simulation/             # Inference stress tests
├── case_studies/           # Retrospective analysis
├── tests/                  # Unit and integration tests
├── docs/                   # Documentation
└── notebooks/              # Jupyter notebooks
```

How to Contribute

Types of Contributions

1. Code Contributions
   · New telemetry adapters (SGLang, Ollama, DeepSpeed)
   · Additional architecture calibrations
   · EDT controller improvements
   · Performance optimizations
2. Research Contributions
   · New architecture exponent validations
   · Real production telemetry datasets
   · Case study analyses
   · Cross-domain applications
3. Documentation
   · API documentation
   · Tutorials
   · Examples
   · Translations
4. Testing
   · Unit tests
   · Integration tests with real models
   · Benchmarking

Issue Tracking

· Check existing issues before creating new ones
· Use issue templates when available
· Include relevant ENTRO-AI parameters (Ψ, κ, τ_collapse)
· Specify architecture (transformer/bert/vit/neuromorphic)

Pull Request Process

1. Create a Branch
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
2. Make Changes
   · Write clean, documented code
   · Add tests for new functionality
   · Update documentation
   · Reference ENTROPIA equations where applicable
3. Run Tests
   ```bash
   # Run all tests
   pytest tests/
   
   # Run specific test suite
   pytest tests/test_edt_controller.py
   
   # Run with coverage
   pytest --cov=entro_ai tests/
   ```
4. Format Code
   ```bash
   # Format with black
   black entro_ai/ tests/
   
   # Sort imports
   isort entro_ai/ tests/
   
   # Lint with flake8
   flake8 entro_ai/ tests/
   ```
5. Commit and Push
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/your-feature-name
   ```
6. Create Pull Request
   · Use PR template
   · Link related issues
   · Request review from maintainers

Coding Standards

Python Style

· Follow PEP 8
· Use Black for formatting
· Use isort for import sorting
· Type hints are required for all public functions

Docstrings

Use Google-style docstrings:

```python
def edt_controller(psi: float, dpsi_dt: float, architecture: str) -> int:
    """
    Determine EDT intervention level based on Ψ and its derivative.
    
    Args:
        psi: Current dissipation coefficient (dimensionless)
        dpsi_dt: Rate of change of Ψ (s⁻¹)
        architecture: Model architecture ("transformer_llm", "bert", etc.)
    
    Returns:
        int: EDT level (0=no action, 1=L1, 2=L2, 3=L3, 4=L4)
    
    Raises:
        ValueError: If architecture is not supported
    
    Example:
        >>> level = edt_controller(psi=1.65, dpsi_dt=0.12, architecture="transformer_llm")
        >>> print(f"EDT Level: {level}")
        EDT Level: 2
    """
    if architecture not in SUPPORTED_ARCHITECTURES:
        raise ValueError(f"Unsupported architecture: {architecture}")
    
    if psi > 2.0:
        return 4
    elif psi > 1.85:
        return 3
    elif psi > 1.7:
        return 2
    elif psi > 1.5:
        return 1
    else:
        return 0
```

Testing

Unit Tests

· Place tests in tests/ directory
· Use pytest framework
· Aim for >80% coverage

Integration Tests

· Test with real models (small variants for CI)
· Validate EDT interventions
· Test telemetry adapters

Documentation

Building Documentation

```bash
cd docs
make html
```

API Documentation

· Document all public functions and classes
· Include mathematical equations in LaTeX
· Reference ENTROPIA equations (Eq. 12-16)
· Link to architecture exponents table

Research Contributions

If you're contributing research:

1. Reproducibility: Include all code and data
2. Documentation: Document methodology and parameters
3. Validation: Validate against ENTRO-AI benchmarks
4. Citation: Cite ENTRO-AI and ENTROPIA properly

Required Citations

```bibtex
@article{baladi2026entroai,
  title={ENTRO-AI: Entropy-Resistant Inference Architecture},
  author={Baladi, Samir},
  year={2026},
  note={E-LAB-02}
}

@article{baladi2026entropia,
  title={ENTROPIA: Statistical Dynamics of Information Dissipation},
  author={Baladi, Samir},
  year={2026},
  doi={10.5281/zenodo.19416737},
  note={E-LAB-01}
}
```

Contact

· Principal Investigator: Samir Baladi - gitdeeper@gmail.com
· GitLab Issues: gitlab.com/gitdeeper10/entro-ai/-/issues
· Discussions: gitlab.com/gitdeeper10/entro-ai/-/discussions

---

Thank you for contributing to ENTRO-AI! Together, we're building thermodynamically honest AI systems.

"Artificial intelligence that understands its own thermodynamic limits is not weaker. It is, for the first time, physically honest."
