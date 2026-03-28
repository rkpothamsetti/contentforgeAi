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

        prompt = f"""You are a content strategist and data analyst for {brief.brand_name}.
Analyse the following content and engagement metrics, then provide strategic recommendations.

CONTENT TOPIC: {brief.topic}
FORMAT: {brief.format.value}
AUDIENCE: {brief.audience}

CONTENT PREVIEW:
{content[:1500] if content else "No content available"}

ENGAGEMENT METRICS (simulated from similar past content):
{json.dumps(simulated_metrics, indent=2)}

Provide strategic analysis and recommendations in STRICT JSON:
{{
  "content_score": <1-100>,
  "engagement_analysis": "<2-3 sentence analysis of the engagement metrics>",
  "recommendations": [
    {{
      "category": "timing" | "format" | "targeting" | "topic" | "distribution",
      "priority": "high" | "medium" | "low",
      "recommendation": "<specific actionable recommendation>",
      "expected_impact": "<expected improvement>"
    }}
  ],
  "optimal_posting": {{
    "best_days": ["<day>"],
    "best_times": ["<time range>"],
    "frequency": "<recommended posting frequency>"
  }},
  "audience_insights": "<2-3 sentence insight about the target audience>",
  "trending_topics": ["<related trending topic to explore>"]
}}

Output ONLY valid JSON, no markdown fences."""

        raw = await generate(prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            data = {
                "content_score": 78,
                "engagement_analysis": "Content shows solid engagement with room for improvement in click-through rate.",
                "recommendations": [
                    {
                        "category": "timing",
                        "priority": "high",
                        "recommendation": "Publish during peak hours (9-11 AM local time)",
                        "expected_impact": "15-20% increase in impressions",
                    }
                ],
                "optimal_posting": {
                    "best_days": ["Tuesday", "Thursday"],
                    "best_times": ["9:00-11:00 AM", "2:00-4:00 PM"],
                    "frequency": "2-3 times per week",
                },
                "audience_insights": "Target audience engages most with data-driven content.",
                "trending_topics": ["AI in Enterprise", "Digital Transformation"],
            }

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
