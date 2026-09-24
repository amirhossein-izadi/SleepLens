# Git Workflow & Branching Strategy

> Production-ready Git workflow with pre-commit hooks and branch management.

---

## Branch Strategy

```
main (production-ready)
│
└── develop (integration branch)
    │
    ├── feature/feature-name
    ├── bugfix/issue-description
    ├── hotfix/production-issue
    └── release/version-number
```

### Branch Types

| Branch | Purpose | Base | Merges To |
|--------|---------|------|-----------|
| `main` | Production code | - | - |
| `develop` | Integration | main | main |
| `feature/*` | New features | develop | develop |
| `bugfix/*` | Bug fixes | develop | develop |
| `hotfix/*` | Production fixes | main | main & develop |
| `release/*` | Release preparation | develop | main & develop |

---

## Naming Conventions

```bash
# Features
feature/user-authentication
feature/appointment-booking
feature/ai-report-generation

# Bugfixes
bugfix/login-redirect-issue
bugfix/date-picker-timezone

# Hotfixes
hotfix/security-patch
hotfix/payment-failure

# Releases
release/v1.2.0
release/v2.0.0-rc1
```

---

## Commit Messages

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no feature change)
- `docs`: Documentation only
- `style`: Formatting, no code change
- `test`: Adding/updating tests
- `chore`: Maintenance, dependencies
- `perf`: Performance improvement
- `ci`: CI/CD changes

### Examples

```bash
# Good commit messages
feat(appointments): add booking confirmation email
fix(auth): resolve token expiration handling
docs(api): update endpoint documentation
refactor(patients): extract validation to service layer
hotfix(security): patch SQL injection vulnerability

# Bad commit messages
fix stuff
update
WIP
```

---

## Workflow Steps

### Starting a Feature

```bash
# 1. Update develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/user-appointments

# 3. Work and commit
git add .
git commit -m "feat(appointments): add appointment model"

# 4. Push and create PR
git push -u origin feature/user-appointments
```

### Merging Changes

```bash
# 1. Rebase on develop (preferred)
git fetch origin
git rebase origin/develop

# 2. Force push (if needed)
git push --force-with-lease

# 3. Create Pull Request
# Review, tests pass, then merge
```

### Hotfix Process

```bash
# 1. Create hotfix from main
git checkout main
git pull main
git checkout -b hotfix/critical-fix

# 2. Fix and commit
git add .
git commit -m "hotfix: fix critical issue"

# 3. Merge to main
git checkout main
git merge --no-ff hotfix/critical-fix
git push origin main

# 4. Merge to develop
git checkout develop
git merge --no-ff hotfix/critical-fix
git push origin develop

# 5. Delete hotfix branch
git branch -d hotfix/critical-fix
```

---

## Pre-commit Hooks (Your Project)

Your project already has pre-commit configured. Never modify this rule.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: check-merge-conflict
      - id: check-yaml
      - id: trailing-whitespace
      - id: detect-private-key
      
  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
      
  - repo: https://github.com/psf/black
    hooks:
      - id: black
      
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
```

### Running Hooks

```bash
# Install hooks
make hooks

# Run manually
make hooks-run

# Or manually
pre-commit install
pre-commit run --all-files
```

---

## What NOT to Commit

### Critical Rules

```bash
# ❌ NEVER commit migrations folder content (except __init__.py)
# Your .gitignore already handles this:
**/migrations/*.py
!**/migrations/__init__.py

# ❌ NEVER commit .env files
.env
.env.*

# ❌ NEVER commit secrets, keys, tokens
*.pem
*.key
secrets/
credentials/
```

### Your .gitignore Patterns

```
# Database
*.sqlite3
db.sqlite3

# Python
*.pyc
__pycache__/
*.log

# Virtual Environment
.venv/
uv.lock
.uv/

# Environment files
.env
.env.*

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Media
media/
staticfiles/
medical/*

# Test/Cache
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage
```

---

## Makefile Commands

```bash
# Code quality
make format        # Run black, isort, ruff
make lint          # Run ruff only

# Testing
make test          # Run all tests
make test-app APP=accounts  # Test specific app

# Database
make migrate       # Run migrations
make mm APP=accounts  # Make migrations for app

# Docker
make up            # Start dev environment
make down          # Stop dev environment
make logs          # View logs

# Git
make hooks         # Install pre-commit
make hooks-run     # Run pre-commit
```

---

## Pull Request Best Practices

### Before Creating PR

- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] No linting errors (`make lint`)
- [ ] Pre-commit hooks pass (`make hooks-run`)
- [ ] Branch is rebased on latest develop

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Feature
- [ ] Bug Fix
- [ ] Refactor
- [ ] Documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
```

---

## Handling Conflicts

```bash
# 1. Update develop
git checkout develop
git pull origin develop

# 2. Rebase your branch
git checkout feature/your-branch
git rebase develop

# 3. Resolve conflicts if any
# Edit conflicted files, then:
git add .
git rebase --continue

# 4. Force push (if needed)
git push --force-with-lease
```

---

## Release Process

```bash
# 1. Create release branch
git checkout develop
git pull develop
git checkout -b release/v1.2.0

# 2. Update version
# Bump version in settings/__init__.py or pyproject.toml

# 3. Test and fix any issues

# 4. Merge to main
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# 5. Merge back to develop
git checkout develop
git merge --no-ff release/v1.2.0
git push origin develop

# 6. Delete release branch
git branch -d release/v1.2.0
```

---

*Related: [07_CI_CD.md](07_CI_CD.md), [01_PROJECT_STRUCTURE.md](01_PROJECT_STRUCTURE.md)*