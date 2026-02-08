# NetDevOps Framework - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                            │
│  (main.py - Terraform-like commands: plan, apply, check, etc.) │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────────────────┐
│                   Core Orchestrator                             │
│  - Device filtering and selection                               │
│  - Template priority resolution                                 │
│  - Workflow coordination (plan -> apply)                       │
└─────────────┬──────────────┬──────────────┬─────────────────────┘
              │              │              │
    ┌─────────┴─────────┐   ┌┴──────────────┴┐   ┌─────────────────┴──┐
    │  Template System  │   │ Driver System  │   │ Inventory System   │
    └─────────┬─────────┘   └┬──────────────┬┘   └─────────────────┬──┘
              │              │              │                      │
    ┌─────────┴─────────┐   ┌┴─────────┐   ┌┴─────────┐   ┌───────┴────┐
    │Template Discovery │   │ VRP5     │   │ VRP8     │   │Device Specs│
    │    (Dynamic)      │   │(no commit)│   │(commit)  │   │& SSH Params│
    └─────────┬─────────┘   └┬─────────┘   └┬─────────┘   └────────────┘
              │              │              │
    ┌─────────┴─────────┐   ┌┴──────────────┴┐
    │  Jinja2 Engine    │   │    Netmiko     │
    │ (render_template) │   │ (SSH Sessions) │
    └───────────────────┘   └────────────────┘
```

## Component Details

### 1. CLI Interface (`main.py`)
**Responsibility**: User interaction and command orchestration
- Terraform-inspired commands (`plan`, `apply`, `check`, `list`, `templates`)
- Argument parsing and validation
- User confirmation workflows
- Progress reporting and output formatting
- Error handling and user feedback

### 2. Template Discovery System (`template_discovery.py`)
**Responsibility**: Dynamic template management
- **TemplateDiscovery**: Scans filesystem for `.j2` templates
- **TemplateInfo**: Metadata extraction from Jinja2 comments
- **Dynamic Loading**: No hardcoded template references
- **Metadata Parsing**: Extracts `description`, `safe`, `changes_hostname` flags
- **Caching**: Performance optimization for repeated operations

### 3. Driver System (`drivers/`)
**Responsibility**: Device-specific behavior abstraction
- **huawei_vrp5.py**: VRP 5.x devices (no commit required)
  - Uses `send_config_set` with timeout handling
  - Automatic save command execution
  - Hostname change detection
- **huawei_vrp8.py**: VRP 8.x devices (commit required)
  - Uses `send_command_timing` for reliability
  - Manual config command execution
  - Commit handling with fallback mechanisms
  - Advanced error recovery
- **routeros7.py**: MikroTik RouterOS 7.x devices

### 4. Configuration Rendering (`render/`)
**Responsibility**: Template processing
- **Jinja2 Integration**: FileSystemLoader with vendor-specific paths
- **Data Binding**: Device inventory data to template variables
- **Template Resolution**: Dynamic template path resolution

### 5. Inventory Management (`inventory/devices.yml`)
**Responsibility**: Device and connection configuration
- **Device Specifications**: Name, host, vendor, device_type
- **SSH Parameters**: Authentication and connection settings
- **Template Overrides**: Per-device template specifications
- **Logging Configuration**: Configurable log paths

### 6. Utility Systems
- **Connection Parameters** (`utils/`): Netmiko parameter extraction
- **Template Validation** (`validate_templates.py`): Syntax and metadata validation
- **Diagnostics** (`diagnostics.py`): SSH connectivity and device troubleshooting

## Data Flow

### Plan Workflow
1. **Device Selection**: Filter devices by name or include all
2. **Template Resolution**: Priority order (CLI -> Inventory -> Default)
3. **Template Discovery**: Dynamic lookup and metadata extraction
4. **SSH Connectivity**: Test device reachability
5. **Configuration Rendering**: Apply device data to template
6. **Preview Generation**: Format and display planned changes
7. **Safety Analysis**: Check for hostname changes and unsafe operations

### Apply Workflow
1. **Plan Execution**: Complete plan workflow first
2. **User Confirmation**: Interactive approval (unless --force)
3. **Driver Selection**: Choose appropriate vendor-specific driver
4. **Configuration Execution**: Apply commands via Netmiko
5. **Error Handling**: Device-specific error recovery
6. **Result Reporting**: Success/failure with detailed output

## Security and Safety Features

### Template Safety System
- **Metadata Flags**: Templates self-declare safety characteristics
- **Hostname Detection**: Automatic detection of hostname-changing commands
- **Confirmation Prompts**: User approval for potentially risky operations
- **Safe Defaults**: Default templates designed to be minimally invasive

### Connection Security
- **SSH Key Support**: Public key authentication
- **Credential Isolation**: No hardcoded credentials
- **Session Logging**: Configurable audit trails
- **Timeout Management**: Prevent hanging connections

### Error Recovery
- **Graceful Failures**: Continue processing other devices on individual failures
- **Detailed Logging**: Comprehensive error reporting
- **State Recovery**: Ability to return devices to consistent state

## Extensibility Points

### Adding New Vendors
1. Create driver in `drivers/<vendor>.py` with `send_config(conn, config_set)` function
2. Add driver import and mapping in `main.py`
3. Create template directory `templates/<vendor>/`
4. Add default template with metadata

### Adding New Templates
1. Create `.j2` file in appropriate vendor directory
2. Add Jinja2 metadata comment with description and safety flags
3. Templates are automatically discovered and available

### Adding New Commands
1. Extend argument parser in `main.py`
2. Add command handling logic in main workflow
3. Follow existing patterns for error handling and output

## Performance Considerations

### Template Caching
- Templates discovered once per execution
- Metadata parsing cached
- Jinja2 template compilation cached by engine

### Connection Management
- Single SSH session per device per operation
- Configurable timeouts to prevent hanging
- Session reuse within single command execution

### Parallel Execution
- Currently sequential device processing
- Architecture supports future parallel implementation
- Thread-safe template discovery system

## MCP (Model Context Protocol) Readiness

### Structured Data Formats
- All configuration in YAML/JSON formats
- Template metadata in standardized comments
- Clear separation of data and logic

### API-Compatible Functions
- Each major operation is a discrete function
- Clear input/output contracts
- Minimal external dependencies per function

### State Management
- Stateless operation model
- All state in inventory files
- Idempotent operations where possible