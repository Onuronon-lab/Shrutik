# Contributing to Shrutik

Thank you for your interest in contributing to Shrutik! This guide will help you get started with contributing to our open-source voice data collection platform.

## Ways to Contribute

### Voice Data Contribution
- **Record Voice Samples**: Contribute voice recordings in your native language
- **Transcribe Audio**: Help transcribe audio clips to improve dataset quality
- **Quality Review**: Review and validate transcriptions from other contributors
- **Language Support**: Help add support for new languages and dialects

### Code Contribution
- **Bug Fixes**: Fix reported issues and improve stability
- **Feature Development**: Implement new features and enhancements
- **Performance Optimization**: Improve system performance and scalability
- **Testing**: Write and improve test coverage
- **Documentation**: Improve code documentation and API references

### Documentation
- **User Guides**: Improve setup and usage documentation
- **Developer Docs**: Enhance technical documentation
- **Translations**: Translate documentation to other languages
- **Tutorials**: Create tutorials and examples

### Design & UX
- **UI/UX Improvements**: Enhance user interface and experience
- **Accessibility**: Improve accessibility features
- **Mobile Responsiveness**: Optimize for mobile devices
- **Branding**: Improve visual design and branding

## Getting Started

### 1. Set Up Development Environment

Follow our [Local Development Guide](https://onuronon-lab.github.io/Shrutik/local-development.html) to set up your development environment. also you can setup with docker as well. See [Docker Local Setup](https://onuronon-lab.github.io/Shrutik/docker-local-setup.html)

### 2. Find an Issue

- Browse [open issues](https://github.com/Onuronon-lab/Shrutik/issues)
- Look for issues labeled `good first issue` for beginners
- Check issues labeled `help wanted` for areas needing assistance
- Join our [Discord](https://discord.gg/9hZ9eW8ARk) to discuss ideas

### 3. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/shrutik.git
cd shrutik

# Add upstream remote
git remote add upstream https://github.com/Onuronon-lab/Shrutik.git
```

## Development Workflow

### 1. Create a Branch

**Important:** All PRs must be submitted to the `deployment-dev` branch, not `master`.

```bash
# Update deployment-dev branch
git checkout deployment-dev
git pull origin deployment-dev

# Create a feature branch
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b fix/issue-number-description
```

### 2. Make Changes

- Write code
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add voice recording validation

- Add audio quality validation
- Implement duration checks
- Add error handling for invalid formats
- Update tests and documentation

Fixes #123"
```

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create a Pull Request to deployment-dev on GitHub
```

**PR Guidelines:**
- Target the `deployment-dev` branch (not master!)
- Fill out the PR template completely
- Ensure all CI checks pass
- Code must be formatted (see Code Formatting section)

---

## Code Formatting

We use automated code formatters to maintain consistent code style and eliminate formatting-related merge conflicts.

### Tools & Configuration

- **Backend (Python)**: Black (88 chars), isort, flake8
- **Frontend (TypeScript/React)**: Prettier (100 chars), ESLint

### Quick Setup

**1. Install formatting tools:**

```bash
pip install black isort flake8
cd frontend && npm install && cd ..
```

**2. Set up pre-commit hooks (recommended):**

```bash
./scripts/setup_pre_commit.sh
```

This auto-formats your code on every commit!

### Using Pre-commit Hooks

Once set up, just commit normally:

```bash
git add .
git commit -m "feat: your changes"
# ✨ Code is automatically formatted before commit!
```

### Before Submitting a PR

If not using pre-commit hooks, format manually:

```bash
# Format entire codebase
./scripts/format_code.sh

# Review changes
git diff

# Commit and push
git add .
git commit -m "style: format code"
git push
```

### Manual Formatting Commands

```bash
# Format everything
./scripts/format_code.sh

# Backend only
black app/ tests/ scripts/
isort app/ tests/ scripts/

# Frontend only
cd frontend
npm run format
npm run lint:fix
```

### CI/CD Checks

Our GitHub Actions workflow automatically checks formatting on all PRs to deployment-dev. If formatting fails:

```bash
./scripts/format_code.sh
git add .
git commit -m "style: fix formatting"
git push
```

### Skipping Hooks (Emergency Only)

```bash
git commit --no-verify -m "emergency fix"
```

**Note:** Use sparingly! The CI will still check formatting.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Tools not found | `pip install black isort flake8` |
| Prettier not found | `cd frontend && npm install` |
| Hooks not running | `pre-commit install` |

### Style Guidelines

#### Python
```python
# ✅ Good (Black formatted)
def calculate_total(items: list[dict], tax_rate: float = 0.1) -> float:
    """Calculate total with tax."""
    subtotal = sum(item["price"] for item in items)
    return subtotal * (1 + tax_rate)
```

#### TypeScript/React
```typescript
// ✅ Good (Prettier formatted)
const UserCard = ({ name, email }: UserCardProps) => {
  return (
    <div className="user-card">
      <h2>{name}</h2>
      <p>{email}</p>
    </div>
  );
};
```

---

**Benefits:**
- ✅ Zero formatting conflicts in PRs
- ✅ Faster code reviews (focus on logic)
- ✅ Consistent codebase
- ✅ Automatic on every commit

For more details, see [docs/FORMATTING.md](docs/FORMATTING.md)

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(auth): add OAuth2 authentication
fix(api): resolve transcription submission error
docs(readme): update installation instructions
test(voice): add unit tests for audio processing
```

## Testing Guidelines

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test

# Integration tests
pytest tests/integration/

# E2E tests
cd frontend && npm run test:e2e
```

### Writing Tests

#### Backend Tests (Python)

```python
# tests/test_transcription.py
import pytest
from app.services.transcription_service import TranscriptionService

def test_create_transcription(db_session):
    """Test transcription creation."""
    service = TranscriptionService(db_session)
    transcription = service.create_transcription(
        chunk_id=1,
        user_id=1,
        text="Test transcription"
    )
    assert transcription.text == "Test transcription"
```

#### Frontend Tests (TypeScript/Jest)

```typescript
// frontend/src/__tests__/VoiceRecorder.test.tsx
import { render, screen } from '@testing-library/react';
import VoiceRecorder from '../components/VoiceRecorder';

test('renders voice recorder component', () => {
  render(<VoiceRecorder />);
  const recordButton = screen.getByRole('button', { name: /record/i });
  expect(recordButton).toBeInTheDocument();
});
```

### Test Coverage

- Maintain minimum 80% test coverage
- Write tests for all new features
- Include edge cases and error scenarios
- Test both happy path and error conditions

## Coding Standards

### Python (Backend)

#### Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [flake8](https://flake8.pycqa.org/) for linting

```bash
# Format code
black app/
isort app/

# Check linting
flake8 app/
```

#### Code Structure

```python
# Good: Clear function with type hints and docstring
from typing import Optional
from sqlalchemy.orm import Session

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve user by email address.
    
    Args:
        db: Database session
        email: User email address
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()
```

#### Error Handling

```python
# Good: Specific exception handling
try:
    user = create_user(db, user_data)
except ValidationError as e:
    logger.error(f"User validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### TypeScript/React (Frontend)

#### Code Style

- Use [Prettier](https://prettier.io/) for code formatting
- Use [ESLint](https://eslint.org/) for linting
- Follow React best practices
- Use TypeScript for type safety

```bash
# Format code
npm run format

# Check linting
npm run lint
```

#### Component Structure

```typescript
// Good: Typed React component with proper structure
interface VoiceRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  maxDuration?: number;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onRecordingComplete,
  maxDuration = 60
}) => {
  const [isRecording, setIsRecording] = useState(false);
  
  // Component logic here
  
  return (
    <div className="voice-recorder">
      {/* JSX here */}
    </div>
  );
};
```

### Database

#### Migrations

```python
# Good: Clear migration with proper naming
"""Add voice quality metrics

Revision ID: 001_add_voice_quality
Revises: 000_initial
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('transcriptions', 
        sa.Column('quality_score', sa.Float, nullable=True))

def downgrade():
    op.drop_column('transcriptions', 'quality_score')
```

## Documentation Standards

### Code Documentation

- Use clear, descriptive docstrings
- Document all public functions and classes
- Include parameter types and return values
- Provide usage examples for complex functions

### API Documentation

- Use OpenAPI/Swagger annotations
- Document all endpoints, parameters, and responses
- Include example requests and responses
- Document error codes and messages

### User Documentation

- Write clear, step-by-step instructions
- Include screenshots and examples
- Test all instructions on a fresh environment
- Keep documentation up-to-date with code changes

## Code Review Process

### Submitting a Pull Request

1. **Title**: Clear, descriptive title
2. **Description**: Explain what and why
3. **Testing**: Describe how you tested the changes
4. **Screenshots**: Include for UI changes
5. **Breaking Changes**: Document any breaking changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Criteria

Reviewers will check for:

- **Functionality**: Does the code work as intended?
- **Code Quality**: Is the code clean and maintainable?
- **Testing**: Are there adequate tests?
- **Documentation**: Is documentation updated?
- **Performance**: Are there any performance implications?
- **Security**: Are there any security concerns?

## Internationalization

### Adding New Languages

1. **Language Configuration**: Add language to `app/models/language.py`
2. **Frontend Translations**: Add translations to `frontend/src/locales/`
3. **Backend Messages**: Update error messages and notifications
4. **Documentation**: Translate key documentation

### Translation Guidelines

- Use proper Unicode support for all scripts
- Test with right-to-left languages
- Consider cultural context in translations
- Use native speakers for translation review

## 🎤 Voice Data Guidelines

### Recording Quality

- **Environment**: Quiet, echo-free environment
- **Equipment**: Good quality microphone
- **Format**: WAV or high-quality MP3
- **Duration**: 2-10 seconds per clip
- **Content**: Clear, natural speech

### Transcription Guidelines

- **Accuracy**: Transcribe exactly what is spoken
- **Formatting**: Follow language-specific conventions
- **Punctuation**: Include appropriate punctuation
- **Quality Rating**: Rate audio quality honestly

## Recognition

### Contributor Recognition

- Contributors are listed in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file
- Significant contributors may be invited to join the core team
- We highlight contributions in our release notes
- Annual contributor appreciation events

### Badges and Achievements

- First-time contributor badge
- Language champion badges
- Code contributor levels
- Community helper recognition

## Getting Help

### Community Support

- **Discord**: [Join our server](https://discord.gg/9hZ9eW8ARk) for real-time help
- **GitHub Discussions**: Ask questions and share ideas
- **Office Hours**: Weekly community calls (schedule in Discord)

### Mentorship Program

- New contributors can request mentorship
- Experienced contributors can volunteer as mentors
- Structured onboarding for major contributions

### Contact

- **General Questions**: community@shrutik.org
- **Technical Issues**: dev@shrutik.org
- **Security Issues**: security@shrutik.org (private)

## 📜 Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

### Our Standards

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Collaborative**: Work together towards common goals
- **Be Patient**: Help others learn and grow

## 📄 License

By contributing to Shrutik, you agree that your contributions will be licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](../LICENSE). This ensures that all contributions remain available for educational and non-commercial use while requiring attribution to the original creators.

---

Thank you for contributing to Shrutik! Together, we're building a more inclusive digital future. 🎉