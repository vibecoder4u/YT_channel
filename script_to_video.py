#!/usr/bin/env python3
"""Story builder for polished short-form explainer videos.

This module converts either:
- plain scripts (natural-language narration), or
- a short topic prompt (`generate_explainer_story`)

into a storyboard suitable for the renderer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

VISUAL_KEYWORDS = {
    "compare": ("compare", "compared", "versus", " vs ", "before", "after", "difference", "instead"),
    "cycle": ("cycle", "loop", "repeat", "repeats", "feedback loop", "looping"),
    "timeline": ("timeline", "years", "century", "historically", "eventually", "over time", "story"),
    "stat": ("percent", "%", "statistics", "data", "rate", "increased", "decreased", "growth", "trend"),
    "network": ("network", "connected", "signal", "router", "server", "internet", "system"),
    "flow": ("first", "next", "then", "finally", "step", "process", "begins", "leads to", "how it works"),
}

ACCENTS = ["#2AA391", "#3D7AF5", "#F4B942", "#E16F5A", "#7C6BFF", "#49B56B"]


def split_into_scenes(script: str, max_sentences: int = 3) -> list[str]:
    """Split script paragraphs into short, narration-friendly scenes."""
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
            chunk = " ".join(sentences[start:start + max_sentences])
            if chunk:
                scenes.append(chunk)
    return scenes


def _visual_for(text: str) -> str:
    lower = f" {text.lower()} "
    for visual, keywords in VISUAL_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return visual
    return "concept"


def _items_for(text: str, visual: str) -> list[str]:
    if visual == "compare":
        return ["Before", "After"]
    phrases = [part.strip(" .!?;:") for part in re.split(r"[,;:]", text) if part.strip(" .!?;:")]
    if len(phrases) >= 2:
        labels = phrases[:5]
    else:
        words = re.findall(r"[\w'-]+", text)
        stop = {"the", "and", "for", "with", "that", "this", "from", "into", "when", "what", "how", "are", "was", "were", "their", "they", "you", "your", "then", "than", "about"}
        keywords = [word for word in words if word.lower() not in stop]
        labels = [" ".join(keywords[i:i + 2]) for i in range(0, min(len(keywords), 8), 2)]
    labels = [label[:36] for label in labels if label][:5]
    return labels or ["Key idea", "Why it matters"]


def _heading(text: str, limit: int = 64) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    trimmed = clean[:limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return trimmed + "…" if trimmed else clean[:limit - 1]


def _takeaway(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ["because", "so", "this means", "important", "key"]):
        return text.strip()
    if len(text) > 120:
        return text[:117].rstrip() + "…"
    return "The main idea is simple: understand the structure, then the payoff follows."


def _caption(text: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= 84:
        return clean
    return clean[:81].rstrip() + "…"


def script_to_story(script: str, *, title: str = "A Story, Illustrated", voice: str = "en-US-GuyNeural", max_sentences: int = 3) -> dict[str, Any]:
    """Generate a story object from plain-language narration."""
    chunks = split_into_scenes(script, max_sentences=max_sentences)
    scenes = []
    for idx, chunk in enumerate(chunks):
        visual = _visual_for(chunk)
        heading = _heading(chunk)
        scene = {
            "heading": heading,
            "caption": _caption(chunk),
            "takeaway": _takeaway(chunk),
            "narration": chunk,
            "visual": visual,
            "items": _items_for(chunk, visual),
            "action": "point" if visual in {"flow", "network", "stat"} else "explain",
            "accent": ACCENTS[idx % len(ACCENTS)],
        }
        if visual == "stat":
            scene["values"] = [35, 52, 68, 81][:len(scene["items"])]
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


def _clean_topic(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def generate_explainer_story(topic: str, *, title: str | None = None, voice: str = "en-US-GuyNeural") -> dict[str, Any]:
    """Generate a polished short-form explainer from a single topic prompt.

    Example topic: 'why apps feel instant' or 'how AI image tools work'
    """
    topic_text = _clean_topic(topic)
    if not topic_text:
        raise ValueError("A topic is required to generate a polished explainer story.")

    title_text = title or topic_text.title()
    base = topic_text.lower()

    # Build a strong short-form narrative arc: hook, mechanism, contrast, payoff.
    scenes = [
        {
            "heading": f"Why {topic_text} matters right now",
            "caption": f"The hidden reason {topic_text.lower()} feels so important",
            "narration": f"Here is the big idea: {topic_text}. It is shaping the way people work, learn, and decide. The result is that this topic is now showing up everywhere, from apps and content to daily decisions.",
            "visual": "concept",
            "items": ["The problem", "The pattern", "The impact"],
            "action": "point",
            "accent": ACCENTS[0],
            "takeaway": f"People notice {topic_text} because it changes the experience in a way that feels immediate and useful.",
        },
        {
            "heading": "The system behind it",
            "caption": "A simple explanation of the moving parts",
            "narration": f"To understand {topic_text}, start with the basic mechanism. A small input triggers a process, which then turns information into a result. That sequence is the reason the experience seems smooth, fast, and convincing.",
            "visual": "flow",
            "items": ["Input", "Process", "Result"],
            "action": "walk",
            "accent": ACCENTS[1],
            "takeaway": "The real magic is usually not one big leap; it is a clear sequence of steps working together.",
        },
        {
            "heading": "What makes it feel different",
            "caption": "Contrast is the key to clarity",
            "narration": f"Without {topic_text}, the process looks confusing or slow. With it, the same information becomes easier to compare, easier to act on, and easier to understand. That contrast is what makes the idea feel valuable instead of abstract.",
            "visual": "compare",
            "items": ["Before", "After"],
            "action": "demonstrate",
            "accent": ACCENTS[2],
            "takeaway": "The value is not just in the output; it is in how much clearer the whole experience becomes.",
        },
        {
            "heading": "The signal in plain language",
            "caption": "A clean summary of the hidden logic",
            "narration": f"So the short version is this: {topic_text} works because a clear signal is turned into a useful output, and that output is then shaped to match real human needs. In other words, a good system reduces friction while preserving clarity.",
            "visual": "network",
            "items": ["Signal", "Context", "Decision"],
            "action": "explain",
            "accent": ACCENTS[3],
            "takeaway": "The best explanations feel simple because the underlying system is simple once you strip away the noise.",
        },
        {
            "heading": "Why it matters to your audience",
            "caption": "The payoff is practical, not theoretical",
            "narration": f"This matters because {topic_text} changes how people learn, create, and make faster decisions. The result is more momentum, more confidence, and a cleaner path from curiosity to action. That is why it keeps attracting attention.",
            "visual": "stat",
            "items": ["Faster", "Clearer", "More useful"],
            "values": [42, 68, 88],
            "action": "celebrate",
            "accent": ACCENTS[4],
            "takeaway": "When people understand the payoff, they stop seeing the topic as jargon and start recognizing a useful pattern.",
        },
        {
            "heading": "The takeaway",
            "caption": "A final punchline for the episode",
            "narration": f"The real lesson behind {topic_text} is simple: when you remove friction and clarify the pattern, the result feels more natural and more powerful. That is why the idea sticks, and why it keeps mattering in modern tools and modern storytelling.",
            "visual": "cycle",
            "items": ["Notice", "Understand", "Apply", "Share"],
            "action": "point",
            "accent": ACCENTS[5],
            "takeaway": "The best explainers turn complexity into a sequence people can feel and remember.",
        },
    ]

    return {
        "title": title_text,
        "voice": voice,
        "fps": 24,
        "width": 1280,
        "height": 720,
        "reading_beat": 0.35,
        "scenes": scenes,
    }


def script_file_to_story(path: str | Path, **options: Any) -> dict[str, Any]:
    source = Path(path)
    raw = source.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and isinstance(parsed.get("scenes"), list):
            return parsed
    except json.JSONDecodeError:
        pass
    return script_to_story(raw, title=options.pop("title", source.stem.replace("_", " ").title()), **options)


if __name__ == "__main__":
    sample = "Why small tools feel better when they are clear. They reduce friction and friction is what makes work feel slow. Then the payoff is easier decisions and faster learning."
    print(json.dumps(script_to_story(sample, title="Demo Story"), indent=2))
