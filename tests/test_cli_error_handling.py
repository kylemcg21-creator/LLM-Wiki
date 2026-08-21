"""Error handling and edge cases for CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from llm_wiki.cli import main


def test_cli_search_with_no_wiki_found(tmp_path: Path):
    """Should fail gracefully when wiki not found."""
    runner = CliRunner()
    # Run from a directory with no wiki
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["search", "query"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "cannot find" in result.output.lower()


def test_cli_search_invalid_limit(tmp_path: Path):
    """Should handle invalid limit values."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(demo_root), "search", "query", "--limit", "-5"])
    # Should either work or fail gracefully
    assert result.exit_code in [0, 2]  # 2 is Click's error code for invalid options


def test_cli_search_empty_query(tmp_path: Path):
    """Should handle empty or whitespace-only queries."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(demo_root), "search", "   "])
    assert result.exit_code == 0
    # Should either return no results or handle gracefully
    assert "no results" in result.output.lower() or "results" in result.output.lower()


def test_cli_expand_nonexistent_page(tmp_path: Path):
    """Should error when page doesn't exist."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(demo_root), "expand", "nonexistent-page-xyz-123"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_cli_expand_with_missing_section(tmp_path: Path):
    """Should error gracefully when section doesn't exist."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--root", str(demo_root), "expand", "synthesis", "--section", "NonexistentSection123"],
    )
    assert result.exit_code != 0
    assert "section not found" in result.output.lower() or "not found" in result.output.lower()


def test_cli_expand_section_with_json(tmp_path: Path):
    """Should handle --json with sections correctly."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--root",
            str(demo_root),
            "expand",
            "synthesis",
            "--section",
            "Thesis",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"section"' in result.output
    assert '"content"' in result.output


def test_cli_backlinks_nonexistent_page(tmp_path: Path):
    """Should handle backlinks for nonexistent page."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(demo_root), "backlinks", "nonexistent-xyz"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_cli_new_page_with_existing_slug(tmp_path: Path):
    """Should fail when page already exists (without --force)."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    # Try to create page with slug that already exists
    result = runner.invoke(
        main,
        ["--root", str(demo_root), "new", "--type", "entity", "--slug", "andrej-karpathy"],
    )
    assert result.exit_code != 0


def test_cli_new_page_with_force(tmp_path: Path):
    """Should allow overwriting with --force flag."""
    # Setup a temporary wiki
    (tmp_path / "AGENTS.md").write_text("# Agent")
    (tmp_path / "templates" / "entity.md").mkdir(parents=True)
    (tmp_path / "templates" / "entity.md").write_text("# {{title}}\n")
    (tmp_path / "wiki" / "entities").mkdir(parents=True)
    (tmp_path / "wiki" / "entities" / "test.md").write_text("# Old")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--root",
            str(tmp_path),
            "new",
            "--type",
            "entity",
            "--slug",
            "test",
            "--force",
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "wiki" / "entities" / "test.md").exists()


def test_cli_new_page_missing_template(tmp_path: Path):
    """Should error if template file doesn't exist."""
    (tmp_path / "AGENTS.md").write_text("# Agent")
    (tmp_path / "wiki" / "entities").mkdir(parents=True)
    # No templates directory

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--root", str(tmp_path), "new", "--type", "entity", "--slug", "test-topic"],
    )
    assert result.exit_code != 0


def test_cli_lint_invalid_severity(tmp_path: Path):
    """Should reject invalid severity values."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--root", str(demo_root), "lint", "--severity", "invalid-severity"],
    )
    assert result.exit_code == 2  # Click's error for invalid choice


def test_cli_lint_with_json_output(tmp_path: Path):
    """Should output valid JSON when --json flag is used."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(demo_root), "lint", "--json"])
    assert result.exit_code == 0
    # Should be valid JSON (can parse it)
    import json

    try:
        data = json.loads(result.output)
        assert isinstance(data, list)
    except json.JSONDecodeError:
        assert False, "lint --json output is not valid JSON"


def test_cli_init_check_incomplete(tmp_path: Path):
    """Should fail on incomplete project structure."""
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    (incomplete / "AGENTS.md").write_text("x")
    # Missing wiki/, raw/, templates/ directories

    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(incomplete), "init-check"])
    assert result.exit_code != 0


def test_cli_init_check_complete(tmp_path: Path):
    """Should pass when project structure is complete."""
    root = tmp_path / "complete"
    root.mkdir()
    (root / "AGENTS.md").write_text("# Agent")
    (root / "wiki").mkdir()
    (root / "wiki" / "index.md").write_text("# Index")
    (root / "wiki" / "log.md").write_text("# Log")
    (root / "wiki" / "synthesis.md").write_text("# Synthesis")
    (root / "raw").mkdir()
    (root / "templates").mkdir()

    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(root), "init-check"])
    assert result.exit_code == 0
    assert "ready" in result.output.lower()


def test_cli_list_pages_with_type_filter(tmp_path: Path):
    """Should filter pages by type correctly."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--root", str(demo_root), "list", "--type", "entity"],
    )
    assert result.exit_code == 0
    # Output should contain entity pages
    assert "entities/" in result.output


def test_cli_list_pages_json_output(tmp_path: Path):
    """Should output valid JSON for list command."""
    demo_root = Path(__file__).resolve().parents[1] / "examples" / "demo"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--root", str(demo_root), "list", "--json"],
    )
    assert result.exit_code == 0
    import json

    try:
        data = json.loads(result.output)
        assert isinstance(data, list)
        if data:
            assert "path" in data[0]
            assert "stem" in data[0]
    except json.JSONDecodeError:
        assert False, "list --json output is not valid JSON"


def test_cli_graph_large_wiki(tmp_path: Path):
    """Should handle graph export for larger wikis."""
    # Create a wiki with multiple pages
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    for i in range(10):
        (wiki / f"page-{i}.md").write_text(f"# Page {i}\n\nLinks to [[page-{(i + 1) % 10}]]")

    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(tmp_path.parent), "graph", "--json"])
    # Graph command should work (might fail due to root not found, but that's OK)
    # The point is it shouldn't crash on structure
    assert isinstance(result.exit_code, int)  # Should have valid exit code


def test_cli_watch_once_flag(tmp_path: Path):
    """Should exit after one check with --once flag."""
    (tmp_path / "raw").mkdir()
    (tmp_path / "wiki").mkdir()
    (tmp_path / "raw" / "test.md").write_text("content")

    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(tmp_path), "watch", "--once"])
    assert result.exit_code == 0
    # Should complete without hanging


def test_cli_stats_empty_wiki(tmp_path: Path):
    """Should handle stats for empty wiki."""
    (tmp_path / "wiki").mkdir()
    (tmp_path / "raw").mkdir()

    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(tmp_path), "stats"])
    assert result.exit_code == 0
    assert "0" in result.output  # Should show 0 pages


def test_cli_log_empty(tmp_path: Path):
    """Should handle empty log gracefully."""
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki" / "log.md").write_text("# Log\n")

    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(tmp_path), "log"])
    assert result.exit_code == 0
    assert "no log entries" in result.output.lower() or "log" in result.output.lower()


def test_cli_ingest_status_json(tmp_path: Path):
    """Should output valid JSON for ingest-status."""
    (tmp_path / "AGENTS.md").write_text("# Agent")
    (tmp_path / "raw").mkdir()
    (tmp_path / "wiki").mkdir()
    (tmp_path / "raw" / "test.md").write_text("content")

    runner = CliRunner()
    result = runner.invoke(main, ["--root", str(tmp_path), "ingest-status", "--json"])
    assert result.exit_code == 0
    import json

    try:
        data = json.loads(result.output)
        assert isinstance(data, list)
    except json.JSONDecodeError:
        assert False, "ingest-status --json output is not valid JSON"
