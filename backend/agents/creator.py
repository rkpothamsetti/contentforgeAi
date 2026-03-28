"""Content Creator Agent — generates content from briefs using Gemini."""

from __future__ import annotations
from agents.base import BaseAgent
from models import Pipeline, ContentFormat
from ai_client import generate


FORMAT_PROMPTS = {
    ContentFormat.BLOG_POST: "a comprehensive, SEO-optimised blog post (800-1200 words) with headings, subheadings, and a call-to-action",
    ContentFormat.SOCIAL_MEDIA: "a set of 3 social media posts: one for LinkedIn (professional, 150 words), one for Twitter/X (280 chars max), and one for Instagram (engaging caption with hashtags)",
    ContentFormat.EMAIL_NEWSLETTER: "a professional email newsletter with subject line, preview text, greeting, 3-4 content sections, and a clear CTA",
    ContentFormat.PRESS_RELEASE: "a professional press release following AP style with headline, dateline, lead paragraph, body, boilerplate, and contact info",
    ContentFormat.SALES_COLLATERAL: "persuasive sales collateral with value propositions, customer pain points, solution overview, key benefits, and a closing CTA",
}


class CreatorAgent(BaseAgent):
    name = "creator"
    display_name = "Content Creator"

    async def execute(self, pipeline: Pipeline) -> dict:
        brief = pipeline.brief
        format_instruction = FORMAT_PROMPTS.get(
            brief.format, "a professional piece of content"
        )

        knowledge_section = ""
        if brief.knowledge_context:
            knowledge_section = f"""
Use the following internal knowledge/context to inform the content.
Incorporate relevant data, statistics, and insights from it:

--- INTERNAL KNOWLEDGE ---
{brief.knowledge_context[:3000]}
--- END KNOWLEDGE ---
"""

        key_points_text = ""
        if brief.key_points:
            key_points_text = "\nKey points to cover:\n" + "\n".join(
                f"- {p}" for p in brief.key_points
            )

        prompt = f"""You are an expert enterprise content creator for {brief.brand_name}.

Create {format_instruction}.

Topic: {brief.topic}
Target Audience: {brief.audience}
Desired Tone: {brief.tone}
{key_points_text}
{knowledge_section}

Requirements:
- Write in {brief.tone} tone throughout
- Include relevant industry data and insights
- Make it engaging and actionable for the target audience
- Use proper formatting (headers, bullet points where appropriate)
- Include a compelling headline/title
- Ensure the content reflects {brief.brand_name}'s expertise

Output ONLY the content, no meta-commentary."""

        await self.emit(
            pipeline.id,
            "log",
            f"Generating {brief.format.value} for audience: {brief.audience}",
        )

        content = await generate(prompt)
        pipeline.draft_content = content

        word_count = len(content.split())
        await self.emit(
            pipeline.id,
            "log",
            f"Generated {word_count} words of {brief.format.value} content",
        )

        return {
            "content": content,
            "word_count": word_count,
            "format": brief.format.value,
            "topic": brief.topic,
        }
