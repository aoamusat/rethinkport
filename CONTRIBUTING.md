# Contributing to RethinkPort 🚢

Thank you for your interest in contributing to RethinkPort! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- MySQL 5.7+ or MariaDB 10.2+
- Git

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/rethinkport.git
   cd rethinkport
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8 isort
   ```

5. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes in the appropriate files
2. Add or update tests as needed
3. Update documentation if necessary
4. Ensure your code follows the project's style guidelines

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **flake8** for linting
- **isort** for import sorting

Run these tools before committing:

```bash
# Format code
black .

# Sort imports
isort .

# Check for linting issues
flake8 .
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=rethinkdb_mysql_migrator

# Run specific test file
pytest tests/test_migrator.py

# Run tests in verbose mode
pytest -v
```

### Testing with MySQL

For integration testing, you'll need a MySQL instance:

```bash
# Using Docker
docker run --name test-mysql -e MYSQL_ROOT_PASSWORD=test_password -e MYSQL_DATABASE=test_db -p 3306:3306 -d mysql:8.0

# Set environment variables
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=test_password
export MYSQL_DATABASE=test_db

# Run tests
pytest
```

## Submitting Changes

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for custom data type mappings

- Allow users to specify custom type mappings in config
- Add validation for custom type definitions
- Update documentation with examples
```

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add entries to CHANGELOG.md if applicable
4. Submit a pull request with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots if UI changes are involved

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## Types of Contributions

### Bug Reports

When reporting bugs, please include:

- Python version
- MySQL version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Sample data (if applicable)

### Feature Requests

For new features, please:

- Check existing issues first
- Describe the use case
- Explain why it would be valuable
- Consider implementation complexity
- Provide examples if possible

### Code Contributions

Areas where contributions are especially welcome:

- **Performance improvements**: Optimize data processing and insertion
- **Data type support**: Add support for additional RethinkDB/MySQL types
- **Error handling**: Improve error messages and recovery
- **Documentation**: Examples, tutorials, API documentation
- **Testing**: More comprehensive test coverage
- **Configuration**: Additional configuration options

## Code Organization

```
rethinkdb_mysql_migrator/
├── __init__.py          # Package initialization
├── migrator.py          # Core migration logic
├── cli.py              # Command-line interface
└── __main__.py         # Package entry point

tests/
├── test_migrator.py    # Core functionality tests
└── test_cli.py         # CLI tests

examples/
├── config.json         # Sample configuration
└── migration_example.md # Usage examples
```

## Key Components

### RethinkDBMigrator Class

The main migration class handles:
- Data type analysis and schema inference
- MySQL table creation
- Data conversion and insertion
- Progress tracking and error handling

### CLI Module

Command-line interface providing:
- Argument parsing
- Configuration management
- User-friendly output

## Performance Considerations

When contributing performance improvements:

- Profile code to identify bottlenecks
- Consider memory usage for large datasets
- Test with various data sizes
- Document performance characteristics

## Documentation

### Code Documentation

- Use clear docstrings for all functions/classes
- Include parameter types and return values
- Provide usage examples for complex functions

### User Documentation

- Update README.md for new features
- Add examples to examples/ directory
- Update configuration documentation

## Release Process

1. Update version in `setup.py` and `__init__.py`
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Create GitHub release
6. Publish to PyPI (maintainers only)

## Getting Help

- Check existing issues and documentation
- Ask questions in GitHub Discussions
- Join our community chat (if available)
- Contact maintainers for complex issues

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to make database migration easier for everyone.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

Thank you for contributing to RethinkDB MySQL Migrator!
