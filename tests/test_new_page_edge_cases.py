"""Edge cases and advanced scenarios for new page creation."""

from pathlib import Path

from llm_wiki.new_page import _slugify, _title_from_slug, create_page


class TestSlugGeneration:
    """Test slug generation and normalization."""

    def test_slugify_basic(self):
        """Should convert spaces to dashes."""
        assert _slugify("my entity name") == "my-entity-name"

    def test_slugify_uppercase(self):
        """Should convert to lowercase."""
        assert _slugify("MyEntity") == "myentity"

    def test_slugify_special_chars(self):
        """Should remove special characters."""
        result = _slugify("entity (deprecated)")
        assert "entity" in result
        assert "deprecated" in result

    def test_slugify_multiple_dashes(self):
        """Should collapse multiple dashes."""
        result = _slugify("test  --  entity")
        assert "--" not in result

    def test_slugify_empty_slug(self):
        """Should reject empty slugs."""
        assert _slugify("!!!") == ""

    def test_title_from_slug(self):
        """Should generate title from slug."""
        assert _title_from_slug("my-entity-name") == "My Entity Name"

    def test_title_from_slug_single_word(self):
        """Should handle single word slugs."""
        assert _title_from_slug("entity") == "Entity"

    def test_title_from_slug_with_dashes(self):
        """Should capitalize each part."""
        assert _title_from_slug("test-entity-page") == "Test Entity Page"


class TestCreatePageBasic:
    """Test basic page creation."""

    def test_create_entity_page(self, tmp_path: Path):
        """Should create entity page."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)

        result = create_page(tmp_path, page_type="entity", slug="test-entity", title="Test Entity")
        assert result.path.exists()
        assert "entities" in str(result.path)

    def test_create_concept_page(self, tmp_path: Path):
        """Should create concept page."""
        (tmp_path / "templates" / "concept.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "concept.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "concepts").mkdir(parents=True)

        result = create_page(tmp_path, page_type="concept", slug="test-concept")
        assert result.path.exists()
        assert "concepts" in str(result.path)

    def test_create_source_page(self, tmp_path: Path):
        """Should create source page."""
        (tmp_path / "templates" / "source.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "source.md").write_text("---\ntype: source\n---\n")
        (tmp_path / "wiki" / "sources").mkdir(parents=True)

        result = create_page(tmp_path, page_type="source", slug="test-source")
        assert result.path.exists()
        assert "sources" in str(result.path)

    def test_create_answer_page(self, tmp_path: Path):
        """Should create answer page."""
        (tmp_path / "templates" / "answer.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "answer.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "answers").mkdir(parents=True)

        result = create_page(tmp_path, page_type="answer", slug="test-answer")
        assert result.path.exists()
        assert "answers" in str(result.path)


class TestCreatePageWithForce:
    """Test overwrite behavior."""

    def test_create_fails_without_force(self, tmp_path: Path):
        """Should fail when page exists without force."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)
        existing = tmp_path / "wiki" / "entities" / "test.md"
        existing.write_text("# Old")

        try:
            create_page(tmp_path, page_type="entity", slug="test", force=False)
            assert False, "Should have raised FileExistsError"
        except FileExistsError:
            pass

    def test_create_with_force_succeeds(self, tmp_path: Path):
        """Should overwrite when force=True."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)
        existing = tmp_path / "wiki" / "entities" / "test.md"
        existing.write_text("# Old")

        result = create_page(tmp_path, page_type="entity", slug="test", force=True)
        assert result.created or result.path.exists()


class TestCreatePageErrors:
    """Test error handling in page creation."""

    def test_create_unknown_type(self, tmp_path: Path):
        """Should reject unknown page types."""
        try:
            create_page(tmp_path, page_type="unknown", slug="test")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown page type" in str(e)

    def test_create_empty_slug(self, tmp_path: Path):
        """Should reject empty slugs."""
        try:
            create_page(tmp_path, page_type="entity", slug="")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_create_missing_template(self, tmp_path: Path):
        """Should fail if template doesn't exist."""
        (tmp_path / "wiki" / "entities").mkdir(parents=True)
        # No templates directory

        try:
            create_page(tmp_path, page_type="entity", slug="test")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass


class TestCreatePageNormalization:
    """Test slug normalization during creation."""

    def test_create_with_spaces_in_slug(self, tmp_path: Path):
        """Should normalize spaces to dashes."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)

        result = create_page(tmp_path, page_type="entity", slug="my entity name")
        assert "my-entity-name" in str(result.path)

    def test_create_with_uppercase_slug(self, tmp_path: Path):
        """Should normalize to lowercase."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)

        result = create_page(tmp_path, page_type="entity", slug="MyEntity")
        assert "myentity" in str(result.path).lower()


class TestCreatePageResult:
    """Test NewPageResult attributes."""

    def test_result_has_rel_path(self, tmp_path: Path):
        """Result should have relative path."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)

        result = create_page(tmp_path, page_type="entity", slug="test")
        assert result.rel_path
        assert "entities" in result.rel_path

    def test_result_has_absolute_path(self, tmp_path: Path):
        """Result path should be absolute."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)

        result = create_page(tmp_path, page_type="entity", slug="test")
        assert result.path.is_absolute()

    def test_result_created_flag(self, tmp_path: Path):
        """Result should indicate if page was created."""
        (tmp_path / "templates" / "entity.md").parent.mkdir(parents=True)
        (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
        (tmp_path / "wiki" / "entities").mkdir(parents=True)

        result = create_page(tmp_path, page_type="entity", slug="test")
        assert result.created is True
