from pathlib import Path

from app.kb import KnowledgeBase


def test_kb_search(tmp_path: Path) -> None:
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "faq.md").write_text("Цена формируется после брифа.\n\nСрок запуска 2 недели.", encoding="utf-8")

    kb = KnowledgeBase(kb_dir)
    result = kb.search("Какие сроки запуска?", top_k=2)
    assert result
    assert any("Срок запуска" in chunk.text for chunk in result)
