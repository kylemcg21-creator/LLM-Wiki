"""Path resolution and security verification."""

from pathlib import Path

from llm_wiki.paths import find_root, raw_dir, templates_dir, wiki_dir


class TestFindRoot:
    """Test wiki root detection."""

    def test_find_root_with_agents_and_index(self, tmp_path: Path):
        """Should find root when AGENTS.md and wiki/index.md exist."""
        root = tmp_path / "test-wiki"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")
        wiki_d = root / "wiki"

        found = find_root(wiki_d)
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
        except RuntimeError:
            pass

    def test_find_root_with_cwd(self, tmp_path: Path):
        """Should find root from current working directory."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        found = find_root(root / "wiki")
        assert found == root


class TestWikiDir:
    """Test wiki directory resolution."""

    def test_wiki_dir_basic(self, tmp_path: Path):
        """Should return wiki directory."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        wiki_d = wiki_dir(root)
        assert wiki_d == root / "wiki"

    def test_wiki_dir_exists(self, tmp_path: Path):
        """Wiki directory should exist."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki").mkdir()
        (root / "wiki" / "index.md").write_text("# Index")

        wiki_d = wiki_dir(root)
        assert wiki_d.exists()

    def test_wiki_dir_from_nested(self, tmp_path: Path):
        """Should find wiki dir from nested path."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        nested = root / "wiki" / "entities"
        nested.mkdir(parents=True)

        wiki_d = wiki_dir(nested)
        assert wiki_d == root / "wiki"


class TestRawDir:
    """Test raw directory resolution."""

    def test_raw_dir_basic(self, tmp_path: Path):
        """Should return raw directory."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        raw_d = raw_dir(root)
        assert raw_d == root / "raw"

    def test_raw_dir_from_nested(self, tmp_path: Path):
        """Should find raw dir from nested path."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        nested = root / "wiki" / "entities"
        nested.mkdir(parents=True)

        raw_d = raw_dir(nested)
        assert raw_d == root / "raw"


class TestTemplatesDir:
    """Test templates directory resolution."""

    def test_templates_dir_basic(self, tmp_path: Path):
        """Should return templates directory."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        tpl_d = templates_dir(root)
        assert tpl_d == root / "templates"

    def test_templates_dir_from_nested(self, tmp_path: Path):
        """Should find templates dir from nested path."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        nested = root / "wiki" / "entities"
        nested.mkdir(parents=True)

        tpl_d = templates_dir(nested)
        assert tpl_d == root / "templates"


class TestPathAbsoluteness:
    """Test that paths are absolute."""

    def test_root_is_absolute(self, tmp_path: Path):
        """Returned root should be absolute."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        found = find_root(root)
        assert found.is_absolute()

    def test_wiki_dir_is_absolute(self, tmp_path: Path):
        """Returned wiki dir should be absolute."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki").mkdir()
        (root / "wiki" / "index.md").write_text("# Index")

        wiki_d = wiki_dir(root)
        assert wiki_d.is_absolute()

    def test_raw_dir_is_absolute(self, tmp_path: Path):
        """Returned raw dir should be absolute."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        raw_d = raw_dir(root)
        assert raw_d.is_absolute()

    def test_templates_dir_is_absolute(self, tmp_path: Path):
        """Returned templates dir should be absolute."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        tpl_d = templates_dir(root)
        assert tpl_d.is_absolute()


class TestPathConsistency:
    """Test path consistency across functions."""

    def test_all_paths_under_root(self, tmp_path: Path):
        """All derived paths should be under root."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        wiki_d = wiki_dir(root)
        raw_d = raw_dir(root)
        tpl_d = templates_dir(root)

        assert str(wiki_d).startswith(str(root))
        assert str(raw_d).startswith(str(root))
        assert str(tpl_d).startswith(str(root))

    def test_paths_are_unique(self, tmp_path: Path):
        """Returned paths should be unique."""
        root = tmp_path / "wiki-root"
        root.mkdir()
        (root / "AGENTS.md").write_text("# Agent")
        (root / "wiki" / "index.md").write_text("# Index")

        wiki_d = wiki_dir(root)
        raw_d = raw_dir(root)
        tpl_d = templates_dir(root)

        paths = [wiki_d, raw_d, tpl_d, root]
        assert len(paths) == len(set(paths))


class TestMissingRoot:
    """Test handling of missing root."""

    def test_find_root_in_empty_dir(self, tmp_path: Path):
        """Should fail when searching from empty directory."""
        empty = tmp_path / "empty"
        empty.mkdir()

        try:
            find_root(empty)
            assert False, "Should raise error"
        except RuntimeError:
            pass
