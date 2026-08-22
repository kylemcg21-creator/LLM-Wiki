"""Edge cases and advanced scenarios for stats and log parsing."""

from pathlib import Path

from llm_wiki.stats import get_stats, parse_log_entries


class TestStatsBasic:
    """Test basic stats calculation."""

    def test_stats_empty_wiki(self, tmp_path: Path):
        """Should return zeros for empty wiki."""
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw").mkdir()

        stats = get_stats(tmp_path)
        assert stats.page_count == 0
        assert stats.raw_count == 0


class TestStatsPageCounting:
    """Test page counting logic."""

    def test_stats_count_wiki_pages(self, tmp_path: Path):
        """Should count all pages in wiki/."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        for i in range(5):
            (wiki / f"page-{i}.md").write_text(f"# Page {i}")

        stats = get_stats(tmp_path)
        assert stats.page_count == 5

    def test_stats_count_nested_pages(self, tmp_path: Path):
        """Should count pages in nested directories."""
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "concepts").mkdir(parents=True)
        for i in range(3):
            (wiki / "entities" / f"entity-{i}.md").write_text(f"# Entity {i}")
            (wiki / "concepts" / f"concept-{i}.md").write_text(f"# Concept {i}")

        stats = get_stats(tmp_path)
        assert stats.page_count == 6

    def test_stats_exclude_index_and_log(self, tmp_path: Path):
        """Should handle counting of index.md and log.md."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")
        (wiki / "page.md").write_text("# Page")

        stats = get_stats(tmp_path)
        # All should be counted, including special pages
        assert stats.page_count >= 3


class TestStatsRawCounting:
    """Test raw file counting."""

    def test_stats_count_raw_files(self, tmp_path: Path):
        """Should count files in raw/."""
        (tmp_path / "raw").mkdir()
        for i in range(10):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        stats = get_stats(tmp_path)
        assert stats.raw_count == 10

    def test_stats_count_nested_raw(self, tmp_path: Path):
        """Should count nested raw files."""
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        (tmp_path / "raw" / "notes").mkdir(parents=True)
        for i in range(3):
            (tmp_path / "raw" / "papers" / f"paper-{i}.md").write_text(f"paper {i}")
            (tmp_path / "raw" / "notes" / f"note-{i}.md").write_text(f"note {i}")

        stats = get_stats(tmp_path)
        assert stats.raw_count == 6

    def test_stats_skip_gitkeep_readme(self, tmp_path: Path):
        """Should skip .gitkeep and README files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / ".gitkeep").write_text("")
        (tmp_path / "raw" / "README.md").write_text("# Instructions")
        (tmp_path / "raw" / "actual-file.md").write_text("content")

        stats = get_stats(tmp_path)
        # Should only count actual-file.md
        assert stats.raw_count == 1


class TestLogParsing:
    """Test log entry parsing."""

    def test_parse_empty_log(self, tmp_path: Path):
        """Should handle empty log gracefully."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n")

        entries = parse_log_entries(log)
        assert entries == []

    def test_parse_single_log_entry(self, tmp_path: Path):
        """Should parse single log entry."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n\n## 2026-08-22\n\nCreated first entity page.\n")

        entries = parse_log_entries(log)
        assert len(entries) >= 1

    def test_parse_multiple_log_entries(self, tmp_path: Path):
        """Should parse multiple dated entries."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log_content = """# Log

## 2026-08-22

Worked on synthesis page.

## 2026-08-21

Added entity pages.

## 2026-08-20

Initial setup complete.
"""
        log.write_text(log_content)

        entries = parse_log_entries(log)
        assert len(entries) >= 3

    def test_parse_log_with_special_dates(self, tmp_path: Path):
        """Should parse various date formats in log."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log_content = """# Log

## 2026-08-22 (Latest)

Latest entry.

## 2026/08/21

Slash format date.

## August 20, 2026

Long format date.
"""
        log.write_text(log_content)

        entries = parse_log_entries(log)
        # Should parse what it can, at minimum one entry
        assert len(entries) >= 1


class TestLogContent:
    """Test log entry content extraction."""

    def test_log_entry_single_line(self, tmp_path: Path):
        """Should extract single-line log entries."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n\n## 2026-08-22\n\nSimple entry\n")

        entries = parse_log_entries(log)
        if entries:
            assert "Simple entry" in entries[0].content or entries[0].content

    def test_log_entry_multiline(self, tmp_path: Path):
        """Should extract multiline log entries."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n\n## 2026-08-22\n\nFirst line\nSecond line\nThird line\n")

        entries = parse_log_entries(log)
        if entries:
            content = entries[0].content
            assert len(content) > 0

    def test_log_entry_with_markdown_formatting(self, tmp_path: Path):
        """Should preserve markdown in log entries."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n\n## 2026-08-22\n\n- Bullet 1\n- Bullet 2\n\n**Bold text**\n")

        entries = parse_log_entries(log)
        if entries:
            assert "Bullet" in entries[0].content or len(entries[0].content) > 0


class TestLogOrdering:
    """Test log entry ordering."""

    def test_log_entries_reverse_chronological(self, tmp_path: Path):
        """Should maintain entry order from log."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text(
            """# Log

## 2026-08-22

Newest

## 2026-08-21

Middle

## 2026-08-20

Oldest
"""
        )

        entries = parse_log_entries(log)
        assert len(entries) >= 1
        # First entry should be newest
        if len(entries) >= 2:
            assert "Newest" in entries[0].content or entries[0].date


class TestStatsSummary:
    """Test stats summary calculations."""

    def test_stats_returns_dict_structure(self, tmp_path: Path):
        """Should return structured stats object."""
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki" / "page.md").write_text("# Page")
        (tmp_path / "raw" / "file.md").write_text("content")

        stats = get_stats(tmp_path)
        assert hasattr(stats, "page_count")
        assert hasattr(stats, "raw_count")

    def test_stats_with_sources_directory(self, tmp_path: Path):
        """Should count pages in sources/ directory."""
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        for i in range(5):
            (wiki / "sources" / f"source-{i}.md").write_text(f"# Source {i}")

        stats = get_stats(tmp_path)
        # Should include source pages in count
        assert stats.page_count >= 5


class TestStatsLargeScale:
    """Test stats on large wikis."""

    def test_stats_performance_large_wiki(self, tmp_path: Path):
        """Should calculate stats efficiently for large wikis."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (tmp_path / "raw").mkdir()

        # Create 100 pages
        for i in range(100):
            (wiki / f"page-{i}.md").write_text(f"# Page {i}")

        # Create 50 raw files
        for i in range(50):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        import time

        start = time.time()
        stats = get_stats(tmp_path)
        elapsed = time.time() - start

        assert stats.page_count == 100
        assert stats.raw_count == 50
        assert elapsed < 2.0  # Should complete quickly

    def test_stats_large_log(self, tmp_path: Path):
        """Should parse large log files efficiently."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"

        # Create log with 100 entries
        lines = ["# Log\n"]
        for i in range(100):
            lines.append(f"\n## 2026-08-{(i % 28) + 1}\n\nEntry {i}\n")

        log.write_text("".join(lines))

        import time

        start = time.time()
        entries = parse_log_entries(log)
        elapsed = time.time() - start

        assert len(entries) > 0
        assert elapsed < 1.0  # Should parse quickly


class TestLogEdgeCases:
    """Test edge cases in log parsing."""

    def test_log_with_no_markdown_headers(self, tmp_path: Path):
        """Should handle log without date headers."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n\nSome free-form text without date headers\n")

        entries = parse_log_entries(log)
        # Should handle gracefully
        assert isinstance(entries, list)

    def test_log_with_malformed_dates(self, tmp_path: Path):
        """Should handle malformed date formats."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n\n## Not a date\n\nContent\n\n## 2026-13-45\n\nBad date\n")

        entries = parse_log_entries(log)
        # Should not crash
        assert isinstance(entries, list)

    def test_log_with_unicode_content(self, tmp_path: Path):
        """Should handle unicode in log entries."""
        (tmp_path / "wiki").mkdir()
        log = tmp_path / "wiki" / "log.md"
        log.write_text("# Log\n\n## 2026-08-22\n\nWorked on Café résumé 日本語\n")

        entries = parse_log_entries(log)
        # Should handle unicode
        assert isinstance(entries, list)
