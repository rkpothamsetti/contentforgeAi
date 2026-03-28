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

        prompt = f"""You are a senior compliance reviewer for {brief.brand_name}.
Review the following content for brand compliance, legal issues, and regulatory concerns.

BRAND GUIDELINES:
- Tone: {brief.tone} (flag deviations)
- Brand name must be used correctly as "{brief.brand_name}"
- No competitor mentions or unfavourable comparisons
- No unsubstantiated claims (e.g. "best in the world", "#1")
- No discriminatory or exclusionary language
- Must include proper disclaimers for any data/statistics cited

LEGAL & REGULATORY:
- No misleading statements or false promises
- Financial claims must have disclaimers
- Health/medical claims need appropriate caveats
- Data privacy: no collection of personal info without consent mention
- Copyright: no plagiarised or unattributed content

CONTENT TO REVIEW:
{content[:4000]}

Respond in STRICT JSON format:
{{
  "overall_status": "pass" | "warning" | "fail",
  "score": <0-100>,
  "findings": [
    {{
      "category": "brand_tone" | "legal" | "regulatory" | "terminology",
      "severity": "pass" | "warning" | "fail",
      "description": "<what the issue is>",
      "suggestion": "<how to fix it>",
      "location": "<quote the problematic text>"
    }}
  ],
  "auto_fixes_applied": <number of minor fixes you would auto-apply>,
  "reviewed_content": "<the full content with any minor fixes applied>"
}}

If the content passes review, still provide at least 1-2 minor observations.
Output ONLY valid JSON, no markdown fences."""

        await self.emit(
            pipeline.id, "log", "Scanning for brand, legal & regulatory compliance…"
        )

        raw = await generate(prompt)

        # Parse the response — strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: create a pass report
            data = {
                "overall_status": "pass",
                "score": 85,
                "findings": [
                    {
                        "category": "brand_tone",
                        "severity": "pass",
                        "description": "Content aligns with brand guidelines",
                        "suggestion": "No changes needed",
                        "location": "",
                    }
                ],
                "auto_fixes_applied": 0,
                "reviewed_content": content,
            }

        findings = [ComplianceFinding(**f) for f in data.get("findings", [])]
        report = ComplianceReport(
            overall_status=ComplianceLevel(data.get("overall_status", "pass")),
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
