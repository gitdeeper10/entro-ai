"""
Unit tests for ENTRO-AI core module
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entro_ai.core import (
    compute_veff_ai,
    compute_rho_ratio,
    compute_psi,
    compute_kappa,
    compute_tau_collapse,
    get_edt_level,
    EntroAIMonitor
)


class TestCore(unittest.TestCase):
    
    def test_compute_veff_ai(self):
        """Test Eq. 12: V_eff(AI) calculation"""
        veff = compute_veff_ai(
            kv_cache_gb=40.0,
            attn_flops_tflops=1979.0,
            gpu_mem_bw_tbs=3.35,
            n_layers=32,
            d_model=4096
        )
        self.assertGreater(veff, 0)
        self.assertIsInstance(veff, float)
    
    def test_compute_rho_ratio(self):
        """Test ρ/ρ_c calculation"""
        veff = 1e12
        rho_ratio = compute_rho_ratio(
            token_rate=800,
            context_length=8192,
            veff=veff,
            rho_c=1.0
        )
        self.assertGreater(rho_ratio, 0)
        self.assertIsInstance(rho_ratio, float)
    
    def test_compute_psi(self):
        """Test Dissipation Coefficient Ψ calculation"""
        psi = compute_psi(
            rho_ratio=0.8,
            s_total=0.5,
            s_max=1.0
        )
        self.assertGreater(psi, 0)
        self.assertIsInstance(psi, float)
        
        # Test super-critical regime
        psi_inf = compute_psi(rho_ratio=1.1, s_total=0.5, s_max=1.0)
        self.assertEqual(psi_inf, float('inf'))
    
    def test_compute_kappa(self):
        """Test output coherence κ calculation"""
        kappa = compute_kappa(psi=1.0, psi_c=2.0)
        self.assertGreater(kappa, 0)
        self.assertLess(kappa, 1)
        
        # Test collapse
        kappa_collapse = compute_kappa(psi=2.0, psi_c=2.0)
        self.assertEqual(kappa_collapse, 0.0)
    
    def test_compute_tau_collapse(self):
        """Test collapse lead time calculation"""
        tau = compute_tau_collapse(
            psi=1.5,
            dpsi_dt=0.05,
            psi_c=2.0,
            min_tau=1.0,
            max_tau=3600.0
        )
        self.assertGreater(tau, 0)
        self.assertLessEqual(tau, 3600)
        
        # Test decreasing psi (no collapse)
        tau_decreasing = compute_tau_collapse(psi=1.5, dpsi_dt=-0.05)
        self.assertEqual(tau_decreasing, 3600.0)
    
    def test_get_edt_level(self):
        """Test EDT level determination"""
        self.assertEqual(get_edt_level(psi=1.0), 0)  # None
        self.assertEqual(get_edt_level(psi=1.6), 1)  # L1
        self.assertEqual(get_edt_level(psi=1.8), 2)  # L2
        self.assertEqual(get_edt_level(psi=1.9), 3)  # L3
        self.assertEqual(get_edt_level(psi=2.1), 4)  # L4
    
    def test_entro_ai_monitor(self):
        """Test EntroAIMonitor integration"""
        monitor = EntroAIMonitor(
            architecture="transformer_llm",
            n_layers=32,
            d_model=4096,
            kv_cache_gb=40.0
        )
        
        state = monitor.update(
            kv_cache_used=0.75,
            attn_flops_util=0.70,
            token_rate=800,
            context_length=8192,
            gpu_mem_util=0.70
        )
        
        self.assertIsNotNone(state)
        self.assertGreaterEqual(state.rho_ratio, 0)
        self.assertGreaterEqual(state.psi, 0)
        self.assertGreaterEqual(state.kappa, 0)
        self.assertGreaterEqual(state.tau_collapse, 0)
    
    def test_is_critical(self):
        """Test critical regime detection"""
        monitor = EntroAIMonitor()
        
        # Normal regime
        monitor.update(
            kv_cache_used=0.5,
            attn_flops_util=0.5,
            token_rate=400,
            context_length=4096,
            gpu_mem_util=0.5
        )
        self.assertFalse(monitor.is_critical())
        
        # Simulate high psi (would need high load)
        monitor.state.psi = 2.5
        self.assertTrue(monitor.is_critical())


if __name__ == "__main__":
    unittest.main()
