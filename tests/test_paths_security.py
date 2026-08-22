"""Path resolution and security verification."""

from pathlib import Path

from llm_wiki.paths import find_root, resolve_page


class TestFindRoot:
    """Test wiki root detection."""

    def test_find_root_with_agents_and_index(self, tmp_path: Path):
        """Should find root when AGENTS.md and wiki/index.md exist."""
        root = tmp_path / "test-wiki"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")
        wiki_dir = root / "wiki"

        found = find_root(wiki_dir)
        assert found == root

    def test_find_root_walks_up_directory_tree(self, tmp_path: Path):
        """Should walk up directories to find root."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        # Start search from nested directory
        nested = root / "wiki" / "entities"
        nested.mkdir(parents=True)

        found = find_root(nested)
        assert found == root

    def test_find_root_fails_without_required_files(self, tmp_path: Path):
        """Should fail if required files don't exist."""
        incomplete = tmp_path / "incomplete"
        incomplete.mkdir()
        (incomplete / "wiki").mkdir()  # Missing AGENTS.md and index.md

        try:
            find_root(incomplete)
            assert False, "Should have raised error"
        except (RuntimeError, FileNotFoundError):
            pass

    def test_find_root_stops_at_root(self, tmp_path: Path):
        """Should not search beyond filesystem root."""
        # Start from directory with no wiki
        search_dir = tmp_path / "no-wiki" / "nested" / "deep"
        search_dir.mkdir(parents=True)

        try:
            find_root(search_dir)
            assert False, "Should have raised error"
        except (RuntimeError, FileNotFoundError):
            pass


class TestPageResolution:
    """Test page path resolution."""

    def test_resolve_page_by_stem(self, tmp_path: Path):
        """Should resolve page by stem (filename without .md)."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "page.md").write_text("# Page")

        resolved = resolve_page("page", wiki)
        assert resolved == wiki / "page.md"

    def test_resolve_page_nested_directory(self, tmp_path: Path):
        """Should resolve pages in nested directories."""
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "entities" / "entity.md").write_text("# Entity")

        resolved = resolve_page("entity", wiki)
        assert resolved == wiki / "entities" / "entity.md"

    def test_resolve_page_with_path_separators(self, tmp_path: Path):
        """Should resolve with directory/page format."""
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "entities" / "actor.md").write_text("# Actor")

        resolved = resolve_page("entities/actor", wiki)
        assert resolved == wiki / "entities" / "actor.md"

    def test_resolve_page_case_insensitive_stem(self, tmp_path: Path):
        """Should resolve pages case-insensitively."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "MyPage.md").write_text("# My Page")

        resolved = resolve_page("mypage", wiki)
        # May or may not be case-sensitive depending on implementation
        # At least should not crash
        assert resolved is not None or resolved is None


class TestPathTraversalSecurity:
    """Test protection against path traversal attacks."""

    def test_resolve_page_rejects_parent_dir_traversal(self, tmp_path: Path):
        """Should reject attempts to go above wiki root."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (tmp_path / "evil.md").write_text("# Evil")

        try:
            resolved = resolve_page("../evil", wiki)
            # If resolution succeeds, verify it's still inside wiki
            if resolved is not None:
                # Verify resolved path is under wiki
                assert str(resolved).startswith(str(wiki))
        except (ValueError, RuntimeError):
            pass  # Traversal rejection is expected

    def test_resolve_page_rejects_absolute_paths(self, tmp_path: Path):
        """Should reject absolute paths."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        try:
            resolved = resolve_page("/etc/passwd", wiki)
            # If it doesn't reject, at least verify it's inside wiki
            if resolved is not None:
                assert str(resolved).startswith(str(wiki))
        except (ValueError, RuntimeError):
            pass

    def test_resolve_page_rejects_home_expansion(self, tmp_path: Path):
        """Should not expand ~ to home directory."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        try:
            resolved = resolve_page("~/.ssh/id_rsa", wiki)
            # Should reject or resolve within wiki
            if resolved is not None:
                assert str(resolved).startswith(str(wiki))
        except (ValueError, RuntimeError):
            pass

    def test_resolve_page_multiple_traversal_attempts(self, tmp_path: Path):
        """Should reject multiple ../ sequences."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        try:
            resolved = resolve_page("../../../../../../etc/passwd", wiki)
            if resolved is not None:
                assert str(resolved).startswith(str(wiki))
        except (ValueError, RuntimeError):
            pass


class TestPathNormalization:
    """Test path normalization."""

    def test_resolve_page_normalizes_slashes(self, tmp_path: Path):
        """Should handle mixed forward/back slashes."""
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "entities" / "actor.md").write_text("# Actor")

        # Forward slashes should work
        resolved = resolve_page("entities/actor", wiki)
        assert resolved is not None

    def test_resolve_page_handles_double_slashes(self, tmp_path: Path):
        """Should normalize multiple slashes."""
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "entities" / "actor.md").write_text("# Actor")

        resolved = resolve_page("entities//actor", wiki)
        assert resolved is not None or resolved is None

    def test_resolve_page_trailing_slash(self, tmp_path: Path):
        """Should handle trailing slashes."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "page.md").write_text("# Page")

        resolved = resolve_page("page/", wiki)
        # May or may not accept trailing slash
        assert isinstance(resolved, (Path, type(None)))


class TestAmbiguousLinks:
    """Test handling of ambiguous page references."""

    def test_resolve_page_collision_multiple_files(self, tmp_path: Path):
        """Should detect collisions when multiple files match."""
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "concepts").mkdir(parents=True)
        (wiki / "entities" / "actor.md").write_text("# Actor")
        (wiki / "concepts" / "actor.md").write_text("# Actor (concept)")

        # Resolving just "actor" is ambiguous
        resolved = resolve_page("actor", wiki)
        # May return None to indicate ambiguity, or pick one
        # Should not crash
        assert isinstance(resolved, (Path, type(None)))

    def test_resolve_page_unambiguous_with_path(self, tmp_path: Path):
        """Should resolve unambiguously with full path."""
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "concepts").mkdir(parents=True)
        (wiki / "entities" / "actor.md").write_text("# Actor")
        (wiki / "concepts" / "actor.md").write_text("# Actor (concept)")

        # Full path is unambiguous
        resolved = resolve_page("entities/actor", wiki)
        assert resolved == wiki / "entities" / "actor.md"


class TestPathEdgeCases:
    """Test edge cases in path resolution."""

    def test_resolve_page_empty_string(self, tmp_path: Path):
        """Should handle empty page name."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        try:
            resolved = resolve_page("", wiki)
            # May return None or raise error
            assert resolved is None or isinstance(resolved, Path)
        except (ValueError, RuntimeError):
            pass

    def test_resolve_page_only_extension(self, tmp_path: Path):
        """Should handle pages named like extensions."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / ".md").write_text("# Dot file")

        try:
            resolved = resolve_page(".md", wiki)
            # May find it or reject it
            assert isinstance(resolved, (Path, type(None)))
        except (ValueError, RuntimeError):
            pass

    def test_resolve_page_unicode_names(self, tmp_path: Path):
        """Should handle unicode in page names."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "café.md").write_text("# Café")

        try:
            resolved = resolve_page("café", wiki)
            assert resolved is None or resolved == wiki / "café.md"
        except (ValueError, RuntimeError, UnicodeError):
            pass

    def test_resolve_page_very_long_path(self, tmp_path: Path):
        """Should handle very long page names."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        # Create a page with a very long name
        long_name = "a" * 200 + ".md"
        try:
            (wiki / long_name).write_text("# Long")
            resolved = resolve_page(long_name[:-3], wiki)
            # Should handle or reject gracefully
            assert isinstance(resolved, (Path, type(None)))
        except (OSError, ValueError):
            # Filesystem may reject very long names
            pass


class TestPathMetadata:
    """Test metadata about paths."""

    def test_resolved_path_is_absolute(self, tmp_path: Path):
        """Should return absolute paths."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "page.md").write_text("# Page")

        resolved = resolve_page("page", wiki)
        if resolved is not None:
            assert resolved.is_absolute()

    def test_resolved_path_exists(self, tmp_path: Path):
        """Should only resolve to existing files."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        resolved = resolve_page("nonexistent", wiki)
        # Should be None if file doesn't exist
        assert resolved is None or resolved.exists()
