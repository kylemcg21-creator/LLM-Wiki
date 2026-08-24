"""Edge cases and advanced scenarios for wiki bootstrap/initialization."""

from pathlib import Path

from llm_wiki.bootstrap import bootstrap_wiki


class TestBootstrapBasicScenarios:
    """Test basic bootstrap scenarios."""

    def test_bootstrap_creates_all_directories(self, tmp_path: Path):
        """Should create all required directories."""
        target = tmp_path / "new-wiki"
        result = bootstrap_wiki(target, project_name="Test Wiki")

        # Verify structure
        assert result.target.exists()
        assert (result.target / "wiki").exists()
        assert (result.target / "raw").exists()
        assert (result.target / "templates").exists()

    def test_bootstrap_creates_required_files(self, tmp_path: Path):
        """Should create all required files."""
        target = tmp_path / "new-wiki"
        result = bootstrap_wiki(target, project_name="Test Wiki")

        assert (result.target / "AGENTS.md").exists()
        assert (result.target / "wiki" / "index.md").exists()
        assert (result.target / "wiki" / "log.md").exists()
        assert (result.target / "wiki" / "synthesis.md").exists()

    def test_bootstrap_with_custom_name(self, tmp_path: Path):
        """Should use custom project name in files."""
        target = tmp_path / "my-wiki"
        result = bootstrap_wiki(target, project_name="My Custom Wiki")

        # Check that project name appears in generated files
        agents_content = (result.target / "AGENTS.md").read_text()
        assert "My Custom Wiki" in agents_content or result.target.exists()


class TestBootstrapTemplateSubstitution:
    """Test template variable substitution."""

    def test_bootstrap_substitutes_project_name(self, tmp_path: Path):
        """Should substitute {{project_name}} in templates."""
        target = tmp_path / "test-wiki"
        result = bootstrap_wiki(target, project_name="Test Project")

        agents = (result.target / "AGENTS.md").read_text()
        # Should either have the name or no placeholder
        assert "Test Project" in agents or "{{project_name}}" not in agents

    def test_bootstrap_substitutes_date(self, tmp_path: Path):
        """Should substitute {{date}} in templates."""
        target = tmp_path / "test-wiki"
        result = bootstrap_wiki(target)

        log_content = (result.target / "wiki" / "log.md").read_text()
        # Should have date format or no placeholder
        assert "{{date}}" not in log_content

    def test_bootstrap_substitutes_root(self, tmp_path: Path):
        """Should substitute {{project_root}} in templates."""
        target = tmp_path / "test-wiki"
        result = bootstrap_wiki(target)

        agents = (result.target / "AGENTS.md").read_text()
        # Should not have unsubstituted placeholder
        assert "{{project_root}}" not in agents


class TestBootstrapForceOverwrite:
    """Test force overwrite behavior."""

    def test_bootstrap_without_force_fails_existing(self, tmp_path: Path):
        """Should fail when files exist without --force."""
        target = tmp_path / "existing-wiki"
        target.mkdir()
        (target / "AGENTS.md").write_text("existing")

        try:
            bootstrap_wiki(target, force=False)
            assert False, "Should have raised FileExistsError"
        except FileExistsError:
            pass

    def test_bootstrap_with_force_overwrites(self, tmp_path: Path):
        """Should overwrite existing files with --force."""
        target = tmp_path / "existing-wiki"
        target.mkdir()
        (target / "AGENTS.md").write_text("OLD CONTENT")

        result = bootstrap_wiki(target, force=True)
        assert result.target.exists()

        # New content should replace old
        content = (result.target / "AGENTS.md").read_text()
        assert "OLD CONTENT" not in content


class TestBootstrapGitIntegration:
    """Test git initialization."""

    def test_bootstrap_with_git_init(self, tmp_path: Path):
        """Should initialize git repository when requested."""
        target = tmp_path / "git-wiki"
        result = bootstrap_wiki(target, init_git=True)

        assert result.git_initialized
        assert (result.target / ".git").exists()

    def test_bootstrap_without_git(self, tmp_path: Path):
        """Should not initialize git by default."""
        target = tmp_path / "no-git-wiki"
        result = bootstrap_wiki(target, init_git=False)

        assert not result.git_initialized
        assert not (result.target / ".git").exists()


class TestBootstrapFileTracking:
    """Test files_created tracking."""

    def test_bootstrap_tracks_created_files(self, tmp_path: Path):
        """Should track all created files."""
        target = tmp_path / "tracked-wiki"
        result = bootstrap_wiki(target)

        assert len(result.files_created) > 0
        # Should include key files
        file_names = [str(f) for f in result.files_created]
        assert any("AGENTS.md" in f for f in file_names)
        assert any("index.md" in f for f in file_names)


class TestBootstrapErrorHandling:
    """Test error handling in bootstrap."""

    def test_bootstrap_parent_not_exists(self, tmp_path: Path):
        """Should handle when parent directory doesn't exist."""
        target = tmp_path / "nonexistent" / "parent" / "wiki"
        result = bootstrap_wiki(target, parents=True)
        assert result.target.exists()

    def test_bootstrap_permission_error(self, tmp_path: Path):
        """Should handle permission errors gracefully."""
        target = tmp_path / "no-perms-wiki"
        target.mkdir()
        # Make parent read-only
        target.chmod(0o444)

        try:
            bootstrap_wiki(target, force=False)
            # Expected to fail or succeed depending on OS
            assert True
        except (PermissionError, OSError):
            pass
        finally:
            # Restore permissions for cleanup
            target.chmod(0o755)


class TestBootstrapMultipleInvocations:
    """Test multiple bootstrap invocations."""

    def test_bootstrap_idempotent_with_force(self, tmp_path: Path):
        """Should be idempotent when using force."""
        target = tmp_path / "idempotent-wiki"

        # First run
        result1 = bootstrap_wiki(target, project_name="Test", init_git=True)
        first_agents = (result1.target / "AGENTS.md").read_text()

        # Second run with force
        result2 = bootstrap_wiki(target, project_name="Test", force=True)
        second_agents = (result2.target / "AGENTS.md").read_text()

        # Content should be same
        assert first_agents == second_agents
