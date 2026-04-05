"""
Ψ-Dashboard AI Extension
Real-time entropy monitoring for LLM inference
"""

import time
import json
from typing import Dict, Optional, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entro_ai.core import EntroAIMonitor
from entro_ai.architecture import list_architectures, get_architecture_info


app = FastAPI(
    title="ENTRO-AI Ψ-Dashboard",
    description="Real-time entropy monitoring for LLM inference",
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

# Templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# State
monitor: Optional[EntroAIMonitor] = None
websocket_clients: List[WebSocket] = []


class TelemetryUpdate(BaseModel):
    """Telemetry update from inference engine"""
    kv_cache_used: float
    attn_flops_util: float
    token_rate: float
    context_length: int
    gpu_mem_util: float


class DashboardState(BaseModel):
    """Current dashboard state"""
    psi: float
    kappa: float
    rho_ratio: float
    tau_collapse: float
    edt_level: int
    quality_level: str
    is_critical: bool
    architecture: str
    timestamp: float


@app.on_event("startup")
async def startup_event():
    """Initialize dashboard on startup"""
    global monitor
    monitor = EntroAIMonitor(architecture="transformer_llm")
    print("[Dashboard] Initialized")


@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Main dashboard page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ENTRO-AI Ψ-Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #eee;
                min-height: 100vh;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { 
                text-align: center; 
                margin-bottom: 10px;
                font-size: 2.5em;
                color: #ff4444;
            }
            .subtitle { text-align: center; margin-bottom: 30px; color: #888; }
            .dashboard {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }
            .card h3 { margin-bottom: 15px; color: #ff6666; }
            .metric {
                font-size: 2.5em;
                font-weight: bold;
                text-align: center;
                margin: 15px 0;
            }
            .metric.safe { color: #00ff88; }
            .metric.warning { color: #ffaa44; }
            .metric.critical { color: #ff4444; }
            .label { text-align: center; color: #aaa; font-size: 0.9em; }
            .gauge {
                width: 200px;
                height: 100px;
                margin: 20px auto;
                position: relative;
            }
            .gauge-bar {
                width: 100%;
                height: 20px;
                background: #333;
                border-radius: 10px;
                overflow: hidden;
            }
            .gauge-fill {
                height: 100%;
                width: 0%;
                transition: width 0.3s ease;
            }
            .gauge-fill.safe { background: #00ff88; }
            .gauge-fill.warning { background: #ffaa44; }
            .gauge-fill.critical { background: #ff4444; }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                margin-top: 10px;
            }
            .status.critical { background: #ff4444; color: white; }
            .status.warning { background: #ffaa44; color: #333; }
            .status.safe { background: #00ff88; color: #333; }
            .footer {
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                color: #666;
                font-size: 0.8em;
            }
            .arch-badge {
                background: #ff4444;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.7em;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔴 Ψ-Dashboard <span class="arch-badge" id="architecture">transformer_llm</span></h1>
            <div class="subtitle">Real-time Entropy Monitoring for LLM Inference</div>
            
            <div class="dashboard">
                <div class="card">
                    <h3>Dissipation Coefficient Ψ</h3>
                    <div class="metric" id="psi">0.00</div>
                    <div class="gauge">
                        <div class="gauge-bar">
                            <div class="gauge-fill" id="psi-gauge" style="width:0%"></div>
                        </div>
                    </div>
                    <div class="label">Critical threshold: 2.0</div>
                </div>
                
                <div class="card">
                    <h3>Output Coherence κ</h3>
                    <div class="metric" id="kappa">0.00</div>
                    <div class="gauge">
                        <div class="gauge-bar">
                            <div class="gauge-fill safe" id="kappa-gauge" style="width:0%"></div>
                        </div>
                    </div>
                    <div class="label">Collapse threshold: 0.12</div>
                </div>
                
                <div class="card">
                    <h3>τ_collapse</h3>
                    <div class="metric" id="tau">∞</div>
                    <div class="label">Seconds until collapse</div>
                </div>
                
                <div class="card">
                    <h3>System Status</h3>
                    <div style="text-align: center;">
                        <div class="status" id="status">🟢 NORMAL</div>
                    </div>
                    <div style="margin-top: 15px;">
                        <div>ρ/ρ_c: <span id="rho_ratio">0.00</span></div>
                        <div>EDT Level: <span id="edt_level">0</span></div>
                        <div>Quality: <span id="quality">—</span></div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                ENTRO-AI | Builds on ENTROPIA (E-LAB-01) | DOI: 10.5281/zenodo.19416737
            </div>
        </div>
        
        <script>
            let ws = null;
            
            function connect() {
                const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${location.host}/ws`);
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };
                
                ws.onclose = function() {
                    setTimeout(connect, 1000);
                };
            }
            
            function updateDashboard(data) {
                // Update Ψ
                document.getElementById('psi').textContent = data.psi.toFixed(3);
                const psiPercent = Math.min(100, (data.psi / 2.5) * 100);
                const psiGauge = document.getElementById('psi-gauge');
                psiGauge.style.width = psiPercent + '%';
                psiGauge.className = 'gauge-fill ' + (data.psi >= 2.0 ? 'critical' : (data.psi >= 1.5 ? 'warning' : 'safe'));
                
                // Update κ
                document.getElementById('kappa').textContent = data.kappa.toFixed(3);
                document.getElementById('kappa-gauge').style.width = (data.kappa * 100) + '%';
                
                // Update τ
                const tau = data.tau_collapse;
                document.getElementById('tau').textContent = tau < 3600 ? tau.toFixed(1) + 's' : '∞';
                
                // Update status
                const statusEl = document.getElementById('status');
                if (data.psi >= 2.0) {
                    statusEl.textContent = '🔴 CRITICAL - Collapse Imminent';
                    statusEl.className = 'status critical';
                } else if (data.psi >= 1.5) {
                    statusEl.textContent = '🟠 WARNING - EDT Active';
                    statusEl.className = 'status warning';
                } else {
                    statusEl.textContent = '🟢 NORMAL - Steady State';
                    statusEl.className = 'status safe';
                }
                
                // Update other metrics
                document.getElementById('rho_ratio').textContent = data.rho_ratio.toFixed(3);
                document.getElementById('edt_level').textContent = data.edt_level;
                document.getElementById('quality').textContent = data.quality_level;
                document.getElementById('architecture').textContent = data.architecture;
            }
            
            connect();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        while True:
            # Wait for message (keep connection alive)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)


async def broadcast_state(state: DashboardState):
    """Broadcast state to all WebSocket clients"""
    if not websocket_clients:
        return
    
    data = state.dict()
    for client in websocket_clients[:]:
        try:
            await client.send_json(data)
        except:
            websocket_clients.remove(client)


@app.get("/api/state")
async def get_state():
    """Get current dashboard state as JSON"""
    global monitor
    
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    state = monitor.get_state()
    
    # Determine quality level
    if state.kappa >= 0.8:
        quality = "Excellent"
    elif state.kappa >= 0.6:
        quality = "Good"
    elif state.kappa >= 0.4:
        quality = "Moderate"
    elif state.kappa >= 0.2:
        quality = "Poor"
    else:
        quality = "Collapse Imminent"
    
    return DashboardState(
        psi=state.psi,
        kappa=state.kappa,
        rho_ratio=state.rho_ratio,
        tau_collapse=state.tau_collapse,
        edt_level=state.edt_level,
        quality_level=quality,
        is_critical=state.psi >= 2.0,
        architecture=monitor.architecture,
        timestamp=time.time()
    )


@app.post("/api/telemetry")
async def update_telemetry(telemetry: TelemetryUpdate):
    """Update telemetry and broadcast new state"""
    global monitor
    
    if monitor is None:
        raise HTTPException(status_code=503, detail="Monitor not initialized")
    
    state = monitor.update(
        kv_cache_used=telemetry.kv_cache_used,
        attn_flops_util=telemetry.attn_flops_util,
        token_rate=telemetry.token_rate,
        context_length=telemetry.context_length,
        gpu_mem_util=telemetry.gpu_mem_util,
        timestamp=time.time()
    )
    
    # Determine quality level
    if state.kappa >= 0.8:
        quality = "Excellent"
    elif state.kappa >= 0.6:
        quality = "Good"
    elif state.kappa >= 0.4:
        quality = "Moderate"
    elif state.kappa >= 0.2:
        quality = "Poor"
    else:
        quality = "Collapse Imminent"
    
    dashboard_state = DashboardState(
        psi=state.psi,
        kappa=state.kappa,
        rho_ratio=state.rho_ratio,
        tau_collapse=state.tau_collapse,
        edt_level=state.edt_level,
        quality_level=quality,
        is_critical=state.psi >= 2.0,
        architecture=monitor.architecture,
        timestamp=time.time()
    )
    
    # Broadcast to WebSocket clients
    await broadcast_state(dashboard_state)
    
    return dashboard_state


@app.get("/api/architectures")
async def list_architectures_api():
    """List available architectures"""
    return {"architectures": list_architectures()}


@app.post("/api/architecture/{arch}")
async def set_architecture(arch: str):
    """Change architecture"""
    global monitor
    
    if arch not in list_architectures():
        raise HTTPException(status_code=400, detail=f"Unknown architecture: {arch}")
    
    info = get_architecture_info(arch)
    monitor = EntroAIMonitor(architecture=arch)
    
    return {"architecture": arch, "n": info.n, "description": info.description}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
