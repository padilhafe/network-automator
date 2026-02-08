# NetDevOps Framework - Development Guide

## Overview
This guide provides instructions for developers who want to extend, modify, or contribute to the NetDevOps Framework.

## Development Environment Setup

### Prerequisites
- Python 3.8 or higher
- Git for version control
- Text editor or IDE with Python support
- Network access to test devices (lab environment recommended)

### Installation
```bash
git clone <repository-url>
cd lab01
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Development Dependencies
```bash
pip install black flake8 pytest mypy  # Code quality tools
```

## Code Architecture Overview

### Core Components
1. **CLI Interface** (`main.py`) - Command-line interface and orchestration
2. **Template System** (`template_discovery.py`) - Dynamic template discovery and metadata
3. **Driver System** (`drivers/`) - Vendor-specific device interaction logic
4. **Rendering Engine** (`render/`) - Jinja2 template processing
5. **Utilities** (`utils/`, `diagnostics.py`, etc.) - Supporting functionality

### Design Principles
- **Separation of Concerns**: Each module has a clear, single responsibility
- **Extensibility**: New vendors and templates can be added without core changes
- **Safety**: Default to safe operations, require explicit confirmation for risky ones
- **Discoverability**: Templates and capabilities are discovered dynamically
- **Testability**: Functions are pure and side-effects are isolated

## Adding New Vendors

### 1. Create Driver Module
Create `drivers/<vendor_name>.py`:
```python
def send_config(conn, config_set):
    """
    Send configuration commands to device
    
    Args:
        conn: Active Netmiko connection object
        config_set: List of configuration command strings
    
    Returns:
        str: Device output from command execution
    """
    # Vendor-specific implementation
    try:
        output = conn.send_config_set(config_set)
        # Add any vendor-specific post-processing
        return output
    except Exception as e:
        return f"[ERROR] Configuration failed: {str(e)}"
```

### 2. Register Driver
In `main.py`, add driver import and registration:
```python
from drivers import huawei_vrp5, huawei_vrp8, routeros7, new_vendor

DRIVERS = {
    "huawei_vrp5": huawei_vrp5,
    "huawei_vrp8": huawei_vrp8,
    "routeros7": routeros7,
    "new_vendor": new_vendor,
}
```

### 3. Create Template Directory
```bash
mkdir templates/new_vendor
```

### 4. Create Default Template
Create `templates/new_vendor/default.j2`:
```jinja2
{#
  description: Basic configuration for New Vendor devices
  safe: true
  changes_hostname: false
#}
{% for iface in interfaces %}
interface {{ iface.name }}
 ip address {{ iface.ip }} {{ iface.mask }}
 no shutdown
exit
{% endfor %}
```

### 5. Test Integration
```bash
# Add device to inventory with new vendor
python main.py templates  # Should show new vendor
python main.py plan test_device  # Test configuration generation
```

## Adding New Templates

### Template Structure
Templates must follow this structure:
```jinja2
{#
  description: Human-readable description of what this template does
  safe: true|false (whether template is considered safe for automated use)
  changes_hostname: true|false (whether template modifies device hostname)
#}
# Template content using Jinja2 syntax
```

### Available Variables
Templates have access to these variables:
- `hostname`: Device name from inventory
- `interfaces`: List of interface dictionaries with `name`, `ip`, `mask`
- Custom variables can be added to inventory per device

### Template Validation
Templates are automatically validated for:
- Jinja2 syntax correctness
- Metadata completeness
- Variable usage consistency
- Safety flag accuracy

### Example Template
```jinja2
{#
  description: Complete OSPF configuration with area assignments
  safe: false
  changes_hostname: true
#}
hostname {{ hostname }}

router ospf 1
{% for iface in interfaces %}
 network {{ iface.ip }} 0.0.0.0 area {{ iface.area|default('0') }}
{% endfor %}
exit

{% for iface in interfaces %}
interface {{ iface.name }}
 ip address {{ iface.ip }} {{ iface.mask }}
 ip ospf 1 area {{ iface.area|default('0') }}
 no shutdown
exit
{% endfor %}
```

## Adding New CLI Commands

### 1. Extend Argument Parser
In `main.py`, modify the argument parser:
```python
parser.add_argument(
    "action",
    choices=["list", "templates", "check", "plan", "apply", "new_command"],
    help="Command descriptions..."
)
```

### 2. Implement Command Logic
Add command handling in the main workflow:
```python
elif args.action == "new_command":
    for device in devices:
        result = handle_new_command(device, args)
        results.append(result)
```

### 3. Create Handler Function
```python
def handle_new_command(device, args):
    """Handle new command implementation"""
    try:
        # Command-specific logic
        return {"success": True, "message": "Command executed"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Driver Development Guidelines

### Connection Management
- Always use context managers for connections
- Handle connection timeouts gracefully
- Implement proper cleanup on errors

### Error Handling
```python
def send_config(conn, config_set):
    try:
        # Primary implementation
        output = conn.send_config_set(config_set)
        return output
    except Exception as e:
        # Fallback or recovery logic
        try:
            # Alternative approach
            return fallback_method(conn, config_set)
        except Exception as e2:
            return f"[ERROR] All methods failed: {str(e2)}"
```

### Device-Specific Considerations

#### For Commit-Required Devices
```python
def send_config(conn, config_set):
    output = conn.send_config_set(config_set)
    
    # Execute commit
    commit_output = conn.send_command("commit")
    
    # Handle commit failures
    if "error" in commit_output.lower():
        conn.send_command("rollback")
        raise Exception(f"Commit failed: {commit_output}")
    
    return output + "\n" + commit_output
```

#### For Prompt-Sensitive Devices
```python
def send_config(conn, config_set):
    # Use timing-based commands for unreliable prompt detection
    output = ""
    for cmd in config_set:
        cmd_output = conn.send_command_timing(cmd, delay_factor=2)
        output += f"{cmd}\n{cmd_output}\n"
    return output
```

## Template Development Best Practices

### 1. Always Include Metadata
Every template must have a metadata comment block at the top.

### 2. Use Safe Defaults
- Default to minimal, non-destructive configurations
- Avoid hostname changes unless absolutely necessary
- Include rollback information in comments

### 3. Handle Missing Data Gracefully
```jinja2
{% if interfaces %}
{% for iface in interfaces %}
interface {{ iface.name }}
 ip address {{ iface.ip }} {{ iface.mask|default('255.255.255.0') }}
{% endfor %}
{% else %}
! No interfaces configured
{% endif %}
```

### 4. Document Complex Logic
```jinja2
{# Configure VLAN interfaces if VLANs are specified #}
{% for iface in interfaces %}
{% if iface.vlan is defined %}
interface vlan{{ iface.vlan }}
 ip address {{ iface.ip }} {{ iface.mask }}
{% endif %}
{% endfor %}
```

### 5. Validate Template Variables
Templates should validate required data:
```jinja2
{% if not hostname %}
{# ERROR: hostname is required #}
{% endif %}
```

## Testing Framework

### Unit Testing
Create tests for individual functions:
```python
# tests/test_template_discovery.py
import pytest
from template_discovery import TemplateDiscovery

def test_template_discovery():
    discovery = TemplateDiscovery()
    templates = discovery.discover_all_templates()
    assert len(templates) > 0
    
def test_template_metadata_parsing():
    # Test metadata extraction
    pass
```

### Integration Testing
Test complete workflows:
```python
# tests/test_integration.py
def test_plan_workflow():
    # Test plan command end-to-end
    pass

def test_template_rendering():
    # Test template rendering with sample data
    pass
```

### Manual Testing
```bash
# Test new vendor
python main.py check test_device
python main.py plan test_device --template new_template
python main.py apply test_device --template safe_template --force

# Validate changes
python validate_templates.py
python diagnostics.py test_device
```

## Code Quality Standards

### Style Guide
- Follow PEP 8 Python style guide
- Use Black for code formatting: `black .`
- Use meaningful variable and function names
- Add docstrings for all public functions

### Linting
```bash
flake8 .          # Style and error checking
mypy .            # Type checking
black --check .   # Formatting verification
```

### Documentation
- Include docstrings for all public functions
- Add type hints where appropriate
- Update .ai/ documentation when adding features
- Include usage examples in docstrings

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Implement graceful degradation

## Debugging Tips

### Template Issues
```python
# Debug template rendering
from jinja2 import Environment
env = Environment()
template = env.from_string(template_content)
try:
    result = template.render(template_data)
    print(result)
except Exception as e:
    print(f"Template error: {e}")
```

### Connection Issues
```python
# Debug Netmiko connections
import logging
logging.basicConfig(level=logging.DEBUG)
# Enable detailed Netmiko logging
```

### Driver Issues
```python
# Add debug output to drivers
def send_config(conn, config_set):
    print(f"DEBUG: Executing {len(config_set)} commands")
    for i, cmd in enumerate(config_set):
        print(f"DEBUG: Command {i+1}: {cmd}")
    # ... rest of implementation
```

## Contributing Guidelines

### Development Workflow
1. Create feature branch from main
2. Implement changes with tests
3. Validate with `python validate_templates.py`
4. Run quality checks (`black`, `flake8`, `mypy`)
5. Test on lab devices
6. Update documentation in `.ai/` directory
7. Submit pull request

### Commit Message Format
```
type(scope): brief description

Longer explanation if needed

- Specific changes made
- Any breaking changes
- Related issues
```

### Breaking Changes
- Document all breaking changes
- Provide migration guide
- Update version appropriately
- Test backward compatibility where possible

## Performance Considerations

### Template Caching
- Templates are cached after first discovery
- Cache invalidation happens on restart
- Consider memory usage for large template sets

### Connection Pooling
- Avoid keeping connections open unnecessarily
- Use connection context managers
- Handle connection timeouts gracefully

### Parallel Processing
Current implementation is sequential. For parallel processing:
```python
import concurrent.futures

def process_device_parallel(devices, operation):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(operation, device): device for device in devices}
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results
```

## Security Considerations

### Credential Management
- Never hardcode credentials
- Support external credential stores
- Use SSH keys where possible
- Implement credential rotation

### Template Security
- Validate template sources
- Sanitize user input in templates
- Audit template changes
- Restrict template execution permissions

### Network Security
- Use encrypted connections only
- Validate device certificates
- Implement connection rate limiting
- Log all administrative actions

## Future Development Areas

### Planned Features
- Parallel device processing
- Configuration backup/restore
- Template version management
- REST API interface
- Web UI for non-CLI users

### Architecture Improvements
- Plugin system for drivers
- Configuration validation engine
- Advanced template inheritance
- Real-time configuration monitoring

### Integration Points
- CI/CD pipeline integration
- Network monitoring systems
- Configuration management databases
- Ticketing system integration