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

        prompt = f"""You are a multi-channel content distribution specialist for {brief.brand_name}.
Adapt the following content for each target channel. Each channel has different requirements.

TARGET CHANNELS:
{json.dumps({ch.value: CHANNEL_META.get(ch, {}) for ch in channels}, indent=2)}

ORIGINAL CONTENT:
{content[:3000]}

For EACH channel, create an optimised version:
- Website/Blog: full article with SEO meta description
- Twitter/X: punchy tweet, max 280 chars, with hashtags
- LinkedIn: professional post with key insights, CTA
- Email: subject line + preview + formatted body
- Internal: concise summary for team comms
- Instagram: visual-first caption with hashtags

Respond in STRICT JSON:
{{
  "channels": [
    {{
      "channel": "<channel_value>",
      "formatted_content": "<the formatted content for this channel>",
      "metadata": {{"char_count": <n>, "hashtags": ["..."], "subject_line": "..." }}
    }}
  ]
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
            # Fallback
            data = {
                "channels": [
                    {
                        "channel": ch.value,
                        "formatted_content": f"[{ch.value} version of content]",
                        "metadata": {"char_count": len(content)},
                    }
                    for ch in channels
                ]
            }

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
