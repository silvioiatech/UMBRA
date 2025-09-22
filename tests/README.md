# UMBRA Tests

This directory contains all test files for the UMBRA project.

## Test Structure

### Integration Tests
- `f4r2_integration_test.py` - F4R2 storage integration tests
- `f4r2_validate.py` - F4R2 validation tests
- `system_test.py` - System-wide integration tests

### Module Tests
- `test_ai_agent_f3r1.py` - AI agent tests
- `test_bot2.py` - Bot version 2 tests
- `test_bus1_business.py` - Business module tests
- `test_c2_update_watcher.py` - Update watcher tests
- `test_c3_instances.py` - Instance management tests
- `test_creator_pr_crt3.py` - Creator CRT3 tests
- `test_creator_pr_crt4.py` - Creator CRT4 tests
- `test_f1.py` - F1 feature tests
- `test_f2.py` - F2 feature tests
- `test_f3r1_integration.py` - F3R1 integration tests
- `test_f4r2_integration.py` - F4R2 integration tests
- `test_general_chat.py` - General chat tests
- `test_manifest_manager.py` - Manifest manager tests
- `test_mvp.py` - MVP tests
- `test_object_storage.py` - Object storage tests
- `test_openrouter.py` - OpenRouter tests
- `test_production_module.py` - Production module tests
- `test_r2_client.py` - R2 client tests
- `test_r2_storage.py` - R2 storage tests
- `test_router_f3r1.py` - Router F3R1 tests
- `test_search_index.py` - Search index tests

### Creator Module Tests
- `creator/test_creator_crt4.py` - Creator CRT4 specific tests

## Running Tests

### All Tests
```bash
python -m pytest tests/
```

### Specific Test Files
```bash
python -m pytest tests/test_specific_file.py
```

### Integration Tests
```bash
python tests/system_test.py
python tests/f4r2_integration_test.py
```

### With Coverage
```bash
python -m pytest tests/ --cov=umbra --cov-report=html
```

## Test Requirements

Make sure you have:
1. Environment variables configured (see `.env.example`)
2. Required dependencies installed (`pip install -r requirements.txt`)
3. Test dependencies installed (`pip install pytest pytest-cov`)

## Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test module interactions
- **System Tests**: Test the complete system
- **Validation Tests**: Validate specific features and configurations