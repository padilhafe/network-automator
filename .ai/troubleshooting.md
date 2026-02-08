# NetDevOps Framework - Troubleshooting Guide

## Overview
This guide provides comprehensive troubleshooting steps for common issues encountered while using the NetDevOps Framework.

## Common Issues and Solutions

### 1. SSH Connection Problems

#### Issue: "SSH FAILED: Authentication failed"
**Symptoms**: Cannot connect to device, authentication errors
**Causes**:
- Incorrect username/password in inventory
- SSH service not enabled on device
- Authentication method mismatch

**Solutions**:
```bash
# Test manual SSH connection
ssh username@device_ip

# Check inventory credentials
cat inventory/devices.yml | grep -A 5 device_name

# Verify SSH service on device (if accessible via console)
display ssh server status  # Huawei
/ip service print         # RouterOS
```

#### Issue: "SSH FAILED: Connection timeout"
**Symptoms**: Long delays before connection failure
**Causes**:
- Network connectivity issues
- Firewall blocking SSH port
- Device overloaded or unresponsive

**Solutions**:
```bash
# Test network connectivity
ping device_ip

# Test SSH port specifically
telnet device_ip 22
nc -zv device_ip 22

# Check if alternate SSH port is configured
nmap -p 22,2222,830 device_ip
```

#### Issue: "SSH FAILED: Host key verification failed"
**Symptoms**: SSH key verification errors
**Solutions**:
```bash
# Remove old host key
ssh-keygen -R device_ip

# Accept new host key manually
ssh -o StrictHostKeyChecking=no username@device_ip

# Configure SSH config file
echo "StrictHostKeyChecking no" >> ~/.ssh/config
```

### 2. Template-Related Issues

#### Issue: "Template 'template_name' not found"
**Symptoms**: Template discovery fails to find specified template
**Diagnosis**:
```bash
# List all available templates
python main.py templates

# Check specific vendor templates
ls -la templates/vendor_name/

# Validate template syntax
python validate_templates.py --template vendor_name template_name
```

**Solutions**:
- Ensure template file exists in correct vendor directory
- Verify template has .j2 extension
- Check file permissions (must be readable)
- Validate template syntax with validator

#### Issue: "Template syntax errors"
**Symptoms**: Jinja2 parsing errors during template rendering
**Diagnosis**:
```bash
# Run template validation
python validate_templates.py

# Check specific template
python validate_templates.py --template vendor_name template_name
```

**Common Syntax Issues**:
```jinja2
# WRONG: Missing closing brace
{% for iface in interfaces %
  interface {{ iface.name }}
{% endfor %}

# CORRECT: Proper braces
{% for iface in interfaces %}
  interface {{ iface.name }}
{% endfor %}

# WRONG: Invalid variable reference
{{ interface.nonexistent_field }}

# CORRECT: Valid variable reference
{{ iface.name }}
```

#### Issue: "Template renders empty configuration"
**Symptoms**: Template processes but produces no output
**Diagnosis**:
- Check if template uses correct variable names
- Verify inventory data structure
- Validate template logic

**Solutions**:
```python
# Debug template variables
python -c "
import yaml
with open('inventory/devices.yml') as f:
    devices = yaml.safe_load(f)['devices']
    device = next(d for d in devices if d['name'] == 'device_name')
    print('Available data:', device.keys())
    print('Interfaces:', device.get('interfaces', []))
"
```

### 3. Configuration Application Issues

#### Issue: "Pattern not detected" (VRP8 devices)
**Symptoms**: Netmiko fails with pattern detection errors
**Causes**:
- Prompt changes during configuration
- Timeout issues with commit commands
- Device response delays

**Solutions**:
1. Use safe templates that don't change hostname:
```bash
python main.py plan device_name --template default
```

2. Increase timeouts in driver code:
```python
# In drivers/huawei_vrp8.py, increase delay_factor
conn.send_command_timing("commit", delay_factor=6)
```

3. Check device logs for issues:
```bash
tail -f logs/netmiko_device.log
```

#### Issue: "Configuration partially applied"
**Symptoms**: Some commands succeed, others fail
**Diagnosis**:
```bash
# Check device output in logs
grep -A 10 -B 10 "Error\|Failed" logs/netmiko_device.log

# Check device current configuration
python -c "
from netmiko import ConnectHandler
from utils import get_connection_params
import yaml

devices = yaml.safe_load(open('inventory/devices.yml'))['devices']
device = next(d for d in devices if d['name'] == 'device_name')
conn_params = get_connection_params(device)

with ConnectHandler(**conn_params) as conn:
    output = conn.send_command('display current-configuration')
    print(output)
"
```

**Solutions**:
- Review failed commands for syntax issues
- Check device permissions and capabilities
- Verify interface names and IP ranges
- Use dry-run mode to test before applying

### 4. Driver-Specific Issues

#### Huawei VRP8 Issues
**Common Problems**:
- Commit timeouts
- Prompt detection failures
- Configuration rollback on errors

**Solutions**:
```python
# Extended timeout configuration
conn.send_command_timing("commit", delay_factor=8)

# Manual prompt detection
conn.find_prompt()
```

#### Huawei VRP5 Issues
**Common Problems**:
- Configuration not saved automatically
- Session timeouts during large configs

**Solutions**:
```python
# Force configuration save
conn.send_command("save force")

# Break large configurations into smaller chunks
```

#### RouterOS Issues
**Common Problems**:
- Command syntax variations
- Interface naming inconsistencies

**Solutions**:
- Use RouterOS-specific command syntax
- Verify interface names with `/interface print`

### 5. Inventory Configuration Issues

#### Issue: "Device not found in inventory"
**Symptoms**: Device name not recognized
**Solutions**:
```bash
# List all devices
python main.py list

# Check inventory syntax
python -c "import yaml; print(yaml.safe_load(open('inventory/devices.yml')))"

# Validate inventory structure
python stats.py --validate
```

#### Issue: "Invalid vendor specified"
**Symptoms**: Vendor not recognized by system
**Solutions**:
- Ensure vendor matches available drivers
- Check spelling in inventory file
- Verify driver is imported in main.py

### 6. Performance Issues

#### Issue: "Commands take too long to execute"
**Symptoms**: Long execution times, timeouts
**Causes**:
- Network latency
- Device processing delays
- Large configuration sets

**Solutions**:
```bash
# Test network latency
ping -c 10 device_ip

# Reduce configuration size
python main.py plan device_name --template minimal_template

# Increase timeout values
# Edit drivers to use larger delay_factor values
```

#### Issue: "Memory or CPU usage is high"
**Symptoms**: System performance degradation
**Solutions**:
- Process devices sequentially instead of parallel
- Clear template cache between operations
- Monitor system resources
- Use connection pooling carefully

### 7. Logging and Debugging

#### Enable Debug Logging
```python
# Add to beginning of main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Check Session Logs
```bash
# Monitor real-time logs
tail -f logs/netmiko_device.log

# Search for specific patterns
grep -i error logs/*.log
grep -i timeout logs/*.log
```

#### Diagnostic Commands
```bash
# Run diagnostic utility
python diagnostics.py device_name

# Test template validation
python validate_templates.py

# Check inventory consistency
python stats.py --validate
```

## Emergency Recovery Procedures

### 1. Device Becomes Unresponsive
1. Wait for current operation to timeout
2. Check device via console/alternate access
3. Verify configuration state
4. Rollback if necessary using device-specific commands

### 2. Corrupted Configuration
1. Access device via console
2. Use device rollback features:
```bash
# Huawei VRP8
rollback configuration to label backup_label

# RouterOS
/system backup load name=backup_name
```

### 3. SSH Access Lost
1. Use console access to restore SSH service
2. Check SSH daemon status
3. Verify IP configuration
4. Reset SSH keys if necessary

## Best Practices for Avoiding Issues

### 1. Pre-Deployment Validation
```bash
# Always validate before applying
python main.py plan device_name
python validate_templates.py
python stats.py --validate
```

### 2. Incremental Changes
- Apply changes to test devices first
- Use minimal templates for initial testing
- Implement changes in small batches

### 3. Backup Strategy
- Create configuration backups before changes
- Document baseline configurations
- Test rollback procedures

### 4. Monitoring
- Monitor session logs during operations
- Use diagnostic tools regularly
- Keep inventory documentation current

### 5. Testing Environment
- Use lab devices for testing new templates
- Validate templates with sample data
- Test driver modifications carefully

## Getting Help

### Internal Diagnostics
```bash
python diagnostics.py device_name    # Device-specific diagnostics
python validate_templates.py         # Template validation
python stats.py --all                # Complete system analysis
```

### Log Analysis
```bash
# Recent errors across all logs
find logs/ -name "*.log" -mtime -1 -exec grep -l -i error {} \;

# Session timeline for specific device
grep -h "^[0-9]" logs/netmiko_device.log | sort
```

### System State Verification
```bash
# Verify all components
python -c "
from template_discovery import TemplateDiscovery
from main import load_inventory

print('Templates:', TemplateDiscovery().discover_all_templates().keys())
print('Devices:', len(load_inventory()))
print('Drivers:', list(DRIVERS.keys()))
"
```

### Environmental Checks
```bash
# Python environment
python --version
pip list | grep -E "(netmiko|jinja2|yaml)"

# File permissions
find . -name "*.py" ! -perm -644 -ls
find templates/ ! -perm -644 -ls
```
