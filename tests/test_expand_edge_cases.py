"""Edge cases and advanced scenarios for section extraction."""

from pathlib import Path

from llm_wiki.expand import extract_section, list_headings


class TestExpandNoHeadings:
    """Test expand with pages that have no headings."""

    def test_extract_section_no_headings(self):
        """Should return None when page has no headings."""
        text = "Just body content, no headings here."
        assert extract_section(text, "any") is None

    def test_list_headings_empty_page(self):
        """Should return empty list for page with no headings."""
        text = "Body content only"
        headings = list_headings(text)
        assert headings == []

    def test_extract_section_empty_page(self):
        """Should return None for completely empty page."""
        text = ""
        assert extract_section(text, "any") is None


class TestExpandSpecialCharacters:
    """Test expand with special characters in headings."""

    def test_extract_section_heading_with_parens(self):
        """Should match headings with parentheses."""
        text = "# Foo (Bar)\n\nContent here"
        section = extract_section(text, "foo")
        assert section is not None
        assert "Content here" in section.content

    def test_extract_section_heading_with_ampersand(self):
        """Should match headings with ampersands."""
        text = "# Foo & Bar\n\nContent"
        section = extract_section(text, "foo")
        assert section is not None

    def test_extract_section_heading_with_colon(self):
        """Should match headings with colons."""
        text = "# Section: Details\n\nContent"
        section = extract_section(text, "section")
        assert section is not None

    def test_extract_section_heading_with_dash(self):
        """Should match headings with dashes."""
        text = "# Foo-Bar-Baz\n\nContent"
        section = extract_section(text, "foo-bar")
        assert section is not None


class TestExpandHeadingHierarchy:
    """Test expand with deeply nested heading hierarchies."""

    def test_extract_section_deeply_nested(self):
        """Should handle H1-H6 hierarchy correctly."""
        text = (
            "# H1\n\nH1 content\n"
            "## H2\n\nH2 content\n"
            "### H3\n\nH3 content\n"
            "#### H4\n\nH4 content\n"
            "## H2b\n\nH2b content"
        )
        section = extract_section(text, "h3")
        assert section is not None
        assert "H3" in section.heading
        # H4 is nested inside H3, should be included
        assert "H4" in section.content

    def test_extract_section_same_level_not_included(self):
        """Should not include siblings at same level as extracted section."""
        text = "## Section 1\n\nContent 1\n## Section 2\n\nContent 2\n## Section 3\n\nContent 3"
        section = extract_section(text, "section 2")
        assert section is not None
        assert "Section 2" in section.heading
        assert "Content 2" in section.content
        assert "Content 1" not in section.content
        assert "Content 3" not in section.content

    def test_extract_section_mixed_levels(self):
        """Should handle mixed heading levels correctly."""
        text = (
            "# Main\n\nMain content\n"
            "## Sub1\n\nSub1 content\n"
            "### Deep\n\nDeep content\n"
            "## Sub2\n\nSub2 content"
        )
        section = extract_section(text, "sub1")
        assert section is not None
        assert "Deep content" in section.content  # Nested under Sub1
        assert "Sub2 content" not in section.content  # Sibling, not nested


class TestExpandFormattingPreservation:
    """Test that expand preserves markdown formatting."""

    def test_extract_section_preserves_bold(self):
        """Should preserve bold formatting in extracted section."""
        text = "# Section\n\n**Bold text** and normal"
        section = extract_section(text, "section")
        assert section is not None
        assert "**Bold**" in section.content

    def test_extract_section_preserves_italic(self):
        """Should preserve italic formatting."""
        text = "# Section\n\n*Italic text* here"
        section = extract_section(text, "section")
        assert section is not None
        assert "*Italic" in section.content

    def test_extract_section_preserves_code(self):
        """Should preserve inline code."""
        text = "# Section\n\n`const x = 5;` in text"
        section = extract_section(text, "section")
        assert section is not None
        assert "`const" in section.content

    def test_extract_section_preserves_links(self):
        """Should preserve markdown links."""
        text = "# Section\n\n[Link text](https://example.com)"
        section = extract_section(text, "section")
        assert section is not None
        assert "[Link" in section.content


class TestExpandWikilinks:
    """Test wikilink extraction from sections."""

    def test_extract_section_with_wikilinks(self):
        """Should extract wikilinks from section content."""
        text = "# Section\n\nSee [[related-page]] and [[another]]"
        section = extract_section(text, "section")
        assert section is not None
        assert "related-page" in section.outbound_links
        assert "another" in section.outbound_links

    def test_extract_section_wikilinks_sorted(self):
        """Should return sorted unique wikilinks."""
        text = "# Section\n\n[[z-page]] and [[a-page]] and [[z-page]] again"
        section = extract_section(text, "section")
        assert section is not None
        assert section.outbound_links == ["a-page", "z-page"]

    def test_extract_section_no_wikilinks(self):
        """Should return empty list when no wikilinks."""
        text = "# Section\n\nNo links here"
        section = extract_section(text, "section")
        assert section is not None
        assert section.outbound_links == []


class TestExpandEdgeCasesMatching:
    """Test edge cases in heading matching logic."""

    def test_extract_section_case_insensitive_match(self):
        """Should match headings case-insensitively."""
        text = "# MySection\n\nContent"
        section = extract_section(text, "MYSECTION")
        assert section is not None

    def test_extract_section_whitespace_normalization(self):
        """Should normalize whitespace in heading matching."""
        text = "# My  Section\n\nContent"
        section = extract_section(text, "my section")
        assert section is not None

    def test_extract_section_partial_word_match(self):
        """Should match partial words separated by dashes/underscores."""
        text = "# foo-bar-baz\n\nContent"
        section = extract_section(text, "bar")
        assert section is not None
        assert "foo-bar-baz" in section.heading

    def test_extract_section_no_substring_match_in_word(self):
        """Should not match substring within a single word."""
        text = "# Synthesis\n\nContent"
        section = extract_section(text, "thesis")
        # Should not match "thesis" within "Synthesis"
        assert section is None


class TestExpandPerformance:
    """Test expand performance with large pages."""

    def test_list_headings_large_page(self, tmp_path: Path):
        """Should efficiently extract headings from large pages."""
        # Create page with 1000 headings
        lines = []
        for i in range(1000):
            lines.append(f"## Heading {i}\n\nContent for heading {i}\n")
        text = "\n".join(lines)

        import time

        start = time.time()
        headings = list_headings(text)
        elapsed = time.time() - start

        assert len(headings) == 1000
        assert elapsed < 1.0  # Should complete in under 1 second

    def test_extract_section_large_content(self):
        """Should extract section from page with large content."""
        # Create page with large content
        large_content = "x " * 10000  # 20k characters
        text = f"# Start\n\n{large_content}\n## Middle\n\nMiddle content\n## End\n\nEnd"

        section = extract_section(text, "middle")
        assert section is not None
        assert "Middle content" in section.content
        assert "Start" not in section.heading
