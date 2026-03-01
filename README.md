# TalentIntel Sentinel

OSINT-based talent intelligence monitoring system.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Initialize
sentinel init

# Add entity
sentinel add github_username --name "Name"

# List entities
sentinel list

# Check status
sentinel status ent_abc123

# Fetch data
sentinel fetch ent_abc123
```

## License

MIT
