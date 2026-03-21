"""CLI entry point for metrics-forge."""

import json

import click
from rich.console import Console

from .analyzers.dashboard_generator import generate_dashboards
from .analyzers.rule_generator import generate_rules
from .analyzers.rule_validator import VALIDATION_RULES, validate_rules
from .demo import create_demo_project
from .parser import parse_existing_rules, parse_service_definitions
from .reporters.export_reporter import export_grafana_dashboards, export_json_report, export_prometheus_rules
from .reporters.terminal_reporter import print_forge_output, print_validation_report

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
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--type", "gen_type", type=click.Choice(["alerts", "dashboards", "all"]),
              default="all", help="What to generate")
def generate(services_file, output, dashboard_dir, fmt, gen_type):
    """Generate alerting rules and dashboards from service definitions."""
    services = parse_service_definitions(services_file)
    if not services:
        console.print("[yellow]No services found.[/yellow]")
        return

    forge_output = None
    dashboards = []

    # Generate based on type
    if gen_type in ("alerts", "all"):
        forge_output = generate_rules(services)
    else:
        from .models import ForgeOutput
        forge_output = ForgeOutput(services_processed=len(services))

    if gen_type in ("dashboards", "all"):
        dashboards = generate_dashboards(services)
        forge_output.dashboards = dashboards

    if fmt == "json":
        if output:
            path = export_json_report(forge_output, output)
            console.print(f"[green]✓[/green] Exported JSON report: {path}")
        else:
            result = {"total_rules": forge_output.total_rules, "total_panels": forge_output.total_panels}
            click.echo(json.dumps(result, indent=2))
    else:
        print_forge_output(forge_output)

    if output and fmt != "json" and gen_type in ("alerts", "all"):
        path = export_prometheus_rules(forge_output, output)
        console.print(f"[green]✓[/green] Exported Prometheus rules: {path}")

    if dashboard_dir and gen_type in ("dashboards", "all"):
        paths = export_grafana_dashboards(dashboards, dashboard_dir)
        console.print(f"[green]✓[/green] Exported {len(paths)} Grafana dashboards to: {dashboard_dir}")


@main.command()
@click.argument("services_file")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--fail-on", type=click.Choice(["critical", "warning"]), default=None)
def validate(services_file, fmt, fail_on):
    """Validate generated rules against best practices."""
    services = parse_service_definitions(services_file)
    forge_output = generate_rules(services)
    result = validate_rules(forge_output.alert_groups)

    if fmt == "json":
        output = {
            "passed": result.passed,
            "rules_checked": result.rules_checked,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "issues": [
                {"rule_id": i.rule_id, "message": i.message, "severity": i.severity.value, "service": i.service}
                for i in result.issues
            ],
        }
        click.echo(json.dumps(output, indent=2))
    else:
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


@main.command()
@click.argument("services_file")
@click.argument("existing_rules_file")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def diff(services_file, existing_rules_file, fmt):
    """Compare generated rules with existing Prometheus rules."""
    services = parse_service_definitions(services_file)
    if not services:
        console.print("[yellow]No services found.[/yellow]")
        return

    forge_output = generate_rules(services)
    existing_groups = parse_existing_rules(existing_rules_file)

    # Extract alert names from both
    generated_names = set()
    for group in forge_output.alert_groups:
        for rule in group.rules:
            generated_names.add(rule.name)

    existing_names = set()
    for group in existing_groups:
        for rule in group.get("rules", []):
            if "alert" in rule:
                existing_names.add(rule["alert"])

    new_rules = generated_names - existing_names
    removed_rules = existing_names - generated_names
    common_rules = generated_names & existing_names

    if fmt == "json":
        output = {
            "new_rules": sorted(list(new_rules)),
            "removed_rules": sorted(list(removed_rules)),
            "common_rules": sorted(list(common_rules)),
            "generated_count": len(generated_names),
            "existing_count": len(existing_names),
        }
        click.echo(json.dumps(output, indent=2))
    else:
        console.print()
        console.print(f"[bold]Generated rules:[/bold] {len(generated_names)}")
        console.print(f"[bold]Existing rules:[/bold] {len(existing_names)}")
        console.print()

        if new_rules:
            console.print(f"[green]New rules ({len(new_rules)}):[/green]")
            for name in sorted(new_rules):
                console.print(f"  + {name}")

        if removed_rules:
            console.print(f"\n[red]Removed rules ({len(removed_rules)}):[/red]")
            for name in sorted(removed_rules):
                console.print(f"  - {name}")

        if not new_rules and not removed_rules:
            console.print("[green]✓ Rules are in sync![/green]")
