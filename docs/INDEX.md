# DocXP Documentation Index

## Essential Documentation

### Getting Started
- **[Quick Start Guide](QUICK_START.md)** - Fast setup for developers
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### Technical Documentation  
- **[Architecture Overview](architecture.md)** - System architecture and design
- **[Project Instructions](../CLAUDE.md)** - Development guidelines and context
- **[Current Tasks](../TODO.md)** - Active development roadmap

## Project Structure

```
docxp/
├── README.md              # Project overview
├── docs/                  # Essential documentation
├── backend/               # FastAPI application
├── frontend/              # Angular UI application  
├── scripts/               # Deployment scripts
├── tools/                 # Utility scripts
├── tests/                 # Sample test data
├── archive/               # Archived files and old documentation
│   ├── documentation/     # Old documentation files
│   ├── testing/           # Test and validation scripts
│   ├── reviews/           # Reports and reviews
│   ├── backups/           # Database backups
│   └── legacy/            # Legacy scripts and configs
└── docker-compose.yml     # Container orchestration
```

## Deployment Options

- **Development**: `podman-compose up -d` (recommended)
- **Production**: `docker-compose up -d`  
- **Quick Start**: `./start.sh` (Linux/Mac) or `start.bat` (Windows)

## Support

- Check [Troubleshooting Guide](TROUBLESHOOTING.md) first
- Review [Deployment Guide](DEPLOYMENT_GUIDE.md) for setup issues
- See archived documentation in `archive/` for historical context