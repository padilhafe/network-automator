# Network Automator - API Guide for MCP Integration

## Overview
This document describes the programmatic API surface of the Network Automator, designed for integration with Model Context Protocol (MCP) and AI assistants.

## Core API Functions

### Device Management

#### `load_inventory(path="inventory/devices.yml") -> List[Dict]`
**Purpose**: Load device inventory from YAML configuration
**Parameters**:
- `path`: Path to inventory YAML file
**Returns**: List of device dictionaries with connection and configuration parameters
**Example**:
```python
devices = load_inventory()
# Returns: [{"name": "device1", "host": "192.168.1.1", "vendor": "huawei_vrp8", ...}]
```

#### `check_ssh(device: Dict) -> Tuple[bool, str]`
**Purpose**: Test SSH connectivity to a device
**Parameters**:
- `device`: Device dictionary from inventory
**Returns**: Tuple of (success_boolean, status_message)
**Example**:
```python
ok, msg = check_ssh(device)
# Returns: (True, "SSH OK - Prompt: <HUAWEI> (2.34s)")
```

### Template Operations

#### `TemplateDiscovery.discover_all_templates() -> Dict[str, List[TemplateInfo]]`
**Purpose**: Discover all available templates dynamically
**Returns**: Dictionary mapping vendor names to lists of TemplateInfo objects
**Example**:
```python
discovery = TemplateDiscovery()
templates = discovery.discover_all_templates()
# Returns: {"huawei_vrp8": [TemplateInfo(...), ...], ...}
```

#### `TemplateDiscovery.find_template(vendor: str, template_name: str) -> Optional[TemplateInfo]`
**Purpose**: Find a specific template by vendor and name
**Parameters**:
- `vendor`: Vendor identifier (e.g., "huawei_vrp8")
- `template_name`: Template name without .j2 extension
**Returns**: TemplateInfo object or None if not found

#### `render_template(vendor: str, template_name: str, dados: Dict) -> str`
**Purpose**: Render a Jinja2 template with device data
**Parameters**:
- `vendor`: Vendor identifier
- `template_name`: Template filename (with .j2 extension)
- `dados`: Dictionary of template variables
**Returns**: Rendered configuration as string
**Example**:
```python
config = render_template("huawei_vrp8", "default.j2", {
    "hostname": "device1",
    "interfaces": [{"name": "Eth1/0/1", "ip": "10.0.1.1", "mask": "255.255.255.0"}]
})
```

### Configuration Operations

#### `apply_config(device: Dict, template_override: str = None, dry_run: bool = False) -> str`
**Purpose**: Apply or preview configuration changes
**Parameters**:
- `device`: Device dictionary from inventory
- `template_override`: Optional template name override
- `dry_run`: If True, only show what would be applied
**Returns**: Configuration output or preview text
**Example**:
```python
# Preview changes
result = apply_config(device, "default", dry_run=True)

# Apply changes
result = apply_config(device, "default", dry_run=False)
```

### Driver System

#### `DRIVERS[vendor].send_config(conn, config_set: List[str]) -> str`
**Purpose**: Execute configuration commands on device
**Parameters**:
- `conn`: Active Netmiko connection object
- `config_set`: List of configuration commands
**Returns**: Device output from command execution
**Available Drivers**:
- `huawei_vrp5`: For VRP 5.x devices (no commit)
- `huawei_vrp8`: For VRP 8.x devices (with commit)
- `routeros7`: For RouterOS 7.x devices

## Data Structures

### Device Dictionary Schema
```python
{
    "name": str,           # Unique device identifier
    "host": str,           # IP address or hostname
    "vendor": str,         # Driver identifier
    "device_type": str,    # Netmiko device type
    "username": str,       # SSH username
    "password": str,       # SSH password
    "template": str,       # Optional: override template
    "log_path": str,       # Optional: log directory
    "session_log": str,    # Optional: log filename
    "interfaces": [        # List of interface configurations
        {
            "name": str,   # Interface name
            "ip": str,     # IP address
            "mask": str    # Subnet mask
        }
    ]
}
```

### TemplateInfo Object
```python
class TemplateInfo:
    name: str              # Template name (without .j2)
    path: str              # Full filesystem path
    vendor: str            # Vendor identifier
    description: str       # Human-readable description
    safe: bool             # Whether template is considered safe
    changes_hostname: bool # Whether template modifies device hostname
```

### Template Metadata Format
Templates include metadata in Jinja2 comments:
```jinja2
{#
  description: Basic interface configuration for Huawei VRP 8.x devices
  safe: true
  changes_hostname: false
#}
```

## MCP Function Mappings

### Recommended MCP Tools

#### `nacli_list_devices`
```python
def netdevops_list_devices() -> List[Dict]:
    """List all available network devices"""
    return load_inventory()
```

#### `nacli_check_connectivity`
```python
def netdevops_check_connectivity(device_name: str) -> Dict:
    """Test SSH connectivity to a specific device"""
    devices = load_inventory()
    device = next((d for d in devices if d["name"] == device_name), None)
    if not device:
        return {"error": f"Device {device_name} not found"}
    
    ok, msg = check_ssh(device)
    return {"success": ok, "message": msg}
```

#### `nacli_list_templates`
```python
def netdevops_list_templates(vendor: str = None) -> Dict:
    """List available configuration templates"""
    discovery = TemplateDiscovery()
    all_templates = discovery.discover_all_templates()
    
    if vendor:
        return {vendor: all_templates.get(vendor, [])}
    return all_templates
```

#### `nacli_plan_config`
```python
def netdevops_plan_config(device_name: str, template_name: str = None) -> Dict:
    """Preview configuration changes without applying"""
    devices = load_inventory()
    device = next((d for d in devices if d["name"] == device_name), None)
    if not device:
        return {"error": f"Device {device_name} not found"}
    
    try:
        result = apply_config(device, template_name, dry_run=True)
        return {"success": True, "preview": result}
    except Exception as e:
        return {"error": str(e)}
```

#### `nacli_apply_config`
```python
def netdevops_apply_config(device_name: str, template_name: str = None, confirm: bool = False) -> Dict:
    """Apply configuration changes to device"""
    if not confirm:
        return {"error": "Configuration application requires explicit confirmation"}
    
    devices = load_inventory()
    device = next((d for d in devices if d["name"] == device_name), None)
    if not device:
        return {"error": f"Device {device_name} not found"}
    
    try:
        result = apply_config(device, template_name, dry_run=False)
        return {"success": True, "output": result}
    except Exception as e:
        return {"error": str(e)}
```

#### `nacli_validate_template`
```python
def netdevops_validate_template(vendor: str, template_name: str) -> Dict:
    """Validate template syntax and metadata"""
    from validate_templates import TemplateValidator
    
    validator = TemplateValidator()
    success = validator.validate_template_reference(vendor, template_name)
    return {"valid": success}
```

## Safety Considerations for MCP

### Required Confirmations
- Configuration changes should always require explicit confirmation
- Preview operations (plan) are safe and can be automated
- Template validation is safe and can be automated
- Connectivity testing is generally safe but may consume resources

### Error Handling
```python
def safe_wrapper(func):
    """Wrapper for safe MCP function execution"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {"error": f"Operation failed: {str(e)}", "success": False}
    return wrapper
```

### Rate Limiting
- Implement delays between device operations
- Limit concurrent SSH connections
- Cache template discovery results

## Integration Examples

### Basic Device Status Check
```python
# Check all devices
devices = nacli_list_devices()
for device in devices:
    status = nacli_check_connectivity(device["name"])
    print(f"{device['name']}: {status['message']}")
```

### Configuration Workflow
```python
# Plan changes
plan_result = nacli_plan_config("device1", "default")
if plan_result["success"]:
    print(f"Planned changes:\n{plan_result['preview']}")
    
    # Apply with confirmation
    apply_result = nacli_apply_config("device1", "default", confirm=True)
    if apply_result["success"]:
        print(f"Applied successfully:\n{apply_result['output']}")
```

### Template Management
```python
# List templates for specific vendor
templates = nacli_list_templates("huawei_vrp8")
for template in templates["huawei_vrp8"]:
    validation = nacli_validate_template("huawei_vrp8", template.name)
    print(f"{template.name}: {'Valid' if validation['valid'] else 'Invalid'}")
```

## Environment Requirements

### Dependencies
```python
# Required packages
netmiko>=4.0.0
jinja2>=3.0.0
pyyaml>=6.0.0
```

### File Structure
```
network-automator/
├── inventory/devices.yml    # Device inventory
├── templates/               # Template directories
│   ├── huawei_vrp5/
│   ├── huawei_vrp8/
│   └── routeros7/
├── drivers/                 # Device drivers
├── logs/                    # Session logs
└── .ai/                     # AI integration docs
```

### Configuration
- Ensure inventory/devices.yml is properly configured
- Verify SSH connectivity to target devices
- Validate all templates before use
- Configure appropriate logging levels