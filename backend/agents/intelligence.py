"""Content Intelligence Agent — analyses engagement and recommends strategy."""

from __future__ import annotations
import json, random
from agents.base import BaseAgent
from models import Pipeline
from ai_client import generate


class IntelligenceAgent(BaseAgent):
    name = "intelligence"
    display_name = "Content Intelligence"

    async def execute(self, pipeline: Pipeline) -> dict:
        brief = pipeline.brief
        content = pipeline.reviewed_content or pipeline.draft_content

        # Simulate engagement metrics (in a real system these come from analytics APIs)
        simulated_metrics = {
            "impressions": random.randint(5000, 50000),
            "clicks": random.randint(200, 5000),
            "shares": random.randint(20, 500),
            "comments": random.randint(5, 100),
            "avg_read_time_seconds": random.randint(30, 300),
            "bounce_rate": round(random.uniform(0.15, 0.65), 2),
            "conversion_rate": round(random.uniform(0.01, 0.08), 3),
        }

        await self.emit(
            pipeline.id, "log", "Analysing content performance patterns…"
        )

        prompt = f"""You are the Lead Growth Strategist for {brief.brand_name}. 
Your task is to analyze the following content and engagement metrics to provide high-impact strategic recommendations.

CONTEXT:
Topic: {brief.topic}
Format: {brief.format.value}
Target Audience: {brief.audience}

CONTENT PREVIEW:
{content[:1500] if content else "No content available"}

SIMULATED PERFORMANCE DATA:
{json.dumps(simulated_metrics, indent=2)}

Response Format (MANDATORY JSON):
{{
  "content_score": <1-100>,
  "engagement_analysis": "<strategic analysis of why these metrics look the way they do>",
  "recommendations": [
    {{
      "category": "timing" | "format" | "targeting" | "topic" | "distribution",
      "priority": "high" | "medium" | "low",
      "recommendation": "<very specific actionable step>",
      "expected_impact": "<quantified expected improvement>"
    }}
  ],
  "optimal_posting": {{
    "best_days": ["Monday", "Wednesday"],
    "best_times": ["10:00 AM", "4:00 PM"],
    "frequency": "Daily / Weekly / Monthly"
  }},
  "audience_insights": "<deep insight into audience behavior>",
  "trending_topics": ["<related high-growth topic>"]
}}

Output ONLY valid JSON. No markdown fences. No introduction. No conclusion."""

        raw = await generate(prompt)
        data = self._parse_json(raw)

        await self.emit(
            pipeline.id,
            "log",
            f"Content score: {data.get('content_score', 'N/A')}/100 | "
            f"{len(data.get('recommendations', []))} strategic recommendations",
        )

        return {
            "metrics": simulated_metrics,
            "intelligence": data,
        }
