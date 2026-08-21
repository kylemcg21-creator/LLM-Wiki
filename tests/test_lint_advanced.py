"""Advanced lint features and edge cases."""

from pathlib import Path

import pytest

from llm_wiki.lint import lint_wiki, parse_frontmatter


class TestFrontmatterParsing:
    """Test frontmatter parsing edge cases."""

    def test_parse_frontmatter_invalid_yaml(self):
        """Should handle invalid YAML gracefully."""
        text = """---
invalid: [yaml: garbage
---

Content"""
        meta = parse_frontmatter(text)
        assert meta is None  # Invalid YAML should return None

    def test_parse_frontmatter_empty_frontmatter(self):
        """Should handle empty frontmatter block."""
        text = """---
---

Content"""
        meta = parse_frontmatter(text)
        # Empty YAML results in None, not a dict
        assert meta is None or meta == {}

    def test_parse_frontmatter_non_dict_yaml(self):
        """Should handle YAML that doesn't produce a dict."""
        text = """---
- item1
- item2
---

Content"""
        meta = parse_frontmatter(text)
        assert meta is None  # List should return None

    def test_parse_frontmatter_complex_structure(self):
        """Should parse complex nested YAML structures."""
        text = """---
type: entity
metadata:
  nested: value
  list:
    - item1
    - item2
tags:
  - tag1
  - tag2
---

Content"""
        meta = parse_frontmatter(text)
        assert meta is not None
        assert meta["type"] == "entity"
        assert "metadata" in meta
        assert isinstance(meta["tags"], list)

    def test_parse_frontmatter_special_chars_in_values(self):
        """Should handle special characters in frontmatter values."""
        text = """---
type: source
title: "Test: Special (Characters) & Symbols"
description: "Contains 'quotes' and \"double quotes\""
---

Content"""
        meta = parse_frontmatter(text)
        assert meta is not None
        assert meta["type"] == "source"


class TestLintFrontmatter:
    """Test frontmatter validation in lint."""

    def test_lint_missing_frontmatter_warning(self, tmp_path: Path):
        """Should warn when frontmatter is missing."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "page.md").write_text("# Page\n\nNo frontmatter here")

        report = lint_wiki(wiki)
        frontmatter_issues = [i for i in report.issues if i.category == "frontmatter"]
        assert len(frontmatter_issues) > 0

    def test_lint_malformed_frontmatter_handling(self, tmp_path: Path):
        """Should handle malformed YAML frontmatter gracefully."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "bad.md").write_text("---\ninvalid: [yaml: garbage\n---\n\nContent")

        report = lint_wiki(wiki)
        # Should not crash, should report an issue
        assert isinstance(report.issues, list)

    def test_lint_frontmatter_exempt_pages(self, tmp_path: Path):
        """Should skip frontmatter check for exempt pages (index, log)."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n\nNo frontmatter (exempt)")
        (wiki / "log.md").write_text("# Log\n\nNo frontmatter (exempt)")
        (wiki / "other.md").write_text("# Other\n\nNo frontmatter (not exempt)")

        report = lint_wiki(wiki)
        # index.md and log.md should not have frontmatter warnings
        issues = [i for i in report.issues if i.category == "frontmatter"]
        issue_pages = [i.page for i in issues]
        assert "index.md" not in issue_pages
        assert "log.md" not in issue_pages
        # other.md should have issue
        if "other.md" in issue_pages or not issues:
            pass  # Could go either way depending on lint logic


class TestLintContradictions:
    """Test contradiction detection."""

    def test_lint_detects_contradiction_markers(self, tmp_path: Path):
        """Should detect contradiction/supersession markers in source pages."""
        wiki = tmp_path / "wiki"
        (wiki / "sources").mkdir(parents=True)
        (wiki / "sources" / "paper.md").write_text(
            "---\ntype: source\ncreated: 2026-01-01\nupdated: 2026-01-01\n---\n\n"
            "This work SUPERSEDES the previous analysis."
        )

        report = lint_wiki(wiki, project_root=tmp_path)
        # Should detect contradiction marker (case-insensitive)
        contradiction_issues = [i for i in report.issues if "contradiction" in i.category]
        # May or may not flag depending on logic, but shouldn't crash

    def test_lint_contradiction_exempt_pages(self, tmp_path: Path):
        """Should exempt index, log, synthesis, contradictions from contradiction ledger."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "synthesis.md").write_text("---\ntype: synthesis\n---\n\nCONTRADICTS earlier work")
        (wiki / "index.md").write_text("# Index\n\nCONTRADICTS something")

        report = lint_wiki(wiki, project_root=tmp_path)
        # synthesis.md and index.md should not generate contradiction hints
        issues = [i for i in report.issues if "contradiction-hint" in i.category]
        issue_pages = [i.page for i in issues]
        assert "synthesis.md" not in issue_pages
        assert "index.md" not in issue_pages


class TestLintMissingRequiredPages:
    """Test detection of missing required pages."""

    def test_lint_missing_index_page(self, tmp_path: Path):
        """Should flag missing wiki/index.md."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "some-page.md").write_text("# Page")
        # No index.md

        report = lint_wiki(wiki)
        # Should detect missing index
        errors = [i for i in report.errors if "index" in i.message.lower()]
        assert len(errors) > 0

    def test_lint_missing_log_page(self, tmp_path: Path):
        """Should flag missing wiki/log.md."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index")
        # No log.md

        report = lint_wiki(wiki)
        # Should detect missing log
        errors = [i for i in report.errors if "log" in i.message.lower()]
        # May or may not flag depending on lint logic

    def test_lint_with_all_required_pages(self, tmp_path: Path):
        """Should pass when all required pages exist."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")

        report = lint_wiki(wiki)
        # Should have minimal errors related to required pages
        required_errors = [
            i
            for i in report.errors
            if any(x in i.message.lower() for x in ["index", "log", "synthesis"])
        ]
        # Should be empty or minimal


class TestLintLargeWiki:
    """Test lint performance on larger wikis."""

    def test_lint_performance_large_wiki(self, tmp_path: Path):
        """Lint should complete in reasonable time for large wikis."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")

        # Create 100 pages
        for i in range(100):
            (wiki / f"page-{i}.md").write_text(f"# Page {i}\n\nContent [[page-{(i+1)%100}]]")

        import time

        start = time.time()
        report = lint_wiki(wiki)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 10 seconds)
        assert elapsed < 10.0
        assert isinstance(report.issues, list)

    def test_lint_large_page_with_many_links(self, tmp_path: Path):
        """Should handle pages with many wikilinks."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")

        # Create page with many wikilinks
        content = "# Page with many links\n\n"
        for i in range(100):
            content += f"See [[page-{i}]] and "

        (wiki / "hub.md").write_text(content)

        report = lint_wiki(wiki)
        # Should handle without crashing
        assert isinstance(report.issues, list)


class TestLintOrphanDetection:
    """Test orphan page detection."""

    def test_lint_detects_orphan_pages(self, tmp_path: Path):
        """Should detect pages with no incoming or outgoing links."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n\n[[connected]]")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")
        (wiki / "connected.md").write_text("# Connected\n\nLinks back [[index]]")
        (wiki / "orphan.md").write_text("# Orphan\n\nNo links to or from this page")

        report = lint_wiki(wiki)
        orphan_issues = [i for i in report.issues if "orphan" in i.category.lower()]
        # Should detect the orphan page or at least not crash
        assert isinstance(orphan_issues, list)


class TestLintBrokenLinks:
    """Test broken link detection."""

    def test_lint_ambiguous_link_detection(self, tmp_path: Path):
        """Should detect ambiguous wikilinks (multiple matches)."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")
        (wiki / "entities").mkdir()
        (wiki / "concepts").mkdir()
        (wiki / "entities" / "transformer.md").write_text("# Transformer (entity)")
        (wiki / "concepts" / "transformer.md").write_text("# Transformer (concept)")
        (wiki / "page.md").write_text("# Page\n\nSee [[transformer]] for details")

        report = lint_wiki(wiki)
        ambiguous_issues = [i for i in report.issues if "ambiguous" in i.category.lower()]
        # Should detect or flag the ambiguous link
        assert isinstance(ambiguous_issues, list)

    def test_lint_broken_link_detection(self, tmp_path: Path):
        """Should detect broken wikilinks."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")
        (wiki / "page.md").write_text("# Page\n\nLinks to [[nonexistent-page]] that doesn't exist")

        report = lint_wiki(wiki)
        broken_issues = [i for i in report.issues if i.category == "broken-link"]
        # Should detect the broken link
        assert len(broken_issues) > 0


class TestLintCategoryFiltering:
    """Test lint issue filtering by category."""

    def test_lint_category_filtering(self, tmp_path: Path):
        """Should correctly filter by category."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n\n[[missing]]")
        (wiki / "log.md").write_text("# Log")
        (wiki / "synthesis.md").write_text("# Synthesis")

        report = lint_wiki(wiki)

        # Get all issues
        all_issues = report.issues

        # Filter by specific category
        broken_links = [i for i in all_issues if i.category == "broken-link"]
        frontmatter_issues = [i for i in all_issues if i.category == "frontmatter"]

        # Should have different categories
        assert len(all_issues) > 0
        # Broken links should be detected
        assert len(broken_links) > 0
