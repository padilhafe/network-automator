# Network Automator - MCP Context Documentation

## Tool Identity and Purpose

### What is Network Automator?
A Python-based network device configuration management tool that implements Terraform-like workflows for network infrastructure. It provides a professional, safe, and extensible approach to automating network device configurations using SSH connectivity and Jinja2 templates.

### Core Philosophy
- **Safety First**: Plan before apply, with confirmation prompts and dry-run capabilities
- **Infrastructure as Code**: Template-driven configuration management
- **Vendor Agnostic**: Extensible driver system supporting multiple network device types
- **Dynamic Discovery**: Templates and capabilities discovered automatically from filesystem
- **Professional Interface**: Modern Typer+Rich CLI with beautiful terminal output
- **Enhanced UX**: Interactive prompts, progress indicators, and structured visual feedback

## System Capabilities

### Primary Operations
1. **Device Discovery**: List and validate network devices from inventory with rich table output
2. **Connectivity Testing**: SSH connectivity validation with real-time progress indicators
3. **Configuration Planning**: Preview configuration changes with structured visual panels
4. **Configuration Application**: Apply templates with interactive confirmation prompts
5. **Template Management**: Dynamic discovery and validation with comprehensive metadata display
6. **Enhanced Reporting**: Beautiful terminal output with tables, panels, and status indicators

### Supported Workflows
- `plan` - Show configuration changes that would be applied (like `terraform plan`)
- `apply` - Apply configuration changes with confirmation (like `terraform apply`)
- `apply --force` - Apply without confirmation for automation (like `terraform apply -auto-approve`)
- `check` - Validate SSH connectivity to devices
- `list` - Display available devices and their properties
- `templates` - Show dynamically discovered templates with metadata

## Technical Architecture

### Core Components
- **CLI Orchestrator** (`main.py`): Command processing and user interaction
- **Template Discovery System** (`template_discovery.py`): Dynamic template detection with metadata
- **Driver System** (`drivers/`): Vendor-specific device interaction handlers
- **Configuration Rendering** (`render/`): Jinja2 template processing with device data
- **Inventory Management** (`inventory/devices.yml`): YAML-based device definitions
- **Validation Systems** (`validate_templates.py`, `diagnostics.py`): Safety and consistency checks

### Device Driver System
- **huawei_vrp5**: For Huawei VRP 5.x devices (no commit required)
- **huawei_vrp8**: For Huawei VRP 8.x devices (commit-based configuration)
- **routeros7**: For MikroTik RouterOS 7.x devices
- **Extensible**: New drivers can be added without core system modifications

### Template System
Templates are Jinja2 files with embedded metadata:
```jinja2
{#
  description: Human-readable description of template purpose
  safe: true|false (safety flag for automated operations)  
  changes_hostname: true|false (hostname modification flag)
#}
```

Templates are organized by vendor (`templates/<vendor>/<template>.j2`) and discovered dynamically.

## Data Structures

### Device Inventory Schema
```yaml
devices:
  - name: device-identifier          # Unique device name
    host: ip-or-hostname            # Network address  
    vendor: driver-identifier       # Driver to use (huawei_vrp5, huawei_vrp8, routeros7)
    device_type: netmiko-type       # Netmiko device type for SSH
    username: ssh-username          # SSH authentication
    password: ssh-password          # SSH authentication
    template: optional-template     # Override default template
    log_path: optional-path         # Custom log directory
    session_log: log-filename       # SSH session log file
    interfaces:                     # Interface configuration data
      - name: interface-name        # Physical interface identifier
        ip: ip-address              # IP address to assign
        mask: subnet-mask           # Subnet mask
```

### Template Variables
Templates receive structured data:
- `hostname`: Device name from inventory
- `interfaces`: List of interface configuration objects
- Custom variables can be added per device in inventory

## Safety Mechanisms

### Multi-Layer Safety System
1. **Template Metadata**: Templates declare safety characteristics
2. **Plan-First Workflow**: Always preview changes before application
3. **User Confirmation**: Interactive approval for configuration changes
4. **SSH Validation**: Connectivity testing before configuration attempts
5. **Error Recovery**: Graceful handling of connection and configuration failures
6. **Detailed Logging**: Comprehensive audit trail in configurable log files

### Risk Assessment
- Templates marked as `safe: false` generate warnings
- Hostname-changing templates trigger special warnings
- Dry-run mode allows risk-free testing
- Force flag bypasses confirmations for automation scenarios

## MCP Integration Points

### Safe Operations (No Confirmation Required)
- Device listing and inventory queries
- SSH connectivity testing  
- Template discovery and validation
- Configuration planning (dry-run operations)
- Log file analysis and diagnostics

### Dangerous Operations (Require Explicit Confirmation)
- Configuration application (`apply` commands)
- Template creation or modification
- Inventory modifications
- Any operation that changes device state

### Recommended MCP Functions
```python
# Safe operations
def list_devices() -> List[Dict]
def check_device_connectivity(device_name: str) -> Dict
def list_templates(vendor: str = None) -> Dict  
def plan_configuration(device_name: str, template: str = None) -> Dict
def validate_template(vendor: str, template_name: str) -> Dict

# Dangerous operations (require confirmation parameter)
def apply_configuration(device_name: str, template: str = None, confirm: bool = False) -> Dict
```

## Current System State

### Working Features
- Complete Terraform-like CLI workflow
- Dynamic template discovery with metadata
- Multi-vendor driver system with error recovery
- SSH connectivity validation and diagnostics
- Template syntax validation and safety analysis
- Configurable logging and audit trails
- Professional CLI interface with colored output

### File Structure
```
network-automator/
├── main.py                    # Typer-based CLI interface and orchestration
├── netdevops                  # CLI wrapper script
├── activate.sh                # Environment activation script
├── requirements.txt           # Python dependencies including Typer
├── pyproject.toml            # Package configuration
├── template_discovery.py      # Dynamic template management
├── validate_templates.py      # Template validation utility  
├── diagnostics.py            # SSH and device diagnostics
├── drivers/                  # Vendor-specific device drivers
│   ├── huawei_vrp5.py
│   ├── huawei_vrp8.py
│   └── routeros7.py
├── templates/                # Jinja2 configuration templates
│   ├── huawei_vrp5/
│   ├── huawei_vrp8/
│   └── routeros7/
├── inventory/
│   └── devices.yml           # Device definitions
├── logs/                     # SSH session logs
├── render/                   # Template processing engine
├── utils/                    # Connection parameter utilities
└── .ai/                      # AI integration documentation
```

### Dependencies
- **typer**: Modern CLI framework with Rich integration
- **rich**: Beautiful terminal output and formatting
- **netmiko**: SSH device connectivity and command execution
- **jinja2**: Template rendering engine
- **pyyaml**: Configuration file parsing
- **python 3.8+**: Runtime environment

## Operational Considerations

### Performance Characteristics
- Sequential device processing (safe, predictable)
- Template discovery caching for efficiency  
- SSH connection reuse within operations
- Configurable timeouts for network operations

### Error Handling Philosophy
- Fail fast with clear error messages
- Continue processing other devices on individual failures
- Comprehensive logging for debugging
- Graceful degradation when possible

### Extensibility Points
- New device drivers: Add Python module in `drivers/` directory
- New templates: Add `.j2` files in appropriate vendor directory
- New CLI commands: Extend argument parser and add handlers
- Custom validation: Extend template validation system

This framework represents a production-ready network automation solution with enterprise-grade safety mechanisms and professional operational characteristics.