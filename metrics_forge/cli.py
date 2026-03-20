"""CLI entry point for metrics-forge."""

import json
import click
from rich.console import Console

from .parser import parse_service_definitions
from .analyzers.rule_generator import generate_rules
from .analyzers.dashboard_generator import generate_dashboards
from .analyzers.rule_validator import validate_rules, VALIDATION_RULES
from .reporters.terminal_reporter import print_forge_output, print_validation_report
from .reporters.export_reporter import export_prometheus_rules, export_grafana_dashboards, export_json_report
from .demo import create_demo_project

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="metrics-forge")
def main():
    """Generate Prometheus alerting rules and Grafana dashboards from service definitions."""
    pass


@main.command()
@click.argument("services_file")
@click.option("--output", "-o", default=None, help="Output YAML file for Prometheus rules")
@click.option("--dashboard-dir", "-d", default=None, help="Output directory for Grafana dashboards")
@click.option("--format", "fmt", type=click.Choice(["terminal", "json"]), default="terminal")
def generate(services_file, output, dashboard_dir, fmt):
    """Generate alerting rules and dashboards from service definitions."""
    services = parse_service_definitions(services_file)
    if not services:
        console.print("[yellow]No services found.[/yellow]")
        return

    forge_output = generate_rules(services)
    dashboards = generate_dashboards(services)
    forge_output.dashboards = dashboards

    if fmt == "json":
        if output:
            path = export_json_report(forge_output, output)
            console.print(f"[green]✓[/green] Exported JSON report: {path}")
        else:
            click.echo(json.dumps({"total_rules": forge_output.total_rules, "total_panels": forge_output.total_panels}, indent=2))
    else:
        print_forge_output(forge_output)

    if output and fmt != "json":
        path = export_prometheus_rules(forge_output, output)
        console.print(f"[green]✓[/green] Exported Prometheus rules: {path}")

    if dashboard_dir:
        paths = export_grafana_dashboards(dashboards, dashboard_dir)
        console.print(f"[green]✓[/green] Exported {len(paths)} Grafana dashboards to: {dashboard_dir}")


@main.command()
@click.argument("services_file")
@click.option("--fail-on", type=click.Choice(["critical", "warning"]), default=None)
def validate(services_file, fail_on):
    """Validate generated rules against best practices."""
    services = parse_service_definitions(services_file)
    forge_output = generate_rules(services)
    result = validate_rules(forge_output.alert_groups)
    print_validation_report(result)

    if fail_on:
        from .models import AlertSeverity
        severity_map = {"critical": AlertSeverity.CRITICAL, "warning": AlertSeverity.WARNING}
        threshold = severity_map[fail_on]
        levels = [AlertSeverity.CRITICAL]
        if threshold == AlertSeverity.WARNING:
            levels.append(AlertSeverity.WARNING)
        has_issues = any(i.severity in levels for i in result.issues)
        if has_issues:
            raise SystemExit(1)


@main.command()
@click.option("--output-dir", "-o", default="demo-metrics", help="Output directory")
def demo(output_dir):
    """Generate demo service definitions."""
    path = create_demo_project(output_dir)
    console.print(f"[green]✓[/green] Created demo project: [bold]{path}[/bold]")
    console.print("\nTry these commands:")
    console.print(f"  metrics-forge generate {path}/services.yaml")
    console.print(f"  metrics-forge generate {path}/services.yaml -o rules.yaml -d dashboards/")
    console.print(f"  metrics-forge validate {path}/services.yaml")


@main.command()
def rules():
    """List all validation rules."""
    from rich.table import Table
    table = Table(title="Validation Rules", show_lines=True)
    table.add_column("Rule ID", style="bold")
    table.add_column("Severity")
    table.add_column("Description")

    for rule_id, info in VALIDATION_RULES.items():
        color = {"critical": "red", "warning": "yellow", "info": "blue"}.get(info["severity"].value, "white")
        table.add_row(rule_id, f"[{color}]{info['severity'].value.upper()}[/{color}]", info["message"])

    console.print(table)
