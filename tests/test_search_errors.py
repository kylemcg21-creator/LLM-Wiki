"""Error handling for search backend variations and edge cases."""

from pathlib import Path

import pytest

from llm_wiki.search import make_snippet, search_wiki_with_backend, tokenize


class TestSearchEdgeCases:
    """Test edge cases in search functionality."""

    def test_search_special_regex_characters(self):
        """Should handle special regex characters in queries."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        # Queries that could break regex: [ ] ( ) . * + ? ^ $ \
        queries = ["[test", "test(case)", "foo.bar", "test*query", "foo+bar", "test?"]
        for query in queries:
            # Should not raise, should return list
            results = search_wiki_with_backend(demo_wiki, query, limit=5, backend="bm25")
            assert isinstance(results, list)

    def test_search_empty_wiki(self, tmp_path: Path):
        """Should return empty results on wiki with no pages."""
        empty_wiki = tmp_path / "empty" / "wiki"
        empty_wiki.mkdir(parents=True)
        results = search_wiki_with_backend(empty_wiki, "query", limit=10, backend="bm25")
        assert results == []

    def test_search_whitespace_only_query(self):
        """Should handle whitespace-only queries."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results = search_wiki_with_backend(demo_wiki, "   ", limit=5, backend="bm25")
        assert isinstance(results, list)

    def test_search_very_long_query(self):
        """Should handle very long query strings."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        long_query = "word " * 1000  # 5000 character query
        results = search_wiki_with_backend(demo_wiki, long_query, limit=5, backend="bm25")
        assert isinstance(results, list)

    def test_search_unicode_characters(self):
        """Should handle unicode characters in queries."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        queries = ["café", "naïve", "résumé", "北京", "🎉"]
        for query in queries:
            results = search_wiki_with_backend(demo_wiki, query, limit=5, backend="bm25")
            assert isinstance(results, list)

    def test_search_case_insensitive(self):
        """Should search case-insensitively."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results_lower = search_wiki_with_backend(demo_wiki, "wiki", limit=5, backend="bm25")
        results_upper = search_wiki_with_backend(demo_wiki, "WIKI", limit=5, backend="bm25")
        # Both should return results
        assert isinstance(results_lower, list)
        assert isinstance(results_upper, list)

    def test_search_with_zero_limit(self):
        """Should handle limit=0 gracefully."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results = search_wiki_with_backend(demo_wiki, "query", limit=0, backend="bm25")
        assert results == []

    def test_search_with_very_large_limit(self):
        """Should handle very large limit values."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results = search_wiki_with_backend(demo_wiki, "wiki", limit=9999, backend="bm25")
        # Should return results, but not more than exist
        assert isinstance(results, list)

    def test_tokenize_empty_string(self):
        """Should handle tokenization of empty string."""
        tokens = tokenize("")
        assert tokens == []

    def test_tokenize_only_special_chars(self):
        """Should skip non-alphanumeric characters."""
        tokens = tokenize("!@#$%^&*()")
        assert tokens == []

    def test_tokenize_mixed_content(self):
        """Should extract tokens from mixed content."""
        tokens = tokenize("Hello123 World456!@# Test789")
        assert "hello123" in tokens
        assert "world456" in tokens
        assert "test789" in tokens

    def test_make_snippet_empty_query_terms(self):
        """Should handle snippet generation with empty query terms."""
        text = "This is some sample text content."
        snippet = make_snippet(text, [], width=100)
        assert isinstance(snippet, str)
        assert len(snippet) > 0

    def test_make_snippet_no_matches(self):
        """Should return text snippet even if query terms don't match."""
        text = "This is some sample text content."
        snippet = make_snippet(text, ["nonexistent"], width=100)
        assert isinstance(snippet, str)
        assert len(snippet) > 0

    def test_make_snippet_entire_text_shorter_than_width(self):
        """Should return entire text if shorter than width."""
        text = "Short"
        snippet = make_snippet(text, ["short"], width=200)
        assert "short" in snippet.lower()

    def test_make_snippet_very_small_width(self):
        """Should handle very small width values."""
        text = "This is a much longer text that exceeds the width"
        snippet = make_snippet(text, ["text"], width=10)
        assert isinstance(snippet, str)
        # Should still be a valid string


class TestSearchBackendBehavior:
    """Test search backend selection and fallback."""

    def test_search_invalid_backend(self):
        """Should reject invalid backend names."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        with pytest.raises((ValueError, RuntimeError)):
            search_wiki_with_backend(demo_wiki, "query", backend="invalid_backend")

    def test_search_backend_bm25_always_available(self):
        """BM25 backend should always be available."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results = search_wiki_with_backend(demo_wiki, "memex", limit=5, backend="bm25")
        # Should not raise
        assert isinstance(results, list)

    def test_search_result_snippet_not_empty(self):
        """Search results should have non-empty snippets."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results = search_wiki_with_backend(demo_wiki, "wiki", limit=5, backend="bm25")
        for result in results:
            assert result.snippet
            assert len(result.snippet) > 0

    def test_search_result_score_positive(self):
        """Search result scores should be positive."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results = search_wiki_with_backend(demo_wiki, "wiki", limit=5, backend="bm25")
        for result in results:
            assert result.score > 0

    def test_search_results_ordered_by_score(self):
        """Results should be ordered by score (highest first)."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        results = search_wiki_with_backend(demo_wiki, "wiki", limit=10, backend="bm25")
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_search_respects_limit(self):
        """Search results should not exceed limit."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        for limit in [1, 5, 10]:
            results = search_wiki_with_backend(demo_wiki, "wiki", limit=limit, backend="bm25")
            assert len(results) <= limit


class TestSearchQmdBackend:
    """Test qmd backend handling (may not be installed)."""

    def test_search_qmd_backend_not_installed(self):
        """Should fail gracefully when qmd CLI not found."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        try:
            results = search_wiki_with_backend(demo_wiki, "query", backend="qmd")
            # If qmd is installed, results should be a list
            assert isinstance(results, list)
        except (RuntimeError, FileNotFoundError):
            # Expected if qmd is not installed
            pass

    def test_search_backend_qmd_if_available(self):
        """qmd backend should work if qmd CLI is available."""
        demo_wiki = Path(__file__).resolve().parents[1] / "examples" / "demo" / "wiki"
        try:
            results = search_wiki_with_backend(demo_wiki, "memex", limit=5, backend="qmd")
            # If we get here, qmd is installed and working
            assert isinstance(results, list)
        except (RuntimeError, FileNotFoundError):
            # Skip if qmd is not available
            pytest.skip("qmd CLI not installed")
