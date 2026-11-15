#!/usr/bin/env python3
"""Turn plain narration text into a scene-based JSON storyboard.

This lightweight adapter uses deterministic heuristics; it needs no LLM API key.
The existing engine remains responsible for creating visuals, voiceover, captions,
and the final MP4.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

VISUAL_KEYWORDS = {
    "compare": ("compare", "compared", "versus", " vs ", "before", "after", "difference"),
    "cycle": ("cycle", "loop", "repeat", "repeats", "feedback loop"),
    "timeline": ("timeline", "years", "century", "historically", "eventually", "over time"),
    "stat": ("percent", "%", "statistics", "data", "rate", "increased", "decreased", "growth"),
    "network": ("network", "connected", "signal", "router", "server", "internet"),
    "flow": ("first", "next", "then", "finally", "step", "process", "begins", "leads to"),
}


def split_into_scenes(script: str, max_sentences: int = 3) -> list[str]:
    """Split script paragraphs into readable, narration-sized scenes.

    Blank lines are treated as deliberate scene breaks. Within a paragraph,
    sentences are grouped in threes to avoid one-frame-per-sentence storyboards.
    """
    if not isinstance(script, str) or not script.strip():
        raise ValueError("The script is empty. Add narration text and try again.")
    if max_sentences < 1:
        raise ValueError("max_sentences must be at least 1")

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", script.strip()) if part.strip()]
    scenes: list[str] = []
    for paragraph in paragraphs:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()]
        if not sentences:
            continue
        for start in range(0, len(sentences), max_sentences):
            scenes.append(" ".join(sentences[start:start + max_sentences]))
    return scenes


def _visual_for(text: str) -> str:
    lower = f" {text.lower()} "
    for visual, keywords in VISUAL_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return visual
    return "concept"


def _items_for(text: str, visual: str) -> list[str]:
    """Return short labels appropriate for the renderer's infographic cards."""
    if visual == "compare":
        return ["Before", "After"]
    # Use comma/semicolon-separated phrases where available; otherwise make
    # compact labels from the sentence's meaningful words.
    phrases = [part.strip(" .!?;:") for part in re.split(r"[,;:]", text) if part.strip(" .!?;:")]
    if len(phrases) >= 2:
        labels = phrases[:5]
    else:
        words = re.findall(r"[\w'-]+", text)
        stop = {"the", "and", "for", "with", "that", "this", "from", "into", "when", "what", "how", "are", "was", "were", "their", "they", "you", "your", "then", "than"}
        keywords = [word for word in words if word.lower() not in stop]
        labels = [" ".join(keywords[i:i + 2]) for i in range(0, min(len(keywords), 8), 2)]
    labels = [label[:36] for label in labels if label]
    return labels[:5] or ["Key idea", "Why it matters"]


def _heading(text: str, limit: int = 64) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[:limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def script_to_story(script: str, *, title: str = "A Story, Illustrated", voice: str = "en-US-GuyNeural", max_sentences: int = 3) -> dict[str, Any]:
    """Build a story object accepted by ``engine.run`` from plain text."""
    chunks = split_into_scenes(script, max_sentences=max_sentences)
    scenes = []
    for chunk in chunks:
        visual = _visual_for(chunk)
        heading = _heading(chunk)
        scene = {
            "heading": heading,
            "caption": heading,
            "narration": chunk,
            "visual": visual,
            "items": _items_for(chunk, visual),
            "action": "point" if visual in {"flow", "network", "stat"} else "explain",
            "accent": "#2AA391",
        }
        if visual == "stat":
            scene["values"] = [30, 55, 75, 90][:len(scene["items"])]
        scenes.append(scene)
    return {
        "title": title,
        "voice": voice,
        "fps": 24,
        "width": 1280,
        "height": 720,
        "reading_beat": 0.35,
        "scenes": scenes,
    }


def script_file_to_story(path: str | Path, **options: Any) -> dict[str, Any]:
    source = Path(path)
    return script_to_story(source.read_text(encoding="utf-8"), title=options.pop("title", source.stem.replace("_", " ").title()), **options)
