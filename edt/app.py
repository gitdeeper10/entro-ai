"""
EDT Controller FastAPI Application
Entropy-Driven Throttling microservice for AI inference
"""

import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entro_ai.core import EntroAIMonitor, compute_psi, get_edt_level
from entro_ai.edt_controller import EDTController, EDTLevel, get_intervention


app = FastAPI(
    title="ENTRO-AI EDT Controller",
    description="Entropy-Driven Throttling microservice for LLM inference",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class TelemetryData(BaseModel):
    """Inference telemetry from LLM server"""
    kv_cache_used: float  # 0-1
    attn_flops_util: float  # 0-1
    token_rate: float  # tokens/second
    context_length: int  # tokens
    gpu_mem_util: float  # 0-1
    timestamp: Optional[float] = None


class EDTStatusResponse(BaseModel):
    """EDT controller status response"""
    current_psi: float
    current_level: int
    level_name: str
    intervention_description: Optional[str]
    intervention_active: bool
    tau_collapse: float
    kappa: float
    is_critical: bool


class InterventionRequest(BaseModel):
    """Request to apply intervention"""
    level: int
    reason: str


class InterventionResponse(BaseModel):
    """Intervention application response"""
    applied: bool
    level: int
    action: str
    message: str


# Global controller instance
controller: Optional[EDTController] = None
monitor: Optional[EntroAIMonitor] = None


@app.on_event("startup")
async def startup_event():
    """Initialize controller on startup"""
    global controller, monitor
    controller = EDTController(architecture="transformer_llm", auto_recover=True)
    monitor = EntroAIMonitor(architecture="transformer_llm")
    print("[EDT] Controller initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ENTRO-AI EDT Controller"}


@app.post("/telemetry")
async def ingest_telemetry(data: TelemetryData, background_tasks: BackgroundTasks):
    """
    Ingest inference telemetry and update thermodynamic state
    """
    global controller, monitor
    
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    timestamp = data.timestamp or time.time()
    
    # Update monitor state
    state = monitor.update(
        kv_cache_used=data.kv_cache_used,
        attn_flops_util=data.attn_flops_util,
        token_rate=data.token_rate,
        context_length=data.context_length,
        gpu_mem_util=data.gpu_mem_util,
        timestamp=timestamp
    )
    
    # Update controller
    if controller:
        controller.update_psi(state.psi, timestamp)
    
    return {
        "status": "ok",
        "psi": state.psi,
        "kappa": state.kappa,
        "tau_collapse": state.tau_collapse,
        "edt_level": state.edt_level
    }


@app.get("/status", response_model=EDTStatusResponse)
async def get_status():
    """Get current EDT controller status"""
    global controller, monitor
    
    if controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    status = controller.get_status()
    current_intervention = controller.get_current_intervention()
    
    return EDTStatusResponse(
        current_psi=status["current_psi"],
        current_level=status["current_level"],
        level_name=EDTLevel(status["current_level"]).name if status["current_level"] in [0,1,2,3,4] else "UNKNOWN",
        intervention_description=current_intervention.description if current_intervention else None,
        intervention_active=status["is_active"],
        tau_collapse=monitor.state.tau_collapse if monitor else 0,
        kappa=monitor.state.kappa if monitor else 0,
        is_critical=status["current_psi"] >= 2.0
    )


@app.post("/intervention/{level}")
async def apply_intervention(level: int, request: InterventionRequest):
    """
    Manually apply an EDT intervention
    """
    global controller
    
    if controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    try:
        edt_level = EDTLevel(level)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {level}")
    
    intervention = get_intervention(edt_level)
    if intervention is None:
        raise HTTPException(status_code=400, detail=f"No intervention defined for level {level}")
    
    # Log intervention
    print(f"[EDT] Manual intervention Level {level}: {intervention.action} - Reason: {request.reason}")
    
    return InterventionResponse(
        applied=True,
        level=level,
        action=intervention.action,
        message=f"Intervention applied: {intervention.description}"
    )


@app.post("/reset")
async def reset_controller():
    """Reset EDT controller (clear interventions)"""
    global controller
    
    if controller is None:
        raise HTTPException(status_code=503, detail="Controller not initialized")
    
    controller.current_level = EDTLevel.NONE
    controller.current_intervention_magnitude = 0.0
    controller.recovery_start_time = None
    
    return {"status": "reset", "message": "Controller reset to normal operation"}


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    global controller, monitor
    
    metrics = []
    
    if controller:
        metrics.append(f"entro_ai_psi {controller.current_psi:.6f}")
        metrics.append(f"entro_ai_edt_level {controller.current_level}")
        metrics.append(f"entro_ai_intervention_active {1 if controller.is_intervention_active() else 0}")
    
    if monitor:
        metrics.append(f"entro_ai_kappa {monitor.state.kappa:.6f}")
        metrics.append(f"entro_ai_tau_collapse {monitor.state.tau_collapse:.6f}")
        metrics.append(f"entro_ai_rho_ratio {monitor.state.rho_ratio:.6f}")
    
    return "\n".join(metrics)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
