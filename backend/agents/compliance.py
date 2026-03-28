"""Compliance Review Agent — checks content against brand & regulatory guidelines."""

from __future__ import annotations
import json
from agents.base import BaseAgent
from models import (
    Pipeline, ComplianceReport, ComplianceFinding, ComplianceLevel
)
from ai_client import generate


class ComplianceAgent(BaseAgent):
    name = "compliance"
    display_name = "Compliance Reviewer"

    async def execute(self, pipeline: Pipeline) -> dict:
        brief = pipeline.brief
        content = pipeline.draft_content

        if not content:
            raise ValueError("No draft content to review")

        prompt = f"""You are the Chief Compliance & Quality Officer for {brief.brand_name}. 
Your task is to perform a rigorous compliance and brand alignment audit of the following content.

AUDIT CRITERIA:
1. BRAND TONE: Must be "{brief.tone}". Flag any sentences that deviate.
2. ACCURACY: Content must correctly reference {brief.brand_name}.
3. PROHIBITED: No competitor names, no "best in class" without proof, no offensive language.
4. LEGAL: Ensure any statistics or claims have a supporting context or disclaimer.

CONTENT TO AUDIT:
{content[:4000]}

Response Format (MANDATORY JSON):
{{
  "overall_status": "pass" | "warning" | "fail",
  "score": <0-100>,
  "findings": [
    {{
      "category": "brand_tone" | "legal" | "regulatory" | "terminology",
      "severity": "pass" | "warning" | "fail",
      "description": "<detailed explanation of the issue>",
      "suggestion": "<how to fix it>",
      "location": "<exact quote from the text>"
    }}
  ],
  "auto_fixes_applied": <int>,
  "reviewed_content": "<the full content with minor fixes applied>"
}}

If the content is perfect, provide 1-2 positive observations in the findings with severity "pass".
Output ONLY valid JSON. No markdown code blocks. No preamble."""

        await self.emit(
            pipeline.id, "log", "Scanning for brand, legal & regulatory compliance…"
        )

        raw = await generate(prompt)
        data = self._parse_json(raw)

        findings = []
        for f in data.get("findings", []):
            try:
                # Ensure all required fields exist with defaults to avoid Pydantic errors
                findings.append(ComplianceFinding(
                    category=f.get("category", "brand_tone"),
                    severity=ComplianceLevel(f.get("severity", "pass").lower()),
                    description=f.get("description", "Observation made during audit"),
                    suggestion=f.get("suggestion", "No action required"),
                    location=f.get("location", "")
                ))
            except Exception:
                continue

        report = ComplianceReport(
            overall_status=ComplianceLevel(data.get("overall_status", "pass").lower()),
            score=data.get("score", 85),
            findings=findings,
            auto_fixes_applied=data.get("auto_fixes_applied", 0),
            reviewed_content=data.get("reviewed_content", content),
        )

        pipeline.compliance_report = report
        pipeline.reviewed_content = report.reviewed_content or content

        fail_count = sum(1 for f in findings if f.severity == ComplianceLevel.FAIL)
        warn_count = sum(1 for f in findings if f.severity == ComplianceLevel.WARNING)

        await self.emit(
            pipeline.id,
            "log",
            f"Compliance score: {report.score}/100 | "
            f"{fail_count} failures, {warn_count} warnings, "
            f"{report.auto_fixes_applied} auto-fixes",
        )

        return {
            "overall_status": report.overall_status.value,
            "score": report.score,
            "findings_count": len(findings),
            "fail_count": fail_count,
            "warning_count": warn_count,
            "auto_fixes": report.auto_fixes_applied,
        }
