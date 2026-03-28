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

            prompt = f"""You are an elite multilingual content localizer for {brief.brand_name}.
Your task is to translate and culturally adapt the provided content into {lang}.

STRICT REQUIREMENTS:
1. LANGUAGE: The output MUST be in {lang}. This is an absolute requirement.
2. VOICE: Maintain the "{brief.tone}" brand voice in the target language.
3. BRAND: Keep the brand name "{brief.brand_name}" in its original English form.
4. FORMAT: Preserve all markdown formatting (headers, bullets, bolding) exactly as in the source.
5. ADAPTATION: Do not just translate words; adapt idioms, date formats, and cultural nuances for the {lang} market.

CONTENT TO TRANSLATE (in English):
{content[:3500]}

Respond ONLY in this STRICT JSON format:
{{
  "translated_content": "<the full {lang} translation>",
  "cultural_notes": ["<specific note about an adaptation made for {lang}>"]
}}

Note: If the language is Hindi, use Devanagari script.
Output ONLY the JSON object. No markdown code blocks."""

            raw = await generate(prompt)
            data = self._parse_json(raw)

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
