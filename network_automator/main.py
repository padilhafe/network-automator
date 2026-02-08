#!/usr/bin/env python3
"""
Network Automator - Network Device Configuration Management
Modern CLI powered by Typer and Rich
"""

import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from jinja2 import Environment, TemplateSyntaxError
from netmiko import ConnectHandler
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

from .drivers import huawei_vrp5, huawei_vrp8, routeros7
from .render import render_template
from .template_discovery import TemplateDiscovery
from .utils import get_connection_params

# Initialize Typer app and Rich console
app = typer.Typer(
    name="nacli",
    help="Network Automator - Professional Network Device Configuration Management",
    add_completion=False,
)

console = Console()

# Driver mapping
DRIVERS = {
    "huawei_vrp5": huawei_vrp5,
    "huawei_vrp8": huawei_vrp8,
    "routeros7": routeros7,
}

# Initialize template discovery
template_discovery = TemplateDiscovery()


def load_inventory(path: str = "inventory/devices.yml") -> List[dict]:
    """Load device inventory from YAML file"""
    import os
    from pathlib import Path

    # If path is relative, make it relative to the project root (parent of network_automator)
    if not os.path.isabs(path):
        project_root = Path(__file__).parent.parent
        full_path = project_root / path
    else:
        full_path = Path(path)

    try:
        with open(full_path) as f:
            return yaml.safe_load(f)["devices"]
    except FileNotFoundError:
        console.print(f"[red]Error: Inventory file not found: {full_path}[/red]")
        raise typer.Exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing YAML file: {e}[/red]")
        raise typer.Exit(1)


def print_device_header(device: dict, index: int, total: int):
    """Print formatted device header"""
    panel_title = f"Device {index}/{total}: {device['name']}"
    content = f"""[bold]Host:[/bold] {device["host"]}
[bold]Vendor:[/bold] {device["vendor"]}
[bold]Device Type:[/bold] {device["device_type"]}
[bold]Template:[/bold] {device.get("template", "default.j2")}"""

    console.print(Panel(content, title=panel_title, border_style="blue"))


def check_ssh(device: dict) -> tuple[bool, str]:
    """Test SSH connectivity to device"""
    start_time = time.time()

    with console.status(
        f"[yellow]Testing SSH connectivity to {device['name']}...", spinner="dots"
    ):
        try:
            conn_params = get_connection_params(device)
            with ConnectHandler(**conn_params) as conn:
                prompt = conn.find_prompt()

            elapsed = time.time() - start_time
            return True, f"SSH OK - Prompt: {prompt.strip()} ({elapsed:.2f}s)"
        except Exception as e:
            elapsed = time.time() - start_time
            return False, f"SSH FAILED: {str(e)} ({elapsed:.2f}s)"


def apply_config(
    device: dict, template_override: Optional[str] = None, dry_run: bool = False
) -> str:
    """Apply or plan configuration with detailed feedback"""
    action_text = "Planning" if dry_run else "Applying"

    with console.status(
        f"[yellow]{action_text} configuration for {device['name']}...", spinner="dots"
    ):
        # Determine template using priority order
        vendor = device["vendor"]
        template_info = None

        if template_override:
            template_name = template_override
            template_info = template_discovery.find_template(vendor, template_name)
            if template_info:
                console.print(
                    f"   [green]Using specified template:[/green] {template_name}"
                )
                if template_info.changes_hostname:
                    console.print(
                        f"   [yellow]WARNING: Template changes hostname[/yellow]"
                    )
            else:
                console.print(
                    f"   [red]ERROR: Template '{template_name}' not found for vendor '{vendor}'[/red]"
                )
                return "ERROR: Template not found"
        elif device.get("template"):
            template_name = device.get("template").replace(".j2", "")
            template_info = template_discovery.find_template(vendor, template_name)
            if template_info:
                console.print(
                    f"   [green]Using inventory template:[/green] {template_name}"
                )
                if template_info.changes_hostname:
                    console.print(
                        f"   [yellow]WARNING: Template changes hostname[/yellow]"
                    )
            else:
                console.print(
                    f"   [red]ERROR: Template '{template_name}' not found for vendor '{vendor}'[/red]"
                )
                return "ERROR: Template not found"
        else:
            template_info = template_discovery.get_fallback_template(vendor)
            if template_info:
                template_name = template_info.name
                console.print(
                    f"   [green]Using fallback template:[/green] {template_name}"
                )
            else:
                console.print(
                    f"   [red]ERROR: No default template found for vendor '{vendor}'[/red]"
                )
                return "ERROR: No default template found"

        # Render template
        template_file = f"{template_name}.j2"
        config_text = render_template(
            vendor=vendor,
            template_name=template_file,
            dados={
                "hostname": device["name"],
                "interfaces": device.get("interfaces", []),
            },
        )

        config_set = [line.strip() for line in config_text.splitlines() if line.strip()]

    # Display configuration plan
    plan_table = Table(title="Configuration Plan")
    plan_table.add_column("Property", style="cyan")
    plan_table.add_column("Value", style="white")

    plan_table.add_row("Device", device["name"])
    plan_table.add_row("Template", template_name)
    if template_info:
        plan_table.add_row("Description", template_info.description or "No description")
        plan_table.add_row("Safe", "Yes" if template_info.safe else "No")
    plan_table.add_row("Changes", f"{len(config_set)} configuration commands")
    plan_table.add_row("Driver", vendor)

    mode_color = "cyan" if dry_run else "green"
    mode_text = "PLAN (preview only)" if dry_run else "APPLY (will execute)"
    plan_table.add_row("Mode", f"[{mode_color}]{mode_text}[/{mode_color}]")

    console.print(plan_table)

    # Display configuration changes
    console.print(f"\n[bold]Configuration Changes:[/bold]")
    for i, line in enumerate(config_set, 1):
        prefix = "+" if not dry_run else " "
        color = "green" if not dry_run else "cyan"
        console.print(f"[{color}]  {prefix} {line}[/{color}]")

    # Check for hostname changes
    changes_hostname = (
        template_info.changes_hostname
        if template_info
        else any("sysname" in cmd for cmd in config_set)
    )

    if changes_hostname:
        console.print(
            Panel(
                "[yellow]Configuration changes hostname - may cause Netmiko issues\n"
                "Consider using a safer template[/yellow]",
                title="⚠️  WARNING",
                border_style="yellow",
            )
        )

    if dry_run:
        console.print(
            Panel(
                f"[cyan]This plan shows what would be applied to {device['name']}\n"
                f"Run 'apply' to execute these changes[/cyan]",
                title="📋 Plan Summary",
                border_style="cyan",
            )
        )
        return "PLAN: Configuration changes planned but not applied"

    # Execute configuration
    with console.status(
        f"[yellow]Executing configuration changes on {device['name']}...",
        spinner="dots",
    ):
        start_time = time.time()
        conn_params = get_connection_params(device)

        with ConnectHandler(**conn_params) as conn:
            output = DRIVERS[device["vendor"]].send_config(conn, config_set)

        elapsed = time.time() - start_time

    console.print(
        f"[green]Configuration applied successfully! ({elapsed:.2f}s)[/green]"
    )
    return output


def print_summary(results: List[dict], action: str):
    """Print operation summary"""
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)

    summary_table = Table(title=f"{action.upper()} SUMMARY")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", justify="right")

    if action == "plan":
        summary_table.add_row("Devices planned", str(total_count))
        summary_table.add_row("Plan successful", f"[green]{success_count}[/green]")
        summary_table.add_row(
            "Plan failed", f"[red]{total_count - success_count}[/red]"
        )
    else:
        summary_table.add_row("Devices targeted", str(total_count))
        summary_table.add_row("Successfully applied", f"[green]{success_count}[/green]")
        summary_table.add_row(
            "Failed to apply", f"[red]{total_count - success_count}[/red]"
        )

    console.print(summary_table)

    # Show failed devices
    if success_count < total_count:
        console.print(f"\n[bold red]Failed devices:[/bold red]")
        for result in results:
            if not result["success"]:
                console.print(f"  [red]{result['device']}: {result['error']}[/red]")


@app.command()
def list_devices():
    """List all available devices from inventory"""
    devices = load_inventory()

    table = Table(title="Available Devices")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Vendor", style="magenta")
    table.add_column("Host", style="yellow")
    table.add_column("Type", style="green")

    for device in devices:
        table.add_row(
            device["name"], device["vendor"], device["host"], device["device_type"]
        )

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(devices)} devices")


@app.command("list")
def list_devices_alias():
    """Alias for list-devices command"""
    list_devices()


@app.command()
def templates(
    vendor: Optional[str] = typer.Argument(
        None, help="Show templates for specific vendor only"
    ),
):
    """List all available configuration templates"""
    all_templates = template_discovery.discover_all_templates()

    if not all_templates:
        console.print("[red]No templates found[/red]")
        return

    # Filter by vendor if specified
    if vendor:
        if vendor not in all_templates:
            console.print(f"[red]Vendor '{vendor}' not found[/red]")
            console.print(
                f"[yellow]Available vendors:[/yellow] {', '.join(all_templates.keys())}"
            )
            return
        filtered_templates = {vendor: all_templates[vendor]}
    else:
        filtered_templates = all_templates

    table = Table(title="Available Templates")
    table.add_column("Vendor", style="magenta")
    table.add_column("Template", style="cyan")
    table.add_column("Safe", justify="center")
    table.add_column("Description", style="white")

    for vendor_name, templates in sorted(filtered_templates.items()):
        for i, template in enumerate(templates):
            vendor_display = vendor_name if i == 0 else ""
            safe_style = "green" if template.safe else "yellow"
            safe_text = "✓" if template.safe else "⚠"
            description = template.description or "No description"

            table.add_row(
                vendor_display,
                template.name,
                f"[{safe_style}]{safe_text}[/{safe_style}]",
                description,
            )

    console.print(table)

    # Show template priority info
    console.print(
        Panel(
            "[bold]Template Priority Order:[/bold]\n"
            "1. --template <name>     (command line override)\n"
            "2. template in YAML      (device inventory)\n"
            "3. default               (automatic fallback)",
            title="ℹ️  Template Priority",
            border_style="blue",
        )
    )

    # Show summary
    summary = template_discovery.get_template_summary()
    if summary:
        summary_table = Table(title="Template Summary")
        summary_table.add_column("Vendor", style="magenta")
        summary_table.add_column("Total", justify="right")
        summary_table.add_column("Safe", justify="right", style="green")
        summary_table.add_column("Unsafe", justify="right", style="yellow")

        for vendor_name, stats in summary.items():
            summary_table.add_row(
                vendor_name,
                str(stats["total"]),
                str(stats["safe"]),
                str(stats["unsafe"]),
            )

        console.print(summary_table)


@app.command()
def check(
    device_name: Optional[str] = typer.Argument(
        None, help="Specific device name to check"
    ),
):
    """Test SSH connectivity to devices"""
    devices = load_inventory()

    # Filter devices if specific name provided
    if device_name:
        devices = [d for d in devices if d["name"] == device_name]
        if not devices:
            console.print(f"[red]Device '{device_name}' not found![/red]")
            console.print(f"[yellow]Available devices:[/yellow]")
            all_devices = load_inventory()
            for device in all_devices:
                console.print(f"  [cyan]{device['name']}[/cyan] ({device['vendor']})")
            raise typer.Exit(1)

    # Show operation header
    console.print(
        Panel(
            f"[bold]SSH Connectivity Check[/bold]\n"
            f"Devices: {len(devices)}\n"
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="🔍 Network Automator",
            border_style="blue",
        )
    )

    results = []
    total_start_time = time.time()

    for i, device in enumerate(devices, 1):
        print_device_header(device, i, len(devices))

        result = {"device": device["name"], "success": False, "error": None}

        ok, msg = check_ssh(device)
        result["success"] = ok

        if ok:
            console.print(f"[green]✓ SUCCESS: {msg}[/green]")
        else:
            result["error"] = msg
            console.print(f"[red]✗ FAILED: {msg}[/red]")

        results.append(result)

    # Show summary
    total_elapsed = time.time() - total_start_time
    print_summary(results, "check")
    console.print(f"\n[bold]Total time:[/bold] {total_elapsed:.2f}s")
    console.print(
        f"[bold]Finished:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


@app.command()
def plan(
    device_name: Optional[str] = typer.Argument(
        None, help="Specific device name to plan"
    ),
    template: Optional[str] = typer.Option(
        None, "--template", "-t", help="Specific template to use"
    ),
):
    """Show configuration changes that would be applied (dry-run)"""
    devices = load_inventory()

    # Filter devices if specific name provided
    if device_name:
        devices = [d for d in devices if d["name"] == device_name]
        if not devices:
            console.print(f"[red]Device '{device_name}' not found![/red]")
            raise typer.Exit(1)

    # Show operation header
    console.print(
        Panel(
            f"[bold]Configuration Planning[/bold]\n"
            f"Devices: {len(devices)}\n"
            f"Template: {template or 'auto-detect'}\n"
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="📋 Network Automator",
            border_style="cyan",
        )
    )

    results = []
    total_start_time = time.time()

    for i, device in enumerate(devices, 1):
        print_device_header(device, i, len(devices))

        result = {"device": device["name"], "success": False, "error": None}

        # Check SSH first
        ok, msg = check_ssh(device)
        if not ok:
            result["error"] = f"SSH: {msg}"
            console.print(f"[red]✗ SSH failed: {msg}[/red]")
        else:
            try:
                output = apply_config(device, template, dry_run=True)
                result["success"] = True
                console.print(f"[cyan]✓ Plan completed successfully[/cyan]")
            except Exception as e:
                result["error"] = f"Config: {str(e)}"
                console.print(f"[red]✗ Configuration error: {e}[/red]")

        results.append(result)

    # Show summary
    total_elapsed = time.time() - total_start_time
    print_summary(results, "plan")
    console.print(f"\n[bold]Total time:[/bold] {total_elapsed:.2f}s")
    console.print(
        f"[bold]Finished:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


@app.command()
def apply(
    device_name: Optional[str] = typer.Argument(
        None, help="Specific device name to configure"
    ),
    template: Optional[str] = typer.Option(
        None, "--template", "-t", help="Specific template to use"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Apply configuration changes to devices"""
    devices = load_inventory()

    # Filter devices if specific name provided
    if device_name:
        devices = [d for d in devices if d["name"] == device_name]
        if not devices:
            console.print(f"[red]Device '{device_name}' not found![/red]")
            raise typer.Exit(1)

    # Show operation header
    console.print(
        Panel(
            f"[bold]Configuration Application[/bold]\n"
            f"Devices: {len(devices)}\n"
            f"Template: {template or 'auto-detect'}\n"
            f"Force mode: {'Yes' if force else 'No'}\n"
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="⚙️  Network Automator",
            border_style="green",
        )
    )

    results = []
    total_start_time = time.time()

    for i, device in enumerate(devices, 1):
        print_device_header(device, i, len(devices))

        result = {"device": device["name"], "success": False, "error": None}

        # Check SSH first
        ok, msg = check_ssh(device)
        if not ok:
            result["error"] = f"SSH: {msg}"
            console.print(f"[red]✗ SSH failed: {msg}[/red]")
        else:
            try:
                # If not force mode, show plan and ask for confirmation
                if not force:
                    # Show plan first
                    console.print(f"\n[yellow]Showing configuration plan...[/yellow]")
                    plan_output = apply_config(device, template, dry_run=True)

                    # Ask for confirmation
                    if not Confirm.ask(
                        f"\nDo you want to apply these changes to {device['name']}?"
                    ):
                        console.print(f"[yellow]Apply cancelled by user[/yellow]")
                        result["success"] = True
                        results.append(result)
                        continue

                # Execute configuration
                output = apply_config(device, template, dry_run=False)
                result["success"] = True

                # Show device output if available
                if output.strip() and not output.startswith("PLAN:"):
                    console.print(
                        Panel(
                            output.strip(), title="Device Output", border_style="green"
                        )
                    )

                console.print(f"[green]✓ Configuration applied successfully[/green]")

            except KeyboardInterrupt:
                console.print(f"\n[yellow]Apply cancelled by user[/yellow]")
                result["success"] = True
                results.append(result)
                break
            except Exception as e:
                result["error"] = f"Config: {str(e)}"
                console.print(f"[red]✗ Configuration error: {e}[/red]")

        results.append(result)

    # Show summary
    total_elapsed = time.time() - total_start_time
    print_summary(results, "apply")
    console.print(f"\n[bold]Total time:[/bold] {total_elapsed:.2f}s")
    console.print(
        f"[bold]Finished:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


@app.command()
def version():
    """Show version information"""
    console.print(
        Panel(
            "[bold]Network Automator[/bold]\n"
            "Version: 1.0.0\n"
            "CLI: Typer + Rich\n"
            "Network: Netmiko\n"
            "Templates: Jinja2\n"
            "\n"
            "[dim]Professional Network Device Configuration Management[/dim]",
            title="📦 Version Info",
            border_style="blue",
        )
    )


@app.command()
def stats(
    all_info: bool = typer.Option(
        False, "--all", help="Show all information available"
    ),
    details: bool = typer.Option(
        False, "--details", help="Show detailed device information"
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate inventory consistency"
    ),
    network: bool = typer.Option(False, "--network", help="Show network information"),
):
    """Show inventory statistics and analysis"""
    devices = load_inventory()
    if not devices:
        console.print("[red]No devices found in inventory[/red]")
        raise typer.Exit(1)

    if all_info:
        show_basic_stats(devices)
        show_network_info(devices)
        validate_inventory(devices)
        show_device_details(devices)
    elif details:
        show_device_details(devices)
    elif validate:
        validate_inventory(devices)
    elif network:
        show_network_info(devices)
    else:
        show_basic_stats(devices)


def show_basic_stats(devices):
    """Show basic inventory statistics"""
    console.print(Panel("📊 Basic Statistics", style="blue"))

    table = Table(title="Device Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="white")

    table.add_row("Total Devices", str(len(devices)))

    # Count by vendor
    vendors = Counter(d["vendor"] for d in devices)
    for vendor, count in vendors.most_common():
        percentage = (count / len(devices)) * 100
        table.add_row(f"├─ {vendor}", f"{count} ({percentage:.1f}%)")

    console.print(table)

    # Device types table
    device_types = Counter(d["device_type"] for d in devices)
    if device_types:
        types_table = Table(title="Device Types")
        types_table.add_column("Type", style="magenta")
        types_table.add_column("Count", justify="right")
        types_table.add_column("Percentage", justify="right")

        for dev_type, count in device_types.most_common():
            percentage = (count / len(devices)) * 100
            types_table.add_row(dev_type, str(count), f"{percentage:.1f}%")

        console.print(types_table)


def show_network_info(devices):
    """Show network information"""
    console.print(Panel("🌐 Network Information", style="blue"))

    subnets = set()
    total_interfaces = 0

    for device in devices:
        interfaces = device.get("interfaces", [])
        total_interfaces += len(interfaces)

        for interface in interfaces:
            if "ip" in interface and "mask" in interface:
                ip_parts = interface["ip"].split(".")
                if len(ip_parts) >= 3:
                    subnet = f"{'.'.join(ip_parts[:3])}.0"
                    subnets.add(subnet)

    info_table = Table(title="Network Summary")
    info_table.add_column("Metric", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Total Interfaces", str(total_interfaces))
    info_table.add_row("Unique Subnets", str(len(subnets)))

    console.print(info_table)

    if subnets:
        subnets_table = Table(title="Discovered Subnets")
        subnets_table.add_column("Subnet", style="green")

        for subnet in sorted(subnets):
            subnets_table.add_row(f"{subnet}/24")

        console.print(subnets_table)


def show_device_details(devices):
    """Show detailed device information"""
    console.print(Panel("🔍 Device Details", style="blue"))

    for i, device in enumerate(devices, 1):
        device_info = f"""[bold]{device["name"]}[/bold]
[cyan]Host:[/cyan] {device["host"]}
[cyan]Vendor:[/cyan] {device["vendor"]}
[cyan]Type:[/cyan] {device["device_type"]}
[cyan]Template:[/cyan] {device.get("template", "default")}"""

        interfaces = device.get("interfaces", [])
        if interfaces:
            device_info += f"\n[cyan]Interfaces ({len(interfaces)}):[/cyan]"
            for iface in interfaces:
                ip_info = f"{iface.get('ip', 'N/A')}/{iface.get('mask', 'N/A')}"
                device_info += f"\n  • {iface['name']:<15} {ip_info}"
        else:
            device_info += "\n[yellow]⚠️  No interfaces configured[/yellow]"

        console.print(
            Panel(device_info, title=f"Device {i}/{len(devices)}", border_style="cyan")
        )


def validate_inventory(devices):
    """Validate inventory consistency"""
    console.print(Panel("✅ Inventory Validation", style="blue"))

    errors = []
    warnings = []

    required_fields = ["name", "host", "vendor", "device_type", "username", "password"]
    device_names = set()
    device_hosts = set()
    known_vendors = ["huawei_vrp5", "huawei_vrp8", "routeros7"]

    for i, device in enumerate(devices, 1):
        device_id = f"Device #{i} ({device.get('name', 'UNNAMED')})"

        # Check required fields
        for field in required_fields:
            if field not in device or not device[field]:
                errors.append(f"{device_id}: Missing required field '{field}'")

        # Check for duplicate names
        name = device.get("name")
        if name:
            if name in device_names:
                errors.append(f"{device_id}: Duplicate device name '{name}'")
            device_names.add(name)

        # Check for duplicate hosts
        host = device.get("host")
        if host:
            if host in device_hosts:
                warnings.append(f"{device_id}: Duplicate host '{host}'")
            device_hosts.add(host)

        # Check vendor
        vendor = device.get("vendor")
        if vendor and vendor not in known_vendors:
            warnings.append(f"{device_id}: Unknown vendor '{vendor}'")

        # Check interfaces
        interfaces = device.get("interfaces", [])
        interface_names = set()
        for iface in interfaces:
            iface_name = iface.get("name")
            if not iface_name:
                warnings.append(f"{device_id}: Interface without name")
            elif iface_name in interface_names:
                errors.append(f"{device_id}: Duplicate interface '{iface_name}'")
            else:
                interface_names.add(iface_name)

            if "ip" not in iface or not iface["ip"]:
                warnings.append(f"{device_id}: Interface '{iface_name}' missing IP")
            if "mask" not in iface or not iface["mask"]:
                warnings.append(f"{device_id}: Interface '{iface_name}' missing mask")

    # Show validation results
    validation_table = Table(title="Validation Results")
    validation_table.add_column("Category", style="cyan")
    validation_table.add_column("Count", justify="right")

    validation_table.add_row("Devices Analyzed", str(len(devices)))
    validation_table.add_row(
        "Errors", f"[red]{len(errors)}[/red]" if errors else "[green]0[/green]"
    )
    validation_table.add_row(
        "Warnings",
        f"[yellow]{len(warnings)}[/yellow]" if warnings else "[green]0[/green]",
    )

    console.print(validation_table)

    if errors:
        console.print("\n[bold red]Critical Errors:[/bold red]")
        for error in errors:
            console.print(f"  [red]• {error}[/red]")

    if warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  [yellow]• {warning}[/yellow]")

    if not errors and not warnings:
        console.print(
            "\n[bold green]🎉 Inventory is valid! No issues found.[/bold green]"
        )


@app.command()
def validate(
    vendor: Optional[str] = typer.Option(
        None, "--vendor", help="Validate specific vendor only"
    ),
    template_name: Optional[str] = typer.Option(
        None, "--template", help="Validate specific template"
    ),
):
    """Validate configuration templates"""
    validator = TemplateValidator()

    if template_name and vendor:
        success = validate_template_reference(validator, vendor, template_name)
        raise typer.Exit(0 if success else 1)
    elif vendor:
        validate_vendor_templates(validator, vendor)
    else:
        validate_all_templates(validator)


class TemplateValidator:
    """Validates templates for syntax, metadata, and best practices"""

    def __init__(self):
        self.env = Environment()

    def validate_template_syntax(self, template_path: str):
        """Validate Jinja2 template syntax"""
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.env.parse(content)
            return True, "Syntax valid"
        except TemplateSyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.message}"
        except Exception as e:
            return False, f"Error reading template: {str(e)}"

    def validate_template_metadata(self, template_info):
        """Validate template metadata completeness"""
        issues = []

        if not template_info.description:
            issues.append("Missing description in template metadata")
        elif len(template_info.description) < 10:
            issues.append("Description too short (less than 10 characters)")

        try:
            with open(template_info.path, "r", encoding="utf-8") as f:
                content = f.read()

            has_hostname_commands = any(
                keyword in content.lower()
                for keyword in ["sysname", "hostname", "identity"]
            )

            if has_hostname_commands and not template_info.changes_hostname:
                issues.append(
                    "Contains hostname commands but changes_hostname is false"
                )

            if not has_hostname_commands and template_info.changes_hostname:
                issues.append(
                    "Marked as changing hostname but no hostname commands found"
                )

        except Exception as e:
            issues.append(f"Could not analyze template content: {str(e)}")

        return issues


def validate_template_reference(validator, vendor: str, template_name: str):
    """Validate a specific template reference"""
    template_info = template_discovery.find_template(vendor, template_name)

    if not template_info:
        console.print(
            f"[red]Template '{template_name}' not found for vendor '{vendor}'[/red]"
        )
        return False

    syntax_valid, syntax_msg = validator.validate_template_syntax(template_info.path)
    metadata_issues = validator.validate_template_metadata(template_info)

    if syntax_valid and not metadata_issues:
        console.print(f"[green]✓ Template '{template_name}' is valid[/green]")
        return True
    else:
        console.print(f"[red]✗ Template '{template_name}' has validation issues:[/red]")
        if not syntax_valid:
            console.print(f"  [red]ERROR: {syntax_msg}[/red]")
        for issue in metadata_issues:
            console.print(f"  [yellow]WARN: {issue}[/yellow]")
        return False


def validate_vendor_templates(validator, vendor: str):
    """Validate templates for specific vendor"""
    all_templates = template_discovery.discover_all_templates()

    if vendor not in all_templates:
        console.print(f"[red]Vendor '{vendor}' not found[/red]")
        console.print(f"Available vendors: {', '.join(all_templates.keys())}")
        raise typer.Exit(1)

    validate_templates_list(validator, {vendor: all_templates[vendor]})


def validate_all_templates(validator):
    """Validate all discovered templates"""
    all_templates = template_discovery.discover_all_templates()
    validate_templates_list(validator, all_templates)


def validate_templates_list(validator, templates_dict):
    """Validate a list of templates and show results"""
    console.print(Panel("🔍 Template Validation", style="blue"))

    total_templates = 0
    total_valid = 0

    for vendor, templates in templates_dict.items():
        vendor_table = Table(title=f"{vendor} Templates")
        vendor_table.add_column("Template", style="cyan")
        vendor_table.add_column("Status", justify="center")
        vendor_table.add_column("Issues", style="yellow")

        for template_info in templates:
            total_templates += 1

            syntax_valid, syntax_msg = validator.validate_template_syntax(
                template_info.path
            )
            metadata_issues = validator.validate_template_metadata(template_info)

            if syntax_valid and not metadata_issues:
                total_valid += 1
                status = "[green]✓ VALID[/green]"
                issues = "None"
            else:
                status = "[red]✗ INVALID[/red]"
                all_issues = []
                if not syntax_valid:
                    all_issues.append(syntax_msg)
                all_issues.extend(metadata_issues)
                issues = "; ".join(all_issues[:2])  # Limit to first 2 issues
                if len(all_issues) > 2:
                    issues += "..."

            vendor_table.add_row(template_info.name, status, issues)

        console.print(vendor_table)

    # Summary
    summary_table = Table(title="Validation Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", justify="right")

    summary_table.add_row("Total Templates", str(total_templates))
    summary_table.add_row("Valid Templates", f"[green]{total_valid}[/green]")
    summary_table.add_row(
        "Invalid Templates", f"[red]{total_templates - total_valid}[/red]"
    )

    console.print(summary_table)

    if total_valid == total_templates:
        console.print("\n[bold green]🎉 All templates passed validation![/bold green]")
    else:
        console.print("\n[yellow]Some templates have validation issues.[/yellow]")


@app.command()
def examples():
    """Show usage examples"""
    examples_text = """
[bold cyan]Basic Commands:[/bold cyan]
  [green]nacli list[/green]                                # List all available devices
  [green]nacli templates[/green]                           # List all available templates
  [green]nacli check[/green]                               # Test SSH connectivity to all devices
  [green]nacli version[/green]                             # Show version information
  [green]nacli stats[/green]                               # Show inventory statistics
  [green]nacli validate[/green]                            # Validate templates

[bold cyan]Device-Specific Operations:[/bold cyan]
  [green]nacli check huawei-ne40[/green]                   # Test SSH to specific device
  [green]nacli plan huawei-ne40[/green]                    # Show changes for specific device
  [green]nacli apply huawei-ne40[/green]                   # Apply to specific device

[bold cyan]Configuration Management:[/bold cyan]
  [green]nacli plan[/green]                                # Show configuration changes (all devices)
  [green]nacli apply[/green]                               # Apply configuration (with confirmation)
  [green]nacli apply --force[/green]                       # Apply without confirmation
  [green]nacli apply --template router_no_hostname[/green] # Use specific template

[bold cyan]Analysis & Validation:[/bold cyan]
  [green]nacli stats --all[/green]                         # Complete inventory analysis
  [green]nacli stats --validate[/green]                    # Validate inventory consistency
  [green]nacli validate --vendor huawei_vrp8[/green]       # Validate vendor templates
  [green]nacli validate --vendor huawei_vrp8 --template default[/green] # Validate specific template

[bold cyan]Workflow Example:[/bold cyan]
  1. [yellow]nacli list[/yellow]                           # Check available devices
  2. [yellow]nacli templates[/yellow]                      # Review available templates
  3. [yellow]nacli validate[/yellow]                       # Validate templates
  4. [yellow]nacli check[/yellow]                          # Test connectivity
  5. [yellow]nacli plan[/yellow]                           # Preview changes
  6. [yellow]nacli apply[/yellow]                          # Apply configurations

[dim]For more information, visit: https://github.com/padilhafe/network-automator[/dim]
    """

    console.print(
        Panel(
            examples_text.strip(),
            title="💡 Usage Examples",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()
