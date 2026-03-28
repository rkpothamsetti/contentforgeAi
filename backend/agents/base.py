"""Base agent class with timing, event emission, and error handling."""

from __future__ import annotations
import asyncio, datetime, traceback, json, re
from typing import TYPE_CHECKING
from models import AgentResult, AgentStatus, WSEvent

if TYPE_CHECKING:
    from models import Pipeline


class BaseAgent:
    """Abstract base for all ContentForge agents."""

    name: str = "base_agent"
    display_name: str = "Base Agent"

    def _parse_json(self, raw: str) -> dict:
        """Robustly extract JSON from a string that may contain markdown or preamble."""
        # Try to find content between ```json and ```
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1)
        else:
            # Fallback: find the first { and last }
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                cleaned = raw[start : end + 1]
            else:
                cleaned = raw.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Last ditch: try to clean up common issues
            # 1. Handle literal newlines in strings (very common in LLaMA)
            # This is tricky without a full parser, but we can try to escape them
            # if they are between double quotes.
            
            # Simple approach: if it fails, try to replace literal newlines with \n
            # but only if they are not followed by a quote or something that looks like JSON structure
            attempt = cleaned.replace("\n", "\\n")
            # But wait, we might have just escaped the actual structure!
            # Let's try to find text before the last } and just keep that
            
            cleaned = cleaned.strip()
            # If it ends with something other than } or ], try to find the last valid closer
            last_brace = cleaned.rfind("}")
            last_bracket = cleaned.rfind("]")
            end_pos = max(last_brace, last_bracket)
            if end_pos != -1:
                cleaned = cleaned[:end_pos + 1]
            
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # If it still fails, it might be the literal newlines.
                # Let's try the simple escape and see if it works.
                try:
                    return json.loads(cleaned.replace("\n", "\\n"))
                except json.JSONDecodeError:
                    raise ValueError(f"JSON Parse Error. Cleaned content: {cleaned[:100]}...")

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
