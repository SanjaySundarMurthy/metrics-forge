"""Tests for CLI commands."""

import json

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

    def test_generate_type_alerts(self, demo_dir, tmp_path):
        out = str(tmp_path / "rules.yaml")
        result = runner.invoke(main, ["generate", f"{demo_dir}/services.yaml", "--type", "alerts", "-o", out])
        assert result.exit_code == 0
        assert "Exported Prometheus rules" in result.output

    def test_generate_type_dashboards(self, demo_dir, tmp_path):
        out = str(tmp_path / "dashboards")
        result = runner.invoke(main, ["generate", f"{demo_dir}/services.yaml", "--type", "dashboards", "-d", out])
        assert result.exit_code == 0
        assert "Grafana dashboards" in result.output

    def test_generate_type_all(self, demo_dir, tmp_path):
        out = str(tmp_path / "rules.yaml")
        dash_dir = str(tmp_path / "dashboards")
        result = runner.invoke(main, [
            "generate", f"{demo_dir}/services.yaml",
            "--type", "all", "-o", out, "-d", dash_dir
        ])
        assert result.exit_code == 0


class TestValidateCommand:
    def test_validate(self, demo_dir):
        result = runner.invoke(main, ["validate", f"{demo_dir}/services.yaml"])
        assert result.exit_code == 0

    def test_validate_fail_on(self, demo_dir):
        result = runner.invoke(main, ["validate", f"{demo_dir}/services.yaml", "--fail-on", "warning"])
        assert result.exit_code in (0, 1)

    def test_validate_json_format(self, demo_dir):
        result = runner.invoke(main, ["validate", f"{demo_dir}/services.yaml", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "passed" in data
        assert "rules_checked" in data
        assert "issues" in data


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


class TestDiffCommand:
    def test_diff(self, demo_dir, tmp_path):
        # First generate rules to a file
        rules_file = str(tmp_path / "rules.yaml")
        runner.invoke(main, ["generate", f"{demo_dir}/services.yaml", "-o", rules_file])

        # Then diff against itself (should show no changes)
        result = runner.invoke(main, ["diff", f"{demo_dir}/services.yaml", rules_file])
        assert result.exit_code == 0

    def test_diff_json_format(self, demo_dir, tmp_path):
        rules_file = str(tmp_path / "rules.yaml")
        runner.invoke(main, ["generate", f"{demo_dir}/services.yaml", "-o", rules_file])

        result = runner.invoke(main, ["diff", f"{demo_dir}/services.yaml", rules_file, "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "new_rules" in data
        assert "removed_rules" in data
        assert "generated_count" in data


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


class TestCustomMetrics:
    def test_custom_metrics_rules(self):
        from metrics_forge.analyzers.rule_generator import generate_rules
        from metrics_forge.models import ServiceDefinition, ServiceTier

        svc = ServiceDefinition(
            name="test-service",
            tier=ServiceTier.STANDARD,
            namespace="test",
            custom_metrics=["cache_hit_ratio", "queue_depth"],
        )
        output = generate_rules([svc])
        rules = output.alert_groups[0].rules
        custom_rule_names = [r.name for r in rules if "cache_hit_ratio" in r.name or "queue_depth" in r.name]
        assert len(custom_rule_names) == 2
