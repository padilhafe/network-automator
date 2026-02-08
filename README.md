# Network Automator

**ATENTION - SOFTWARE IN ACTIVE DEVELOPMENT - USE AT YOUR OWN RISK**
**STILL NOT STATE AWARE, WILL REWRITE EXISTING CONFIGURATION WHEN A TEMPLTE IS APPLIED**

![Network Automator](https://img.shields.io/badge/Network-Automator-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![CLI](https://img.shields.io/badge/CLI-Typer-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

A professional network device configuration management tool inspired by Terraform workflows. Built with Python, featuring a modern Typer-based CLI with Rich formatting for an exceptional user experience.

📍 **[View Project Roadmap](ROADMAP.md)** - See what's coming next!

## 🚀 Features

- **🎯 Terraform-like Workflow**: Plan before apply with comprehensive preview
- **🔍 Dynamic Template Discovery**: Automatic detection of configuration templates
- **🏗️ Multi-Vendor Support**: Extensible driver system for different network devices
- **🛡️ Safety First**: Multiple validation layers and confirmation prompts
- **🎨 Modern CLI**: Beautiful terminal interface powered by Typer and Rich
- **📊 Rich Reporting**: Detailed progress tracking and result summaries
- **🔧 Infrastructure as Code**: Jinja2-based template system
- **📝 Comprehensive Logging**: Full audit trail with configurable logging

## 📋 Supported Vendors

| Vendor | Driver | Description |
|--------|--------|-------------|
| Huawei VRP 5.x | `huawei_vrp5` | Legacy VRP (no commit required) |
| Huawei VRP 8.x | `huawei_vrp8` | Modern VRP (commit-based) |
| MikroTik RouterOS 7.x | `routeros7` | RouterOS 7.x series |

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- SSH access to target network devices
- Device inventory in YAML format

### Install from Source (Recommended)

```bash
git clone https://github.com/padilhafe/network-automator.git
cd network-automator

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Quick Setup with Installation Script

```bash
git clone https://github.com/padilhafe/network-automator.git
cd network-automator
./install.sh  # Sets up everything automatically
```

### Alternative: Install Dependencies Only

```bash
pip install -r requirements.txt
# Then use: python -m network_automator.main
```

## 🚀 Quick Start

### 1. Configure Device Inventory

Create or update `inventory/devices.yml`:

```yaml
devices:
  - name: huawei-core-01
    host: 192.168.1.1
    vendor: huawei_vrp8
    device_type: huawei
    username: admin
    password: your_password
    interfaces:
      - name: GE0/0/1
        ip: 10.0.1.1
        mask: 255.255.255.0
      - name: GE0/0/2
        ip: 10.0.2.1
        mask: 255.255.255.0
        
  - name: mikrotik-edge-01
    host: 192.168.1.10
    vendor: routeros7
    device_type: mikrotik_routeros
    username: admin
    password: your_password
    interfaces:
      - name: ether1
        ip: 192.168.100.1
        mask: 255.255.255.0
```

### 2. Basic Commands

```bash
# List all available devices
nacli list

# Show available templates
nacli templates

# Test SSH connectivity
nacli check

# Preview configuration changes (safe)
nacli plan

# Apply configurations (interactive confirmation)
nacli apply

# Apply without confirmation (automation mode)
nacli apply --force
```

## 📚 Command Reference

### Device Management

```bash
# List all devices
nacli list

# Check SSH connectivity to all devices
nacli check

# Check specific device
nacli check huawei-core-01
```

### Template Management

```bash
# List all available templates
nacli templates

# List templates for specific vendor
nacli templates huawei_vrp8

# Show template discovery summary
nacli templates --summary
```

### Configuration Planning

```bash
# Plan changes for all devices
nacli plan

# Plan changes for specific device
nacli plan huawei-core-01

# Plan with specific template
nacli plan --template router_no_hostname

# Plan for specific device with template
nacli plan huawei-core-01 --template default
```

### Configuration Application

```bash
# Apply with confirmation prompts (recommended)
nacli apply

# Apply to specific device
nacli apply huawei-core-01

# Apply with specific template
nacli apply --template router_no_hostname

# Apply without confirmation (automation)
nacli apply --force

# Apply specific device without confirmation
nacli apply huawei-core-01 --force
```

### Utility Commands

```bash
# Show version information
nacli version

# Get help for any command
nacli --help
nacli apply --help

# Show inventory statistics
nacli stats

# Validate templates
nacli validate
```

## 📁 Project Structure

```
network-automator/
├── network_automator/         # Main package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # CLI application (Typer+Rich)
│   ├── template_discovery.py # Dynamic template discovery
│   ├── drivers/              # Device-specific drivers
│   │   ├── huawei_vrp5.py
│   │   ├── huawei_vrp8.py
│   │   └── routeros7.py
│   ├── render/               # Template rendering engine
│   └── utils/                # Utility functions
├── inventory/
│   └── devices.yml           # Device inventory
├── templates/                # Configuration templates
│   ├── huawei_vrp5/
│   ├── huawei_vrp8/
│   └── routeros7/
├── logs/                     # SSH session logs
├── .ai/                      # AI integration documentation
├── .github/                  # GitHub templates and workflows
├── nacli                     # CLI wrapper script
├── install.sh                # Installation script for Unix systems
├── pyproject.toml            # Package configuration
├── requirements.txt          # Python dependencies
├── ROADMAP.md                # Project roadmap and future plans
├── diagnostics.py            # Legacy diagnostic utilities
├── help.py                   # Legacy help utilities
└── basic_config.txt          # Basic configuration examples
```

## 📝 Template Development

### Template Structure

Templates use Jinja2 syntax with embedded metadata:

```jinja2
{#
  description: Basic interface configuration for Huawei devices
  safe: true
  changes_hostname: false
#}
system-view
{% for iface in interfaces %}
interface {{ iface.name }}
 ip address {{ iface.ip }} {{ iface.mask }}
 undo shutdown
quit
{% endfor %}
quit
save force
```

### Template Metadata

- `description`: Human-readable description
- `safe`: Boolean flag for automation safety
- `changes_hostname`: Boolean flag for hostname changes

### Available Variables

Templates have access to:

- `hostname`: Device name from inventory
- `interfaces`: List of interface configurations
  - `name`: Interface name
  - `ip`: IP address
  - `mask`: Subnet mask

## 🔧 Adding New Vendors

### 1. Create Driver

Create `drivers/new_vendor.py`:

```python
def send_config(conn, config_set):
    """
    Send configuration commands to device
    
    Args:
        conn: Active Netmiko connection object
        config_set: List of configuration commands
    
    Returns:
        str: Device output
    """
    try:
        output = conn.send_config_set(config_set)
        return output
    except Exception as e:
        return f"[ERROR] Configuration failed: {str(e)}"
```

### 2. Register Driver

Add to `main.py`:

```python
from drivers import huawei_vrp5, huawei_vrp8, routeros7, new_vendor

DRIVERS = {
    # existing drivers...
    "new_vendor": new_vendor,
}
```

### 3. Create Templates

```bash
mkdir templates/new_vendor
```

Create `templates/new_vendor/default.j2` with appropriate syntax.

## 🛡️ Security & Safety

### Safety Mechanisms

1. **Plan-Before-Apply**: Always preview changes before execution
2. **Template Metadata**: Safety flags prevent accidental dangerous operations
3. **SSH Validation**: Connectivity testing before configuration
4. **User Confirmation**: Interactive prompts for critical operations
5. **Comprehensive Logging**: Full audit trail of all operations

### Best Practices

- Always run `plan` before `apply`
- Use `--force` only in automated environments
- Review template metadata before use
- Test on lab devices before production
- Keep device inventory up to date
- Monitor logs for issues

## 📊 Advanced Usage

### Template Priority

1. `--template <name>` (command line override)
2. `template` in device YAML (inventory specification)
3. `default` template (automatic fallback)

### Filtering Operations

```bash
# Work with specific devices
nacli check device-name
nacli plan device-name
nacli apply device-name

# Use specific templates
nacli plan --template safe_template
nacli apply --template router_no_hostname
```

### Automation Integration

```bash
# CI/CD Pipeline example
nacli check || exit 1
nacli plan --template production
nacli apply --template production --force
```

## 🐛 Troubleshooting

### Common Issues

**SSH Connection Failed**
```bash
# Test manual SSH
ssh username@device_ip

# Check connectivity
nacli check device-name

# Verify inventory credentials
cat inventory/devices.yml
```

**Template Not Found**
```bash
# List available templates
nacli templates

# Check template location
ls templates/vendor_name/
```

**Configuration Errors**
```bash
# Review logs
tail -f logs/netmiko_*.log

# Run with verbose output
nacli plan device-name  # Safe dry-run first
```

### Getting Help

- Use `nacli --help` for command help
- Use `nacli examples` for usage examples
- Use `nacli stats --validate` for inventory validation
- Use `nacli validate` for template validation
- Check the `.ai/` directory for detailed documentation
- Enable debug logging in drivers for detailed output

## 🤝 Contributing

### Development Setup

```bash
git clone https://github.com/padilhafe/network-automator.git
cd network-automator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or use the installation script
./install.sh
```

### Development Commands

```bash
# After installation, use either:
nacli <command>        # Installed command
./nacli <command>      # Project wrapper script

# Both methods work identically
nacli list
./nacli templates
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy .

# Linting
flake8 .

# Run tests
pytest
```

### Adding Features

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code quality checks pass
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Typer**: Modern CLI framework
- **Rich**: Beautiful terminal formatting
- **Netmiko**: Network device SSH connectivity
- **Jinja2**: Powerful templating engine
- **PyYAML**: YAML configuration parsing

## 📞 Support

- 📧 Email: contato@felipepadilha.com.br
- 🐛 Issues: [GitHub Issues](https://github.com/padilhafe/network-automator/issues)
- 📖 Documentation: [GitHub Repository](https://github.com/padilhafe/network-automator)

---

**Network Automator** - Professional Network Device Configuration Management