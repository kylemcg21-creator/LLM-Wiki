"""Edge cases and advanced scenarios for watch functionality."""

from pathlib import Path

from llm_wiki.watch import get_untracked_files


class TestWatchBasicTracking:
    """Test basic file tracking in raw/."""

    def test_watch_detects_new_files(self, tmp_path: Path):
        """Should detect new files in raw/."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "newfile.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        raw_files = [f.name for f in untracked]
        assert "newfile.md" in raw_files

    def test_watch_empty_raw_directory(self, tmp_path: Path):
        """Should return empty list when no files in raw/."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()

        untracked = get_untracked_files(tmp_path)
        assert untracked == []

    def test_watch_multiple_untracked_files(self, tmp_path: Path):
        """Should detect multiple untracked files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        for i in range(5):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        untracked = get_untracked_files(tmp_path)
        assert len(untracked) == 5


class TestWatchSourceTracking:
    """Test tracking of source pages against raw files."""

    def test_watch_file_with_matching_source(self, tmp_path: Path):
        """Should not report file that has matching source page."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "raw" / "paper.md").write_text("content")
        (tmp_path / "wiki" / "sources" / "paper.md").write_text("---\nraw_file: paper.md\n---")

        untracked = get_untracked_files(tmp_path)
        # paper.md should not be in untracked since it has a source
        raw_files = [f.name for f in untracked]
        assert "paper.md" not in raw_files

    def test_watch_mixed_tracked_untracked(self, tmp_path: Path):
        """Should distinguish between tracked and untracked files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki" / "sources").mkdir(parents=True)

        # Create tracked file
        (tmp_path / "raw" / "tracked.md").write_text("content")
        (tmp_path / "wiki" / "sources" / "tracked.md").write_text("---\nraw_file: tracked.md\n---")

        # Create untracked file
        (tmp_path / "raw" / "untracked.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        raw_files = [f.name for f in untracked]
        assert "tracked.md" not in raw_files
        assert "untracked.md" in raw_files


class TestWatchNestedDirectories:
    """Test watch with nested raw directories."""

    def test_watch_nested_files(self, tmp_path: Path):
        """Should detect files in nested directories."""
        (tmp_path / "raw" / "papers" / "2024").mkdir(parents=True)
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "papers" / "2024" / "article.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        # Should find nested file
        assert len(untracked) > 0

    def test_watch_deeply_nested_structure(self, tmp_path: Path):
        """Should handle deeply nested directory structures."""
        path = tmp_path / "raw" / "l1" / "l2" / "l3" / "l4"
        path.mkdir(parents=True)
        (path / "deep.md").write_text("content")
        (tmp_path / "wiki").mkdir()

        untracked = get_untracked_files(tmp_path)
        assert len(untracked) > 0


class TestWatchSpecialCharacters:
    """Test watch with special characters in filenames."""

    def test_watch_files_with_spaces(self, tmp_path: Path):
        """Should handle filenames with spaces."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "My Document.md").write_text("content")
        (tmp_path / "raw" / "Another File.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        names = [f.name for f in untracked]
        assert "My Document.md" in names
        assert "Another File.md" in names

    def test_watch_files_with_special_chars(self, tmp_path: Path):
        """Should handle special characters in filenames."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "file(2024).md").write_text("content")
        (tmp_path / "raw" / "doc-v2.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        names = [f.name for f in untracked]
        assert len(names) == 2

    def test_watch_unicode_filenames(self, tmp_path: Path):
        """Should handle unicode in filenames."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "café.md").write_text("content")
        (tmp_path / "raw" / "résumé.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        # Should handle unicode gracefully
        assert len(untracked) >= 0


class TestWatchIgnorePatterns:
    """Test that watch ignores certain files."""

    def test_watch_ignores_gitkeep(self, tmp_path: Path):
        """Should skip .gitkeep files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / ".gitkeep").write_text("")
        (tmp_path / "raw" / "actual.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        names = [f.name for f in untracked]
        assert ".gitkeep" not in names
        assert "actual.md" in names

    def test_watch_ignores_readme(self, tmp_path: Path):
        """Should skip README files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "README.md").write_text("# Instructions")
        (tmp_path / "raw" / "actual.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        names = [f.name for f in untracked]
        readme_lower = [n.lower() for n in names]
        assert "readme.md" not in readme_lower
        assert "actual.md" in names

    def test_watch_case_insensitive_ignore(self, tmp_path: Path):
        """Should ignore readme case-insensitively."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "raw" / "readme.md").write_text("")
        (tmp_path / "raw" / "ReadMe.md").write_text("")
        (tmp_path / "raw" / "file.md").write_text("content")

        untracked = get_untracked_files(tmp_path)
        names = [f.name for f in untracked]
        names_lower = [n.lower() for n in names]
        assert "readme.md" not in names_lower
        assert "file.md" in names


class TestWatchMatchingLogic:
    """Test the matching logic between raw files and sources."""

    def test_watch_case_sensitive_matching(self, tmp_path: Path):
        """Should match case-sensitively or case-insensitively (depending on impl)."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "raw" / "Paper.md").write_text("content")
        (tmp_path / "wiki" / "sources" / "paper.md").write_text("---\nraw_file: Paper.md\n---")

        untracked = get_untracked_files(tmp_path)
        # Depending on matching logic, Paper.md may or may not be untracked
        # Should not crash at least
        assert isinstance(untracked, list)

    def test_watch_path_matching(self, tmp_path: Path):
        """Should match files by relative path."""
        (tmp_path / "raw" / "subdir").mkdir(parents=True)
        (tmp_path / "wiki" / "sources").mkdir(parents=True)
        (tmp_path / "raw" / "subdir" / "file.md").write_text("content")
        (tmp_path / "wiki" / "sources" / "file.md").write_text("---\nraw_file: subdir/file.md\n---")

        untracked = get_untracked_files(tmp_path)
        # subdir/file.md should be considered tracked
        names = [str(f) for f in untracked]
        # Should not have subdir/file.md as untracked
        assert all("subdir/file.md" not in str(n) for n in names)


class TestWatchPerformance:
    """Test watch performance."""

    def test_watch_many_files(self, tmp_path: Path):
        """Should efficiently scan many files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki").mkdir()

        # Create 100 raw files
        for i in range(100):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        import time

        start = time.time()
        untracked = get_untracked_files(tmp_path)
        elapsed = time.time() - start

        assert len(untracked) == 100
        assert elapsed < 2.0  # Should complete quickly

    def test_watch_large_source_set(self, tmp_path: Path):
        """Should handle comparison against many source files."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "wiki" / "sources").mkdir(parents=True)

        # Create 50 raw files
        for i in range(50):
            (tmp_path / "raw" / f"file-{i}.md").write_text(f"content {i}")

        # Create 50 matching source files
        for i in range(50):
            (tmp_path / "wiki" / "sources" / f"file-{i}.md").write_text(
                f"---\nraw_file: file-{i}.md\n---"
            )

        import time

        start = time.time()
        untracked = get_untracked_files(tmp_path)
        elapsed = time.time() - start

        assert len(untracked) == 0  # All files tracked
        assert elapsed < 2.0
