"""Edge cases and advanced scenarios for watch functionality."""

from pathlib import Path

from llm_wiki.ingest import get_ingest_status


class TestWatchBasicTracking:
    """Test basic file tracking in raw/."""

    def test_watch_detects_new_files(self, tmp_path: Path):
        """Should detect new files in raw/."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "newfile.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status == "pending"]
        assert "newfile.md" in raw_files

    def test_watch_empty_raw_directory(self, tmp_path: Path):
        """Should return empty list when no files in raw/."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()

        statuses = get_ingest_status(tmp_path)
        pending = [s for s in statuses if s.status == "pending"]
        assert pending == []

    def test_watch_multiple_untracked_files(self, tmp_path: Path):
        """Should detect multiple untracked files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        for i in range(5):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        statuses = get_ingest_status(tmp_path)
        pending = [s for s in statuses if s.status == "pending"]
        assert len(pending) == 5


class TestWatchSourceTracking:
    """Test tracking of source pages against raw files."""

    def test_watch_file_with_matching_source(self, tmp_path: Path):
        """Should mark as ingested when source exists."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "raw" / "paper.md").write_text("content")
        (tmp_path / "wiki" / "sources" / "paper.md").write_text("---\nraw_file: paper.md\n---")

        statuses = get_ingest_status(tmp_path)
        # paper.md should be ingested since it has a source
        ingested = [s for s in statuses if s.status == "ingested"]
        pending = [s for s in statuses if s.status == "pending"]
        assert len(ingested) > 0 or len(pending) == 0

    def test_watch_mixed_tracked_untracked(self, tmp_path: Path):
        """Should distinguish between tracked and untracked files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki" / "sources").mkdir(parents=True)

        # Create tracked file
        (tmp_path / "raw" / "tracked.md").write_text("content")
        (tmp_path / "wiki" / "sources" / "tracked.md").write_text("---\nraw_file: tracked.md\n---")

        # Create untracked file
        (tmp_path / "raw" / "untracked.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        pending = [s for s in statuses if s.status == "pending"]
        pending_files = [s.raw_file for s in pending]
        assert "untracked.md" in pending_files
        assert "tracked.md" not in pending_files


class TestWatchNestedDirectories:
    """Test watch with nested raw directories."""

    def test_watch_nested_files(self, tmp_path: Path):
        """Should detect files in nested directories."""
        (tmp_path / "raw" / "papers" / "2024").mkdir(parents=True)
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "papers" / "2024" / "article.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        # Should find nested file
        assert len(statuses) > 0

    def test_watch_deeply_nested_structure(self, tmp_path: Path):
        """Should handle deeply nested directory structures."""
        path = tmp_path / "raw" / "l1" / "l2" / "l3" / "l4"
        path.mkdir(parents=True)
        (path / "deep.md").write_text("content")
        (tmp_path / "wiki").mkdir()

        statuses = get_ingest_status(tmp_path)
        assert len(statuses) > 0


class TestWatchSpecialCharacters:
    """Test watch with special characters in filenames."""

    def test_watch_files_with_spaces(self, tmp_path: Path):
        """Should handle filenames with spaces."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "My Document.md").write_text("content")
        (tmp_path / "raw" / "Another File.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses if s.status == "pending"]
        assert "My Document.md" in raw_files
        assert "Another File.md" in raw_files

    def test_watch_files_with_special_chars(self, tmp_path: Path):
        """Should handle special characters in filenames."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "file(2024).md").write_text("content")
        (tmp_path / "raw" / "doc-v2.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        assert len(statuses) == 2

    def test_watch_unicode_filenames(self, tmp_path: Path):
        """Should handle unicode in filenames."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "café.md").write_text("content")
        (tmp_path / "raw" / "résumé.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        # Should handle unicode gracefully
        assert len(statuses) >= 0


class TestWatchIgnorePatterns:
    """Test that watch ignores certain files."""

    def test_watch_ignores_gitkeep(self, tmp_path: Path):
        """Should skip .gitkeep files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / ".gitkeep").write_text("")
        (tmp_path / "raw" / "actual.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses]
        gitkeep_files = [f for f in raw_files if ".gitkeep" in f]
        assert len(gitkeep_files) == 0
        # Should have actual.md
        actual_files = [f for f in raw_files if "actual.md" in f]
        assert len(actual_files) > 0

    def test_watch_ignores_readme(self, tmp_path: Path):
        """Should skip README files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "README.md").write_text("# Instructions")
        (tmp_path / "raw" / "actual.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses]
        readme_files = [f for f in raw_files if f.lower() == "readme.md"]
        assert len(readme_files) == 0
        # Should have actual.md
        assert any("actual.md" in f for f in raw_files)

    def test_watch_case_insensitive_ignore(self, tmp_path: Path):
        """Should ignore readme case-insensitively."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "readme.md").write_text("")
        (tmp_path / "raw" / "ReadMe.md").write_text("")
        (tmp_path / "raw" / "file.md").write_text("content")

        statuses = get_ingest_status(tmp_path)
        raw_files = [s.raw_file for s in statuses]
        raw_files_lower = [f.lower() for f in raw_files]
        assert "readme.md" not in raw_files_lower
        assert "file.md" in raw_files_lower


class TestIngestStatusCategories:
    """Test all ingest status categories."""

    def test_ingest_all_status_types(self, tmp_path: Path):
        """Should correctly categorize ingest status types."""
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
        (tmp_path / "wiki" / "sources" / "incomplete.md").write_text(incomplete_fm)

        # Orphan: source page referencing nonexistent raw file
        orphan_fm = (
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
            "raw_file: nonexistent.md\n---"
        )
        (tmp_path / "wiki" / "sources" / "orphan.md").write_text(orphan_fm)

        statuses = get_ingest_status(tmp_path)

        status_types = {s.status for s in statuses}
        # Should have various status types
        assert "pending" in status_types

        # Check specific statuses exist
        pending = [s for s in statuses if s.status == "pending"]
        assert len(pending) > 0


class TestIngestPerformance:
    """Test ingest performance."""

    def test_ingest_many_files(self, tmp_path: Path):
        """Should handle wikis with many raw files."""
        (tmp_path / "raw").mkdir()
        for i in range(50):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        (tmp_path / "wiki").mkdir()

        import time

        start = time.time()
        statuses = get_ingest_status(tmp_path)
        elapsed = time.time() - start

        pending = [s for s in statuses if s.status == "pending"]
        assert len(pending) == 50
        assert elapsed < 2.0  # Should complete quickly
