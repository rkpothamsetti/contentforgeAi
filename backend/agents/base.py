"""Base agent class with timing, event emission, and error handling."""

from __future__ import annotations
import asyncio, datetime, traceback
from typing import TYPE_CHECKING
from models import AgentResult, AgentStatus, WSEvent

if TYPE_CHECKING:
    from models import Pipeline


class BaseAgent:
    """Abstract base for all ContentForge agents."""

    name: str = "base_agent"
    display_name: str = "Base Agent"

    def __init__(self, broadcast=None):
        self.broadcast = broadcast  # async fn to send WSEvents

    async def emit(self, pipeline_id: str, event_type: str, message: str, **data):
        if self.broadcast:
            evt = WSEvent(
                pipeline_id=pipeline_id,
                event_type=event_type,
                agent_name=self.name,
                message=message,
                data=data,
            )
            await self.broadcast(evt)

    async def run(self, pipeline: "Pipeline") -> AgentResult:
        start = datetime.datetime.now()
        await self.emit(pipeline.id, "agent_start", f"{self.display_name} started")

        try:
            output = await self.execute(pipeline)
            end = datetime.datetime.now()
            duration = (end - start).total_seconds()

            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                started_at=start.isoformat(),
                completed_at=end.isoformat(),
                duration_seconds=round(duration, 2),
                output=output if isinstance(output, dict) else {"result": str(output)},
            )
            await self.emit(
                pipeline.id,
                "agent_complete",
                f"{self.display_name} completed in {duration:.1f}s",
                duration=duration,
            )
            return result

        except Exception as e:
            end = datetime.datetime.now()
            duration = (end - start).total_seconds()
            await self.emit(
                pipeline.id, "agent_error", f"{self.display_name} failed: {e}"
            )
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                started_at=start.isoformat(),
                completed_at=end.isoformat(),
                duration_seconds=round(duration, 2),
                error=f"{e}\n{traceback.format_exc()}",
            )

    async def execute(self, pipeline: "Pipeline") -> dict:
        raise NotImplementedError
