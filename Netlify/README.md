# 🔴 ENTROPIA Netlify Dashboard

**Statistical Dynamics of Information Dissipation in Complex Non-Linear Digital Systems**

[![Netlify Status](https://api.netlify.com/api/v1/badges/entropia/deploy-status)](https://entropia-lab.netlify.app)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.19183878-orange)](https://doi.org/10.5281/zenodo.19183878)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-red)](LICENSE)

---

## 🚀 Live Dashboard
- **Dashboard:** [https://entropia-lab.netlify.app](https://entropia-lab.netlify.app)
- **Ψ-Dashboard:** [https://entropia-lab.netlify.app/dashboard](https://entropia-lab.netlify.app/dashboard)
- **Reports:** [https://entropia-lab.netlify.app/reports](https://entropia-lab.netlify.app/reports)
- **Documentation:** [https://entropia-lab.netlify.app/docs](https://entropia-lab.netlify.app/docs)
- **Research Paper:** [https://entropia-lab.netlify.app/paper](https://entropia-lab.netlify.app/paper)

---

## 📊 Current Status (2026)

| Metric | Value |
|--------|-------|
| **Validation Events** | 163 |
| **Detection Accuracy** | 94.3% |
| **Mean Lead Time** | 43.2 ± 8.6 s |
| **False Positive Rate** | 1.7% |
| **Critical Threshold Ψ_c** | 2.0 |
| **Simulation Scale** | 10³ → 10⁹ nodes |

---

## 📐 ENTROPIA Parameters

| Parameter | Symbol | Units | Critical Threshold |
|-----------|--------|-------|--------------------|
| Data Density | ρ | bits·s⁻¹·m⁻³ | ρ < ρ_c |
| Critical Throughput | ρ_c | bits·s⁻¹·m⁻³ | System-specific |
| Dissipation Coefficient | Ψ | dimensionless | Ψ_c = 2.0 |
| Entropy Production Rate | σ | J·K⁻¹·m⁻³·s⁻¹ | dσ/dt > 0 |
| Collapse Lead Time | τ_collapse | seconds | τ > 30s |

---

## 📡 Dashboard Features

| Page | Description |
|------|-------------|
| `/` | Main landing page with ENTROPIA overview |
| `/dashboard` | Live Ψ-Dashboard with real-time monitoring |
| `/reports` | Daily, weekly, monthly reports archive |
| `/docs` | Complete documentation and API reference |

---

## 🔧 Local Development

```bash
# Clone repository
git clone https://github.com/gitdeeper10/entropia.git
cd entropia/Netlify

# Install Netlify CLI (optional)
npm install -g netlify-cli

# Set up environment variables
cp .env.example .env

# Start local server
netlify dev
# or simply open public/index.html in browser
```

---

🏗️ Project Structure

```
Netlify/
├── public/                 # Static files
│   ├── index.html         # Main landing page
│   ├── dashboard.html     # Ψ-Dashboard
│   ├── reports.html       # Reports archive
│   └── documentation.html # Documentation
├── package.json           # Project metadata
├── netlify.toml           # Netlify configuration
└── .env.example           # Environment variables template
```

---

📈 Validation Results

Environment Nodes Detection Rate Lead Time False Positive
E-ENV-01 10³ 100% N/A 0%
E-ENV-02 10⁵ 92.2% 38.7 ± 12.1s 2.3%
E-ENV-03 10⁹ 94.3% 43.2 ± 8.6s 1.7%
Combined — 93.9% 41.5 ± 11.2s 1.9%

---

📖 Citation

If you use ENTROPIA in your research, please cite:

```bibtex
@article{baladi2026entropia,
  title   = {ENTROPIA: Statistical Dynamics of Information Dissipation
             in Complex Non-Linear Digital Systems},
  author  = {Baladi, Samir},
  journal = {Entropy (MDPI)},
  year    = {2026},
  month   = {March},
  note    = {Manuscript submitted for review},
  url     = {https://entropia-lab.netlify.app},
  doi     = {10.5281/zenodo.19183878}
}
```

---

📬 Contact

· Author: Samir Baladi
· Email: gitdeeper@gmail.com
· ORCID: 0009-0003-8903-0029
· GitHub: github.com/gitdeeper10/entropia
· GitLab: gitlab.com/gitdeeper10/entropia
· DOI: 10.5281/zenodo.19183878

---

📜 License

MIT License — see LICENSE for details.

---

🔴 ENTROPIA — "When we learn to read entropy in our machines, we gain sovereignty over the digital world."
