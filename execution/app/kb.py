from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]{2,}")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str


class KnowledgeBase:
    def __init__(self, kb_dir: Path) -> None:
        self.kb_dir = kb_dir
        self.chunks: list[Chunk] = []
        self._load()

    def _load(self) -> None:
        if not self.kb_dir.exists():
            return
        for path in self.kb_dir.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            parts = [p.strip() for p in text.split("\n\n") if p.strip()]
            for idx, part in enumerate(parts):
                self.chunks.append(Chunk(chunk_id=f"{path.stem}:{idx}", text=part, source=str(path)))

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t.lower() for t in TOKEN_RE.findall(text)}

    def search(self, query: str, top_k: int = 4) -> list[Chunk]:
        q = self._tokens(query)
        if not q:
            return []
        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            c = self._tokens(chunk.text)
            inter = len(q & c)
            if inter == 0:
                continue
            score = inter / math.sqrt(max(1, len(q)) * max(1, len(c)))
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
