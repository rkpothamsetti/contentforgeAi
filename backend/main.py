"""ContentForge AI — FastAPI backend with REST + WebSocket endpoints."""

from __future__ import annotations
import asyncio, json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ContentBrief, Pipeline, PipelineStage, ApprovalAction,
    AnalyticsOverview, WSEvent, ComplianceLevel,
)
from agents.orchestrator import Orchestrator


# ── In-memory state ──────────────────────────────────────────────────────────

pipelines: dict[str, Pipeline] = {}
ws_clients: dict[str, list[WebSocket]] = {}  # pipeline_id → list of sockets


async def broadcast(evt: WSEvent):
    """Send a WebSocket event to all clients subscribed to a pipeline."""
    msg = evt.model_dump_json()
    # Send to pipeline-specific subscribers
    for ws in ws_clients.get(evt.pipeline_id, []):
        try:
            await ws.send_text(msg)
        except Exception:
            pass
    # Send to global subscribers
    for ws in ws_clients.get("__global__", []):
        try:
            await ws.send_text(msg)
        except Exception:
            pass


orchestrator = Orchestrator(broadcast=broadcast)


# ── App ──────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="ContentForge AI",
    description="Multi-agent enterprise content operations platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ContentForge AI", "agents": 5}


@app.post("/api/pipeline/start")
async def start_pipeline(brief: ContentBrief):
    """Create and start a new content pipeline."""
    pipeline = Pipeline(brief=brief)
    pipelines[pipeline.id] = pipeline

    # Run pipeline in background so the request returns immediately
    asyncio.create_task(orchestrator.run(pipeline))

    return {
        "pipeline_id": pipeline.id,
        "status": pipeline.stage.value,
        "message": "Pipeline started",
    }


@app.get("/api/pipeline/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """Get full pipeline status and results."""
    p = pipelines.get(pipeline_id)
    if not p:
        raise HTTPException(404, "Pipeline not found")
    return p.model_dump()


@app.get("/api/pipelines")
async def list_pipelines():
    """List all pipelines."""
    return [
        {
            "id": p.id,
            "topic": p.brief.topic,
            "format": p.brief.format.value,
            "stage": p.stage.value,
            "created_at": p.created_at,
            "duration": p.total_duration_seconds,
        }
        for p in sorted(pipelines.values(), key=lambda x: x.created_at, reverse=True)
    ]


@app.post("/api/pipeline/{pipeline_id}/approve")
async def approve_pipeline(pipeline_id: str, action: ApprovalAction):
    """Human-in-the-loop approval gate."""
    p = pipelines.get(pipeline_id)
    if not p:
        raise HTTPException(404, "Pipeline not found")
    if p.stage != PipelineStage.AWAITING_APPROVAL:
        raise HTTPException(400, f"Pipeline is not awaiting approval (stage={p.stage.value})")

    if action.approved:
        asyncio.create_task(orchestrator.continue_after_approval(p))
        return {"message": "Approved — pipeline continuing", "pipeline_id": pipeline_id}
    else:
        p.stage = PipelineStage.REJECTED
        p.touch()
        await broadcast(
            WSEvent(
                pipeline_id=pipeline_id,
                event_type="stage_change",
                stage=PipelineStage.REJECTED,
                message=f"Pipeline rejected: {action.feedback}",
            )
        )
        return {"message": "Rejected", "feedback": action.feedback, "pipeline_id": pipeline_id}


@app.get("/api/analytics")
async def get_analytics():
    """Return aggregated analytics."""
    completed = [p for p in pipelines.values() if p.stage == PipelineStage.COMPLETED]
    total = len(pipelines)

    avg_cycle = 0.0
    avg_manual = 0.0
    compliance_passed = 0
    all_languages = set()
    all_channels = set()
    format_counts: dict[str, int] = {}

    for p in completed:
        avg_cycle += p.total_duration_seconds
        avg_manual += p.estimated_manual_hours
        if p.compliance_report and p.compliance_report.overall_status != ComplianceLevel.FAIL:
            compliance_passed += 1
        for lv in p.localized_versions:
            all_languages.add(lv.language)
        for d in p.distributions:
            all_channels.add(d.channel.value)
        fmt = p.brief.format.value
        format_counts[fmt] = format_counts.get(fmt, 0) + 1

    n = len(completed) or 1
    avg_cycle /= n
    avg_manual /= n

    # Time savings: manual hours → AI seconds
    time_savings = 0.0
    if avg_manual > 0:
        time_savings = round(
            (1 - (avg_cycle / 3600) / avg_manual) * 100, 1
        )

    return AnalyticsOverview(
        total_pipelines=total,
        completed_pipelines=len(completed),
        avg_cycle_time_seconds=round(avg_cycle, 1),
        avg_manual_equivalent_hours=round(avg_manual, 1),
        time_savings_percent=max(time_savings, 0),
        compliance_pass_rate=round(compliance_passed / n * 100, 1),
        languages_supported=len(all_languages) if all_languages else 2,
        channels_active=len(all_channels) if all_channels else 3,
        content_by_format=format_counts,
        recent_pipelines=[
            {
                "id": p.id,
                "topic": p.brief.topic,
                "stage": p.stage.value,
                "duration": p.total_duration_seconds,
            }
            for p in sorted(
                pipelines.values(), key=lambda x: x.created_at, reverse=True
            )[:10]
        ],
    ).model_dump()


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/pipeline/{pipeline_id}")
async def ws_pipeline(websocket: WebSocket, pipeline_id: str):
    await websocket.accept()
    ws_clients.setdefault(pipeline_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_clients[pipeline_id].remove(websocket)


@app.websocket("/ws/global")
async def ws_global(websocket: WebSocket):
    await websocket.accept()
    ws_clients.setdefault("__global__", []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients["__global__"].remove(websocket)


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
