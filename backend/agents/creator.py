"""Content Creator Agent — generates content from briefs using Gemini."""

from __future__ import annotations
from agents.base import BaseAgent
from models import Pipeline, ContentFormat
from ai_client import generate


FORMAT_PROMPTS = {
    ContentFormat.BLOG_POST: "a comprehensive, SEO-optimised blog post (800-1200 words). STRUCTURE: Catchy H1, Intro with hook, 3-4 H2 subheadings with detailed paragraphs, bulleted lists for data/features, and a compelling H2 Conclusion with CTA.",
    ContentFormat.SOCIAL_MEDIA: "a set of 3 distinct social media posts. 1. LinkedIn (Professional, thought-leadership style, 150-200 words). 2. Twitter/X (Punchy, thread-style or single tweet, max 280 chars). 3. Instagram (Visual-first caption, emojis, 10-15 relevant hashtags).",
    ContentFormat.EMAIL_NEWSLETTER: "a high-converting email newsletter. STRUCTURE: Subject line (under 50 chars), Preview text, Personalized greeting, 3 sections of value-driven content, and 1 very clear CTA button/link.",
    ContentFormat.PRESS_RELEASE: "a standard corporate press release. STRUCTURE: FOR IMMEDIATE RELEASE, Headline, Dateline (CITY, State), Strong Lead paragraph, Quote from executive, Body paragraphs, Boilerplate for TechCorp, and Media Contact info.",
    ContentFormat.SALES_COLLATERAL: "a persuasive sales deck script or one-pager. STRUCTURE: The Problem, The Cost of Inaction, Our Solution (value props), Case Study/Proof point, 3 Key Benefits, and Next Steps.",
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

        prompt = f"""You are the Lead Content Strategist for {brief.brand_name}. 
Your task is to generate high-quality, professional content that strictly adheres to the following brief.

MANDATORY CONSTRAINTS:
1. FORMAT: {format_instruction}
2. TONE: {brief.tone}
3. TOPIC: {brief.topic}
4. AUDIENCE: {brief.audience}
5. BRAND: All content must reflect {brief.brand_name}'s authority and expertise.

{knowledge_section}
{key_points_text}

ADDITIONAL RULES:
- If format is Social Media, provide each post clearly labeled.
- Use markdown formatting (headings, bolding, lists) to make the content scannable.
- Do NOT include any meta-talk like "Sure, here is your content".
- Output ONLY the final content.

Strictly follow these instructions. Failure to adhere to the format or tone is unacceptable."""

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
