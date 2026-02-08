# Network Automator - Project Overview

## Project Purpose
A Python-based network automation tool inspired by Terraform workflows, designed for configuration management of network devices using Netmiko and Jinja2 templates.

## Architecture

### Core Components
- **Modern CLI Interface**: Typer-powered commands with Rich formatting (`plan`, `apply`, `check`, `list`, `templates`)
- **Dynamic Template Discovery**: Automatic discovery of Jinja2 templates with metadata
- **Multi-Vendor Driver System**: Specialized drivers for different network device types
- **Configuration Rendering**: Jinja2-based template engine with device-specific data
- **Inventory Management**: YAML-based device definitions with flexible configuration

### Key Features
- **Infrastructure as Code**: Template-driven configuration management
- **Safety First**: Plan before apply workflow with confirmation prompts
- **Dynamic Discovery**: Templates are discovered automatically from filesystem
- **Metadata-Driven**: Templates include safety and description metadata
- **Multi-Driver**: Support for different device behaviors (commit vs no-commit)
- **Professional CLI**: Modern Typer+Rich interface with beautiful terminal output

### CLI Command
The tool is accessed via the `nacli` command, providing a professional interface for network automation tasks.

## Supported Vendors
- **Huawei VRP 5.x** (`huawei_vrp5`): No commit required
- **Huawei VRP 8.x** (`huawei_vrp8`): Requires commit for configuration persistence
- **MikroTik RouterOS 7.x** (`routeros7`): Standard RouterOS commands

## Workflow
1. **Discovery**: `nacli list` - Show available devices
2. **Planning**: `nacli plan [device]` - Preview configuration changes
3. **Application**: `nacli apply [device]` - Apply configurations with confirmation
4. **Validation**: Built-in SSH connectivity testing and template validation

## Technology Stack
- **Python 3.8+**: Core runtime
- **Typer**: Modern CLI framework
- **Rich**: Beautiful terminal output and formatting
- **Netmiko**: SSH connection management and device interaction
- **Jinja2**: Template rendering engine
- **PyYAML**: Configuration file parsing

## Project Status
Production-ready tool with comprehensive error handling, logging, and validation systems.