# API Tests

This directory contains tests for the Flask API endpoints.

## User Routes Tests

`test_user_routes.py` contains comprehensive tests for all user management API endpoints defined in `app/routes/user_routes.py`.

### Test Approach

The tests use a mock-based approach that doesn't depend on the actual application code. This approach offers several benefits:

1. **Independence from implementation details**: Tests focus on API behavior rather than implementation.
2. **Faster test execution**: No database or external dependencies are required.
3. **Easier setup**: No need to mock complex dependencies.
4. **More robust tests**: Changes to internal implementation don't break tests as long as the API behavior remains consistent.

The key components:

- A dedicated Flask test application with mock route functions
- Mock schemas for validation
- No actual database connections

### Test Coverage

The tests cover:

- GET all users
- GET user by username (both query param and path)
- POST to create a new user
- PUT to update an existing user
- DELETE to remove a user
- PATCH to partially update a user
- Error handling for all endpoints

### Running the Tests

To run the tests, use pytest from the project root directory:

```bash
# Run all tests
pytest -v

# Run only user route tests
pytest -v tests/test_user_routes.py

# Run tests with coverage report
pytest --cov=app tests/
```

### Test Dependencies

The tests use pytest and Flask's test client to test the API endpoints in isolation.

## Requirements

- pytest
- pytest-cov (for coverage reports)
- Flask (test client)

Install the test dependencies with:

```bash
pip install pytest pytest-cov
```
