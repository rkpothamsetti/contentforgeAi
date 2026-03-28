"""Distribution Agent — formats and simulates publishing to channels."""

from __future__ import annotations
import json
from agents.base import BaseAgent
from models import Pipeline, Channel, ChannelDistribution
from ai_client import generate


CHANNEL_META = {
    Channel.WEBSITE: {"platform": "Company Website / Blog", "max_len": 5000},
    Channel.TWITTER: {"platform": "Twitter / X", "max_len": 280},
    Channel.LINKEDIN: {"platform": "LinkedIn", "max_len": 3000},
    Channel.EMAIL: {"platform": "Email Newsletter", "max_len": 4000},
    Channel.INTERNAL: {"platform": "Internal Comms (Slack/Teams)", "max_len": 2000},
    Channel.INSTAGRAM: {"platform": "Instagram", "max_len": 2200},
}


class DistributorAgent(BaseAgent):
    name = "distributor"
    display_name = "Distributor"

    async def execute(self, pipeline: Pipeline) -> dict:
        brief = pipeline.brief
        content = pipeline.reviewed_content or pipeline.draft_content
        channels = brief.target_channels

        if not content:
            raise ValueError("No content to distribute")

        distributions: list[ChannelDistribution] = []

        channels_str = ", ".join(
            CHANNEL_META.get(ch, {}).get("platform", ch.value)
            for ch in channels
        )

        await self.emit(
            pipeline.id, "log", f"Formatting content for: {channels_str}"
        )

        prompt = f"""You are a senior social media and distribution specialist for {brief.brand_name}.
Your mission is to adapt the core content for each specific target channel with surgery-like precision.

CHANNELS TO OPTIMIZE FOR:
{json.dumps({ch.value: CHANNEL_META.get(ch, {}) for ch in channels}, indent=2)}

SOURCE CONTENT:
{content[:3000]}

STRICT FORMATTING GUIDELINES:
1. Twitter/X: MUST BE UNDER 280 CHARACTERS. Include 2-3 relevant hashtags. Make it a hook that drives a click.
2. LinkedIn: Professional tone. Use a "scroll-stoppping" opening sentence. Include 3-4 bullet points of value. End with a CTA.
3. Website/Blog: Full, rich formatting. Include an SEO-optimized meta description (max 160 chars) at the start.
4. Email: Subject line MUST be catchy. Body must be structured for quick scanning.
5. Internal: Summary style. Focus on "Why this matters to us".
6. Instagram: Focus on the "vibe" and engagement. Use bullet points and lots of hashtags.

Response Format (MANDATORY JSON):
{{
  "channels": [
    {{
      "channel": "<channel_id>",
      "formatted_content": "<platform-specific text>",
      "metadata": {{"char_count": <n>, "hashtags": ["..."], "subject_line": "...", "meta_description": "..." }}
    }}
  ]
}}

Output ONLY valid JSON. No preamble. No markdown code blocks."""

        raw = await generate(prompt)
        data = self._parse_json(raw)

        for ch_data in data.get("channels", []):
            try:
                channel = Channel(ch_data["channel"])
            except ValueError:
                continue
            distributions.append(
                ChannelDistribution(
                    channel=channel,
                    status="published",
                    formatted_content=ch_data.get("formatted_content", ""),
                    metadata=ch_data.get("metadata", {}),
                )
            )

        # Fill any missing channels
        distributed_channels = {d.channel for d in distributions}
        for ch in channels:
            if ch not in distributed_channels:
                distributions.append(
                    ChannelDistribution(
                        channel=ch,
                        status="published",
                        formatted_content=f"[{ch.value} version]",
                        metadata={},
                    )
                )

        pipeline.distributions = distributions

        await self.emit(
            pipeline.id,
            "log",
            f"Published to {len(distributions)} channels successfully",
        )

        return {
            "channels_published": len(distributions),
            "channel_list": [d.channel.value for d in distributions],
        }
