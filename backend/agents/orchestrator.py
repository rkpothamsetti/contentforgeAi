"""Pipeline Orchestrator — chains agents with human-in-the-loop gates."""

from __future__ import annotations
import asyncio, datetime
from typing import Callable, Awaitable
from models import Pipeline, PipelineStage, WSEvent, AgentStatus, ComplianceLevel

from agents.creator import CreatorAgent
from agents.compliance import ComplianceAgent
from agents.localizer import LocalizerAgent
from agents.distributor import DistributorAgent
from agents.intelligence import IntelligenceAgent


class Orchestrator:
    """Manages the sequential agent pipeline with approval gates."""

    def __init__(self, broadcast: Callable[[WSEvent], Awaitable[None]] | None = None):
        self.broadcast = broadcast or self._noop
        self.creator = CreatorAgent(broadcast=self.broadcast)
        self.compliance = ComplianceAgent(broadcast=self.broadcast)
        self.localizer = LocalizerAgent(broadcast=self.broadcast)
        self.distributor = DistributorAgent(broadcast=self.broadcast)
        self.intelligence = IntelligenceAgent(broadcast=self.broadcast)

    @staticmethod
    async def _noop(evt: WSEvent):
        pass

    async def _set_stage(self, pipeline: Pipeline, stage: PipelineStage):
        pipeline.stage = stage
        pipeline.touch()
        await self.broadcast(
            WSEvent(
                pipeline_id=pipeline.id,
                event_type="stage_change",
                stage=stage,
                message=f"Pipeline → {stage.value}",
            )
        )

    async def run(self, pipeline: Pipeline):
        """Execute the full pipeline. Pauses at compliance for human approval."""
        start = datetime.datetime.now()

        try:
            # ── Stage 1: Content Creation ────────────────────────────────
            await self._set_stage(pipeline, PipelineStage.CREATING)
            result = await self.creator.run(pipeline)
            pipeline.agent_results["creator"] = result
            if result.status == AgentStatus.FAILED:
                await self._set_stage(pipeline, PipelineStage.FAILED)
                return

            # ── Stage 2: Compliance Review ───────────────────────────────
            await self._set_stage(pipeline, PipelineStage.REVIEWING)
            result = await self.compliance.run(pipeline)
            pipeline.agent_results["compliance"] = result
            if result.status == AgentStatus.FAILED:
                await self._set_stage(pipeline, PipelineStage.FAILED)
                return

            # Check if compliance failed hard → need human approval
            if (
                pipeline.compliance_report
                and pipeline.compliance_report.overall_status == ComplianceLevel.FAIL
            ):
                await self._set_stage(pipeline, PipelineStage.AWAITING_APPROVAL)
                # Pipeline will be resumed when human approves
                return

            # Auto-approve if compliance passed or warning
            await self._continue_after_approval(pipeline, start)

        except Exception as e:
            await self._set_stage(pipeline, PipelineStage.FAILED)
            await self.broadcast(
                WSEvent(
                    pipeline_id=pipeline.id,
                    event_type="error",
                    message=f"Pipeline failed: {e}",
                )
            )

    async def continue_after_approval(self, pipeline: Pipeline):
        """Called when human approves compliance. Resumes the pipeline."""
        start_time_str = pipeline.created_at
        start = datetime.datetime.fromisoformat(start_time_str)
        await self._continue_after_approval(pipeline, start)

    async def _continue_after_approval(
        self, pipeline: Pipeline, start: datetime.datetime
    ):
        try:
            # ── Stage 3: Localisation ────────────────────────────────────
            await self._set_stage(pipeline, PipelineStage.LOCALIZING)
            result = await self.localizer.run(pipeline)
            pipeline.agent_results["localizer"] = result
            if result.status == AgentStatus.FAILED:
                await self._set_stage(pipeline, PipelineStage.FAILED)
                return

            # ── Stage 4: Distribution ────────────────────────────────────
            await self._set_stage(pipeline, PipelineStage.DISTRIBUTING)
            result = await self.distributor.run(pipeline)
            pipeline.agent_results["distributor"] = result
            if result.status == AgentStatus.FAILED:
                await self._set_stage(pipeline, PipelineStage.FAILED)
                return

            # ── Stage 5: Intelligence (runs in parallel, non-blocking) ──
            intel_result = await self.intelligence.run(pipeline)
            pipeline.agent_results["intelligence"] = intel_result

            # ── Complete ─────────────────────────────────────────────────
            end = datetime.datetime.now()
            pipeline.total_duration_seconds = round(
                (end - start).total_seconds(), 2
            )
            # Estimate manual equivalent
            pipeline.estimated_manual_hours = round(
                self._estimate_manual_hours(pipeline), 1
            )
            await self._set_stage(pipeline, PipelineStage.COMPLETED)

        except Exception as e:
            await self._set_stage(pipeline, PipelineStage.FAILED)
            await self.broadcast(
                WSEvent(
                    pipeline_id=pipeline.id,
                    event_type="error",
                    message=f"Pipeline failed: {e}",
                )
            )

    @staticmethod
    def _estimate_manual_hours(pipeline: Pipeline) -> float:
        """Estimate how long this would take manually."""
        hours = 0.0
        brief = pipeline.brief
        # Content creation
        hours += {"blog_post": 4, "social_media": 1.5, "email_newsletter": 2.5,
                  "press_release": 3, "sales_collateral": 3.5}.get(brief.format.value, 3)
        # Compliance review
        hours += 1.5
        # Localisation per language
        hours += len(brief.target_languages) * 3
        # Distribution per channel
        hours += len(brief.target_channels) * 0.5
        # Intelligence analysis
        hours += 2
        return hours
