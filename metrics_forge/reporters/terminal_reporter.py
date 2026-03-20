"""Rich terminal reporter for metrics-forge."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..models import ForgeOutput, AlertSeverity, ValidationResult

console = Console()


def print_forge_output(output: ForgeOutput) -> None:
    """Print generation summary."""
    console.print()
    header = Text()
    header.append("Metrics Forge Output\n", style="bold")
    header.append(f"Services: ", style="dim")
    header.append(f"{output.services_processed}\n", style="bold")
    header.append(f"Alert Groups: ", style="dim")
    header.append(f"{len(output.alert_groups)}\n", style="bold")
    header.append(f"Total Rules: ", style="dim")
    header.append(f"{output.total_rules}\n", style="bold cyan")
    header.append(f"Dashboards: ", style="dim")
    header.append(f"{len(output.dashboards)}\n", style="bold")
    header.append(f"Total Panels: ", style="dim")
    header.append(f"{output.total_panels}", style="bold cyan")

    console.print(Panel(header, title="[bold]metrics-forge[/bold]", border_style="blue"))

    # Rules table
    if output.alert_groups:
        table = Table(title="Generated Alert Rules", show_lines=True)
        table.add_column("Group", style="cyan")
        table.add_column("Rules", justify="right")
        table.add_column("Alert Names")

        for group in output.alert_groups:
            names = ", ".join(r.name for r in group.rules[:3])
            if len(group.rules) > 3:
                names += f" (+{len(group.rules)-3} more)"
            table.add_row(group.name, str(group.rule_count), names)

        console.print(table)


def print_validation_report(result: ValidationResult) -> None:
    """Print validation results."""
    console.print()
    status = "[green]✓ PASSED[/green]" if result.passed else "[red]✗ FAILED[/red]"
    console.print(Panel(
        f"Validation: {status}\n"
        f"Rules Checked: {result.rules_checked}\n"
        f"[red]Errors: {result.error_count}[/red]  "
        f"[yellow]Warnings: {result.warning_count}[/yellow]",
        title="[bold]Validation Report[/bold]",
        border_style="red" if not result.passed else "green",
    ))

    if not result.issues:
        console.print("[green]No issues found![/green]")
        return

    table = Table(title="Issues", show_lines=True)
    table.add_column("Rule", style="bold", width=10)
    table.add_column("Severity", width=10)
    table.add_column("Message")
    table.add_column("Service", style="cyan")

    for issue in result.issues:
        color = {"critical": "red", "warning": "yellow", "info": "blue"}.get(issue.severity.value, "white")
        table.add_row(
            issue.rule_id,
            f"[{color}]{issue.severity.value.upper()}[/{color}]",
            issue.message,
            issue.service,
        )

    console.print(table)
