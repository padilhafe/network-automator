# Network Automator - AI Integration Documentation

## Purpose
This `.ai` directory contains comprehensive documentation designed to help AI assistants, Large Language Models (LLMs), and Model Context Protocol (MCP) implementations understand and interact with the Network Automator effectively.

## Directory Contents

### Core Documentation Files

#### `project-overview.md`
High-level overview of the Network Automator including:
- Project purpose and philosophy
- Architecture summary
- Key features and capabilities
- Technology stack
- Current status

#### `architecture.md`
Detailed technical architecture documentation covering:
- System component diagrams
- Data flow descriptions
- Component responsibilities
- Security mechanisms
- Extensibility points
- Performance considerations

#### `api-guide.md`
Comprehensive API reference for programmatic integration:
- Core function signatures and usage
- Data structure schemas
- MCP function mappings
- Integration examples
- Safety considerations
- Environment requirements

#### `troubleshooting.md`
Complete troubleshooting guide including:
- Common issues and solutions
- Diagnostic procedures
- Error recovery steps
- Best practices
- Emergency procedures
- Performance optimization

#### `development-guide.md`
Developer documentation for extending the framework:
- Development environment setup
- Adding new vendors and drivers
- Template development guidelines
- Testing procedures
- Code quality standards
- Contributing guidelines

#### `mcp-context.md`
Specialized documentation for MCP integration:
- Framework identity and capabilities
- Safe vs dangerous operations
- Recommended function interfaces
- Current system state
- Operational considerations

## Target Audiences

### AI Assistants and LLMs
These documents provide the context needed to:
- Understand system capabilities and limitations
- Suggest appropriate commands and workflows
- Help troubleshoot issues
- Explain system behavior to users
- Generate safe operational recommendations

### MCP Implementations
Documentation specifically covers:
- Function interface specifications
- Safety mechanism requirements
- Data structure schemas
- Integration best practices
- Error handling patterns

### Future AI Systems
The documentation is designed to be:
- Comprehensive and self-contained
- Structured for machine parsing
- Forward-compatible with emerging AI protocols
- Clear about safety boundaries and requirements

## Usage Guidelines

### For AI Systems
1. **Start with `mcp-context.md`** for quick system understanding
2. **Reference `api-guide.md`** for specific function implementations
3. **Use `troubleshooting.md`** when users report issues
4. **Consult `architecture.md`** for deep technical questions
5. **Check `development-guide.md`** for extension requirements

### For Human Developers
- These files serve as comprehensive technical documentation
- Use as reference for system architecture decisions
- Follow patterns established in API guide for new integrations
- Reference troubleshooting guide for operational issues

## Integration Principles

### Safety First
- All dangerous operations require explicit confirmation
- Plan-before-apply workflow is mandatory
- Template safety metadata must be respected
- SSH connectivity must be validated before configuration changes

### Professional Operation
- Clear error messages and status reporting
- Comprehensive logging and audit trails
- Graceful error handling and recovery
- Terraform-like user experience patterns

### Extensibility
- New vendors and templates can be added dynamically
- System discovers capabilities from filesystem
- No hardcoded limitations or vendor restrictions
- Plugin-style architecture for drivers and templates

## Maintenance

### Keeping Documentation Current
- Update when adding new features or capabilities
- Maintain accuracy of API signatures and data structures
- Document breaking changes and migration paths
- Include new troubleshooting scenarios as they arise

### Version Compatibility
- Documentation tracks with codebase changes
- Breaking changes are clearly marked
- Backward compatibility considerations are documented
- Migration guides provided for major version changes

## Quick Reference

### Most Important Files for AI Integration
1. `mcp-context.md` - Essential system understanding
2. `api-guide.md` - Function interfaces and usage
3. `troubleshooting.md` - Problem resolution

### Key Safety Rules for AI Systems
- Never apply configurations without explicit user confirmation
- Always run `plan` before suggesting `apply` operations  
- Validate SSH connectivity before configuration attempts
- Respect template safety metadata and warnings
- Use appropriate timeout values for network operations

### Essential Commands for AI to Understand
```bash
nacli list                    # Safe: List available devices
nacli templates               # Safe: Show available templates  
nacli check [device]          # Safe: Test SSH connectivity
nacli plan [device]           # Safe: Preview configuration changes
nacli apply [device] --force  # DANGEROUS: Apply without confirmation
nacli apply [device]          # DANGEROUS: Apply with confirmation
```

This documentation enables AI systems to provide intelligent, safe, and effective assistance with network automation tasks while maintaining the security and reliability standards expected in enterprise network operations.

## Important Guidelines for AI Systems

### Documentation Standards
- **Keep it practical**: Focus on functionality and usage, not project history
- **Avoid redundant files**: No migration guides, refactoring summaries, or changelog documents
- **No meta-documentation**: Don't create documentation about documentation
- **Focus on user value**: Only document what users actually need to know
- **Maintain relevance**: Update existing docs rather than creating new ones for minor changes

### What NOT to create:
- Migration guides (users can read git history)
- Refactoring summaries (internal development details)
- Detailed changelogs (use git commits)
- Multiple README files for the same purpose
- Documentation about documentation processes