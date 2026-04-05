"""ENTRO-AI Architecture Calibration Tools

Provides calibration protocols for:
- Transformer LLMs (n = 1.63)
- BERT-class encoders (n = 1.58)
- CNN/ViT (n = 1.74)
- Neuromorphic SNNs (n = 1.42)
"""

from calibration.transformer_calibrator import TransformerCalibrator, CalibrationResult
from calibration.bert_calibrator import BertCalibrator, BertCalibrationResult
from calibration.neuromorphic_calibrator import NeuromorphicCalibrator, NeuromorphicCalibrationResult

__all__ = [
    "TransformerCalibrator",
    "CalibrationResult",
    "BertCalibrator", 
    "BertCalibrationResult",
    "NeuromorphicCalibrator",
    "NeuromorphicCalibrationResult"
]
