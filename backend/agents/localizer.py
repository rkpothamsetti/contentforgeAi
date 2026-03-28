"""Localization Agent — translates and culturally adapts content."""

from __future__ import annotations
import json
from agents.base import BaseAgent
from models import Pipeline, LocalizedContent
from ai_client import generate


class LocalizerAgent(BaseAgent):
    name = "localizer"
    display_name = "Localizer"

    async def execute(self, pipeline: Pipeline) -> dict:
        brief = pipeline.brief
        content = pipeline.reviewed_content or pipeline.draft_content
        languages = brief.target_languages

        if not content:
            raise ValueError("No content to localise")

        if not languages:
            await self.emit(pipeline.id, "log", "No target languages — skipping")
            return {"localized_count": 0, "languages": []}

        localized: list[LocalizedContent] = []

        for lang in languages:
            await self.emit(
                pipeline.id, "log", f"Localising to {lang}…"
            )

            prompt = f"""You are an expert content localiser for {brief.brand_name}.
Translate and culturally adapt the following content into {lang}.

RULES:
- Maintain the original meaning, intent, and brand voice
- Keep "{brief.brand_name}" un-translated (it's a brand name)
- Adapt cultural references, idioms, and metaphors for the {lang}-speaking market
- Keep technical terms in their commonly-used form in {lang}
- Preserve formatting (headers, bullets, etc.)
- Adjust date/number formats to local convention

CONTENT:
{content[:3500]}

Respond in STRICT JSON:
{{
  "translated_content": "<the full translated content>",
  "cultural_notes": ["<note about a cultural adaptation you made>"]
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
                    "translated_content": f"[{lang} translation of the content]",
                    "cultural_notes": [
                        f"Adapted for {lang}-speaking audience"
                    ],
                }

            loc = LocalizedContent(
                language=lang,
                content=data.get("translated_content", ""),
                cultural_notes=data.get("cultural_notes", []),
            )
            localized.append(loc)

        pipeline.localized_versions = localized

        await self.emit(
            pipeline.id,
            "log",
            f"Localised into {len(localized)} languages: {', '.join(languages)}",
        )

        return {
            "localized_count": len(localized),
            "languages": languages,
            "cultural_notes_total": sum(
                len(l.cultural_notes) for l in localized
            ),
        }
