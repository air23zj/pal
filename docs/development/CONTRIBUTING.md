# Contributing to Morning Brief AGI

Thank you for your interest in contributing to Morning Brief AGI!

## Development Setup

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd pal

# Option 1: Using Docker (Recommended)
make up

# Option 2: Local development
make install
make dev
```

### Code Style

- **Python**: We use Black for formatting and Ruff for linting
- **TypeScript**: We use Prettier and ESLint

```bash
# Format code
make format

# Lint code
make lint
```

### Testing

```bash
# Run all tests
make test

# Run specific tests
make test-backend
make test-frontend
```

## Project Structure

- `backend/`: FastAPI application
  - `apps/api/`: API endpoints
  - `packages/`: Reusable packages (connectors, memory, ranking, etc.)
- `frontend/`: Next.js application
- `tests/`: Integration tests
- `docs/`: Documentation

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Format code (`make format`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Coding Guidelines

### Backend (Python)

- Use type hints
- Follow Pydantic schemas for data validation
- Write docstrings for public functions
- Keep functions focused and small
- Add tests for new features

### Frontend (TypeScript)

- Use TypeScript strictly (avoid `any`)
- Create reusable components
- Follow the established component structure
- Use Tailwind for styling
- Keep components focused and composable

## Data Contracts

**IMPORTANT**: The data contracts defined in `backend/packages/shared/schemas.py` and `frontend/src/types/brief.ts` must stay in sync.

When modifying schemas:
1. Update Python schema first
2. Update TypeScript types to match
3. Update API documentation
4. Test both backend and frontend

## Commit Messages

Use conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

Example: `feat: add LinkedIn agent integration`

## Questions?

Open an issue or reach out to the maintainers.

Thank you for contributing! 🎉
