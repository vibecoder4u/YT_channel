#!/usr/bin/env python3
"""Plain script and topic to cinematic explainer storyboard."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

VISUAL_KEYWORDS = {
    "compare": ("compare", "compared", "versus", " vs ", "before", "after", "difference", "instead"),
    "cycle": ("cycle", "loop", "repeat", "feedback loop"),
    "timeline": ("timeline", "years", "century", "historically", "eventually", "over time"),
    "stat": ("percent", "%", "statistics", "data", "rate", "increased", "decreased", "growth", "trend"),
    "network": ("network", "connected", "signal", "router", "server", "internet", "system"),
    "flow": ("first", "next", "then", "finally", "step", "process", "begins", "leads to"),
}
ACCENTS = ["#2AA391", "#3D7AF5", "#F4B942", "#E16F5A", "#7C6BFF", "#49B56B"]


def split_into_scenes(script: str, max_sentences: int = 3) -> list[str]:
    if not isinstance(script, str) or not script.strip():
        raise ValueError("The script is empty. Add narration text and try again.")
    if max_sentences < 1:
        raise ValueError("max_sentences must be at least 1")
    scenes = []
    for paragraph in (p.strip() for p in re.split(r"\n\s*\n", script.strip()) if p.strip()):
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()]
        for start in range(0, len(sentences), max_sentences):
            scenes.append(" ".join(sentences[start:start+max_sentences]))
    return scenes


def _visual_for(text: str) -> str:
    lower = f" {text.lower()} "
    return next((visual for visual, words in VISUAL_KEYWORDS.items() if any(word in lower for word in words)), "concept")


def _items_for(text: str, visual: str) -> list[str]:
    if visual == "compare":
        return ["Before", "After"]
    phrases = [part.strip(" .!?;:") for part in re.split(r"[,;:]", text) if part.strip(" .!?;:")]
    if len(phrases) >= 2:
        labels = phrases[:5]
    else:
        words = re.findall(r"[\w'-]+", text)
        stop = {"the", "and", "for", "with", "that", "this", "from", "into", "when", "what", "how", "are", "was", "were", "their", "they", "you", "your", "then", "than"}
        keywords = [word for word in words if word.lower() not in stop]
        labels = [" ".join(keywords[i:i+2]) for i in range(0, min(len(keywords), 8), 2)]
    return [label[:36] for label in labels if label][:5] or ["Key idea", "Why it matters"]


def _heading(text: str, limit: int = 64) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[:limit-1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def script_to_story(script: str, *, title: str = "A Story, Illustrated", voice: str = "en-US-GuyNeural", max_sentences: int = 3) -> dict[str, Any]:
    chunks = split_into_scenes(script, max_sentences)
    scenes = []
    for index, chunk in enumerate(chunks):
        visual = _visual_for(chunk)
        heading = _heading(chunk)
        scene = {
            "heading": heading,
            "caption": heading,
            "takeaway": chunk if len(chunk) < 120 else chunk[:117].rstrip() + "…",
            "narration": chunk,
            "visual": visual,
            "items": _items_for(chunk, visual),
            "action": "point" if visual in {"flow", "network", "stat"} else "explain",
            "accent": ACCENTS[index % len(ACCENTS)],
            "chapter": f"Chapter {index // 2 + 1}",
        }
        if visual == "stat":
            scene["values"] = [35, 52, 68, 81][:len(scene["items"])]
        scenes.append(scene)
    return {"title": title, "voice": voice, "fps": 24, "width": 1280, "height": 720, "reading_beat": .35, "scenes": scenes}


def generate_explainer_story(topic: str, *, title: str | None = None, voice: str = "en-US-GuyNeural") -> dict[str, Any]:
    """Create a non-researched explainer outline; verify factual claims before publishing."""
    topic = re.sub(r"\s+", " ", topic).strip()
    if not topic:
        raise ValueError("A topic is required")
    prompts = [
        ("The question", f"What makes {topic} worth understanding? Start with the problem or surprising question that makes people curious. Replace this placeholder with a verified hook before publishing."),
        ("The basic idea", f"In plain language, explain what {topic} means. Define the central idea without jargon, and use one accurate example from your research."),
        ("How it works", f"Walk through the real steps behind {topic}. Explain what happens first, what changes next, and what produces the final result."),
        ("A useful comparison", f"Compare {topic} with a familiar alternative. Explain what is genuinely different, and avoid overstating the advantages."),
        ("Why it matters", f"Show a concrete, sourced consequence of {topic}. Add a trustworthy statistic or example only after checking its source."),
        ("The takeaway", f"Summarize the most important thing to remember about {topic}, including one limitation or open question."),
    ]
    scenes = []
    for index, (chapter, narration) in enumerate(prompts):
        visual = ["concept", "concept", "flow", "compare", "stat", "cycle"][index]
        scenes.append({
            "heading": chapter,
            "caption": chapter,
            "takeaway": "Research and verify this scene before publishing.",
            "narration": narration,
            "visual": visual,
            "items": [["Question", "Why now", "Stakes"], ["Meaning", "Example"], ["Step one", "Step two", "Result"], ["Alternative", "This topic"], ["Evidence", "Impact"], ["Remember", "Limit", "Next step"]][index],
            "values": [35, 60, 82] if visual == "stat" else [],
            "action": ["think", "explain", "point", "demonstrate", "celebrate", "point"][index],
            "accent": ACCENTS[index],
            "chapter": chapter,
        })
    return {"title": title or topic.title(), "voice": voice, "fps": 24, "width": 1280, "height": 720, "reading_beat": .35, "scenes": scenes}


def script_file_to_story(path: str | Path, **options: Any) -> dict[str, Any]:
    source = Path(path)
    raw = source.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and isinstance(parsed.get("scenes"), list):
            return parsed
    except json.JSONDecodeError:
        pass
    title = options.pop("title", source.stem.replace("_", " ").title())
    return script_to_story(raw, title=title, **options)
