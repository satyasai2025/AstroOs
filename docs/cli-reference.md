# AstroOS CLI Reference — v2.3.0

## astroos-plugin

Local-first plugin management. No hosted marketplace.

```bash
# List available plugins from bundled registry
astroos-plugin list

# List installed plugins
astroos-plugin list-installed

# Install a plugin (from registry URL)
astroos-plugin install example-calculator

# Uninstall a plugin
astroos-plugin uninstall example-calculator

# Scaffold a new plugin project
astroos-plugin scaffold my-plugin

# Validate a plugin manifest
astroos-plugin validate ./my-plugin
```

Plugin registry: `plugins/registry.json`
Installed plugins: `~/.astroos/plugins/`

## astroos data

Research data privacy tools.

```bash
# Export all data
astroos data export --output ./astroos-export.zip

# Delete all data
astroos data delete --confirm

# Anonymize a project
astroos data anonymize --project <id> --output ./anonymized.json

# Clear computation cache
astroos data clean-cache
```
