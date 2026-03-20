"""Tests for CLI commands."""

from click.testing import CliRunner
from metrics_forge.cli import main

runner = CliRunner()


class TestGenerateCommand:
    def test_generate(self, demo_dir):
        result = runner.invoke(main, ["generate", f"{demo_dir}/services.yaml"])
        assert result.exit_code == 0

    def test_generate_with_output(self, demo_dir, tmp_path):
        out = str(tmp_path / "rules.yaml")
        result = runner.invoke(main, ["generate", f"{demo_dir}/services.yaml", "-o", out])
        assert result.exit_code == 0
        assert "Exported" in result.output

    def test_generate_with_dashboards(self, demo_dir, tmp_path):
        out = str(tmp_path / "dashboards")
        result = runner.invoke(main, ["generate", f"{demo_dir}/services.yaml", "-d", out])
        assert result.exit_code == 0

    def test_generate_json(self, demo_dir, tmp_path):
        out = str(tmp_path / "report.json")
        result = runner.invoke(main, ["generate", f"{demo_dir}/services.yaml", "--format", "json", "-o", out])
        assert result.exit_code == 0


class TestValidateCommand:
    def test_validate(self, demo_dir):
        result = runner.invoke(main, ["validate", f"{demo_dir}/services.yaml"])
        assert result.exit_code == 0

    def test_validate_fail_on(self, demo_dir):
        result = runner.invoke(main, ["validate", f"{demo_dir}/services.yaml", "--fail-on", "warning"])
        assert result.exit_code in (0, 1)


class TestDemoCommand:
    def test_demo(self, tmp_path):
        out = str(tmp_path / "test-demo")
        result = runner.invoke(main, ["demo", "-o", out])
        assert result.exit_code == 0
        assert "Created" in result.output


class TestRulesCommand:
    def test_rules(self):
        result = runner.invoke(main, ["rules"])
        assert result.exit_code == 0
        assert "MET-001" in result.output
        assert "MET-010" in result.output


class TestVersion:
    def test_version(self):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output


class TestParser:
    def test_parse_services(self, demo_dir):
        from metrics_forge.parser import parse_service_definitions
        services = parse_service_definitions(f"{demo_dir}/services.yaml")
        assert len(services) >= 3

    def test_parse_nonexistent(self):
        from metrics_forge.parser import parse_service_definitions
        assert parse_service_definitions("/nonexistent.yaml") == []
