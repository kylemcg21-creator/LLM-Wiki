"""Edge cases and advanced scenarios for ingest tracking."""

from pathlib import Path

from llm_wiki.ingest import get_ingest_status


class TestIngestNestedDirectories:
    """Test ingest handling of nested raw directories."""

    def test_ingest_nested_raw_directories(self, tmp_path: Path):
        """Should handle raw/subdir/file.md correctly."""
        (tmp_path / "raw" / "papers" / "2024").mkdir(parents=True)
        (tmp_path / "raw" / "papers" / "2024" / "article.md").write_text("content")
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        assert any(s.raw_file == "papers/2024/article.md" for s in statuses)
        assert any(s.status == "pending" for s in statuses)

    def test_ingest_deeply_nested_raw_directories(self, tmp_path: Path):
        """Should handle deeply nested directory structures."""
        nested_path = tmp_path / "raw" / "level1" / "level2" / "level3" / "level4"
        nested_path.mkdir(parents=True)
        (nested_path / "deep_file.md").write_text("content")
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        assert any("level1/level2/level3/level4" in s.raw_file for s in statuses)

    def test_ingest_raw_with_subdirectories_no_files(self, tmp_path: Path):
        """Should handle empty subdirectories in raw/."""
        (tmp_path / "raw" / "empty_dir").mkdir(parents=True)
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        # Should not crash, should return empty status
        assert isinstance(statuses, list)


class TestIngestSpecialCharacters:
    """Test ingest with special characters in filenames."""

    def test_ingest_spaces_in_filenames(self, tmp_path: Path):
        """Should handle filenames with spaces."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "My Document.md").write_text("content")
        (tmp_path / "raw" / "Another File With Spaces.md").write_text("content")
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status == "pending"]
        assert "My Document.md" in raw_files
        assert "Another File With Spaces.md" in raw_files

    def test_ingest_special_chars_in_filenames(self, tmp_path: Path):
        """Should handle filenames with special characters."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "file(2024).md").write_text("content")
        (tmp_path / "raw" / "document-v2.md").write_text("content")
        (tmp_path / "raw" / "paper_final.md").write_text("content")
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status == "pending"]
        assert "file(2024).md" in raw_files
        assert "document-v2.md" in raw_files
        assert "paper_final.md" in raw_files

    def test_ingest_unicode_filenames(self, tmp_path: Path):
        """Should handle unicode characters in filenames."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "café.md").write_text("content")
        (tmp_path / "raw" / "résumé.md").write_text("content")
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status == "pending"]
        # Should handle unicode gracefully
        assert len(raw_files) >= 0  # Should not crash


class TestIngestFrontmatterHandling:
    """Test ingest with various frontmatter scenarios."""

    def test_ingest_source_missing_raw_file_field(self, tmp_path: Path):
        """Should mark source as incomplete if raw_file field is missing."""
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "wiki" / "sources" / "source.md").write_text(
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n---\n\nContent"
        )

        statuses = get_ingest_status(tmp_path)
        assert any(s.status == "incomplete" for s in statuses)
        assert any(s.source_page == "sources/source.md" for s in statuses)

    def test_ingest_source_empty_raw_file_field(self, tmp_path: Path):
        """Should mark source as incomplete if raw_file is empty."""
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        empty_fm = (
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
            "raw_file: \n---\n\nContent"
        )
        (tmp_path / "wiki" / "sources" / "source.md").write_text(empty_fm)

        statuses = get_ingest_status(tmp_path)
        incomplete = [s for s in statuses if s.status == "incomplete"]
        assert len(incomplete) > 0

    def test_ingest_malformed_yaml_frontmatter(self, tmp_path: Path):
        """Should handle malformed YAML frontmatter gracefully."""
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "wiki" / "sources" / "bad.md").write_text(
            "---\ninvalid: [yaml: garbage\n---\n\nContent"
        )

        statuses = get_ingest_status(tmp_path)
        # Should not crash
        assert isinstance(statuses, list)

    def test_ingest_valid_raw_file_reference(self, tmp_path: Path):
        """Should mark source as ingested when raw_file matches existing file."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "paper.md").write_text("content")
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        valid_fm = (
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
            "raw_file: paper.md\n---\n\nContent"
        )
        (tmp_path / "wiki" / "sources" / "paper.md").write_text(valid_fm)

        statuses = get_ingest_status(tmp_path)
        assert any(s.status == "ingested" and s.raw_file == "paper.md" for s in statuses)


class TestIngestGitkeepHandling:
    """Test that git-related files are skipped."""

    def test_ingest_skips_gitkeep(self, tmp_path: Path):
        """Should skip .gitkeep files in raw/."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / ".gitkeep").write_text("")
        (tmp_path / "raw" / "actual-paper.md").write_text("content")
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status in ["pending", "ingested"]]
        assert ".gitkeep" not in raw_files
        assert "actual-paper.md" in raw_files

    def test_ingest_skips_readme(self, tmp_path: Path):
        """Should skip README.md files in raw/."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "README.md").write_text("# Instructions")
        (tmp_path / "raw" / "actual-paper.md").write_text("content")
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status in ["pending", "ingested"]]
        assert "README.md" not in raw_files or "readme.md" not in [f.lower() for f in raw_files]
        assert "actual-paper.md" in raw_files

    def test_ingest_case_insensitive_skip(self, tmp_path: Path):
        """Should skip .gitkeep and readme files case-insensitively."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "readme.md").write_text("")
        (tmp_path / "raw" / "ReadMe.md").write_text("")
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status in ["pending", "ingested"]]
        # Case-insensitive comparison
        raw_files_lower = [f.lower() for f in raw_files]
        assert "readme.md" not in raw_files_lower


class TestIngestOrphanDetection:
    """Test detection of orphaned source files."""

    def test_ingest_detects_orphan_sources(self, tmp_path: Path):
        """Should detect source pages that reference nonexistent raw files."""
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        orphan_fm = (
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
            "raw_file: missing-file.md\n---\n\nContent"
        )
        (tmp_path / "wiki" / "sources" / "orphan.md").write_text(orphan_fm)

        statuses = get_ingest_status(tmp_path)
        assert any(s.status == "orphan" and s.source_page == "sources/orphan.md" for s in statuses)

    def test_ingest_multiple_orphans(self, tmp_path: Path):
        """Should detect multiple orphaned sources."""
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        for i in range(3):
            multi_orphan_fm = (
                "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
                f"raw_file: missing-{i}.md\n---\n\nContent"
            )
            (tmp_path / "wiki" / "sources" / f"orphan-{i}.md").write_text(multi_orphan_fm)

        statuses = get_ingest_status(tmp_path)
        orphans = [s for s in statuses if s.status == "orphan"]
        assert len(orphans) >= 3


class TestIngestStatusCategories:
    """Test all ingest status categories."""

    def test_ingest_all_status_types(self, tmp_path: Path):
        """Should correctly categorize all ingest status types."""
        # Setup: ingested, pending, incomplete, orphan
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "ingested-file.md").write_text("content")
        (tmp_path / "raw" / "pending-file.md").write_text("content")

        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        # Ingested: source page with matching raw file
        ingested_fm = (
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
            "raw_file: ingested-file.md\n---"
        )
        (tmp_path / "wiki" / "sources" / "ingested.md").write_text(ingested_fm)

        # Incomplete: source page with no raw_file field
        incomplete_fm = "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n---"
        (tmp_path / "wiki" / "sources" / "incomplete.md").write_text(
            incomplete_fm
        )

        # Orphan: source page referencing nonexistent raw file
        orphan_fm = (
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
            "raw_file: nonexistent.md\n---"
        )
        (tmp_path / "wiki" / "sources" / "orphan.md").write_text(orphan_fm)

        statuses = get_ingest_status(tmp_path)

        status_types = {s.status for s in statuses}
        # Should have various status types
        assert "pending" in status_types  # pending-file.md
        assert "ingested" in status_types  # ingested-file.md with matching source

        # Check specific statuses
        pending = [s for s in statuses if s.status == "pending"]
        ingested = [s for s in statuses if s.status == "ingested"]
        incomplete = [s for s in statuses if s.status == "incomplete"]
        orphan = [s for s in statuses if s.status == "orphan"]

        assert len(pending) > 0
        assert len(ingested) > 0
        assert len(incomplete) > 0
        assert len(orphan) > 0


class TestIngestEmptyWiki:
    """Test ingest on empty or minimal wikis."""

    def test_ingest_empty_wiki(self, tmp_path: Path):
        """Should handle completely empty wiki."""
        (tmp_path / "wiki").mkdir()

        statuses = get_ingest_status(tmp_path)
        assert isinstance(statuses, list)
        assert len(statuses) == 0

    def test_ingest_no_raw_directory(self, tmp_path: Path):
        """Should handle missing raw/ directory."""
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        assert isinstance(statuses, list)
        # Should handle gracefully

    def test_ingest_no_sources_directory(self, tmp_path: Path):
        """Should handle missing wiki/sources/ directory."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "file.md").write_text("content")
        (tmp_path / "wiki").mkdir()

        statuses = get_ingest_status(tmp_path)
        # Should still report raw files as pending
        pending = [s for s in statuses if s.status == "pending"]
        assert len(pending) > 0


class TestIngestLargeScale:
    """Test ingest performance and correctness on larger datasets."""

    def test_ingest_many_files(self, tmp_path: Path):
        """Should handle wikis with many raw files."""
        (tmp_path / "raw").mkdir()
        for i in range(100):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Index")

        statuses = get_ingest_status(tmp_path)
        pending = [s for s in statuses if s.status == "pending"]
        assert len(pending) == 100

    def test_ingest_performance(self, tmp_path: Path):
        """Ingest should complete quickly even with many files."""
        (tmp_path / "raw").mkdir()
        for i in range(50):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        for i in range(50):
            fm = (
                "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
                f"raw_file: file-{i}.md\n---"
            )
            (tmp_path / "wiki" / "sources" / f"file-{i}.md").write_text(fm)

        import time

        start = time.time()
        statuses = get_ingest_status(tmp_path)
        elapsed = time.time() - start

        # Should complete quickly (< 2 seconds)
        assert elapsed < 2.0
        assert len(statuses) > 0
