# UMBRA Scripts

This directory contains utility scripts and setup files for the UMBRA project.

## Contents

### Setup Scripts
- `setup.sh` - Main setup script for the project
- `setup_creator.sh` - Creator module specific setup
- `start_mvp.sh` - Script to start the MVP version

### Utility Scripts
- `creator_examples.py` - Examples for using the Creator module
- `fix_type_hints.py` - Script to fix Python type hints

## Usage

### Setup
To set up the project:
```bash
cd scripts
chmod +x setup.sh
./setup.sh
```

### Creator Setup
For Creator module specific setup:
```bash
cd scripts
chmod +x setup_creator.sh
./setup_creator.sh
```

### Start MVP
To start the MVP version:
```bash
cd scripts
chmod +x start_mvp.sh
./start_mvp.sh
```

### Utilities
To run utility scripts:
```bash
cd scripts
python creator_examples.py
python fix_type_hints.py
```

## Notes

Make sure you have the proper environment variables configured before running setup scripts. See the main project README for environment configuration details.