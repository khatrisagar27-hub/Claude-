# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

**This repository is currently empty** — no source code, build configuration, tests, or tooling have been added yet. Only this documentation file exists alongside the git history.

Current state (as of 2026-06-13):
- No programming language or framework selected
- No package manager or dependency manifest
- No build, lint, or test scripts
- No CI/CD pipeline
- Single branch history off `main`

---

## Bootstrapping a New Project

When starting a project in this repo, the first step is to decide the language and framework, then scaffold accordingly. Common starting points:

### Node.js / TypeScript
```bash
npm init -y
npm install typescript --save-dev
npx tsc --init
```

### Python
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# then: pip install <dependencies> && pip freeze > requirements.txt
# or: use pyproject.toml + poetry/uv
```

### Other runtimes
Use the appropriate package manager and init command for the chosen stack.

After bootstrapping, **update this file** with the sections below filled in.

---

## Build & Test Commands

> **TODO:** Fill in once the project is initialized.

| Task | Command |
|------|---------|
| Install dependencies | `<command>` |
| Run all tests | `<command>` |
| Run a single test | `<command>` |
| Lint | `<command>` |
| Type-check | `<command>` |
| Build / compile | `<command>` |
| Start dev server | `<command>` |

---

## Architecture Overview

> **TODO:** Fill in once source code exists.

Describe:
- Top-level directory layout and the purpose of each directory
- Data flow and key module boundaries
- Core abstractions and where they live
- External services or APIs the project depends on

---

## Project Conventions

> **TODO:** Fill in once conventions are established.

Typical things to document here:
- Naming conventions (files, variables, exports)
- Code organization rules (where new modules go, how to add a feature)
- Commit message format (e.g., Conventional Commits)
- Branch naming strategy
- PR/review process expectations
- Environment variable naming and where they are documented

---

## Git Workflow

- **Development branch convention:** feature branches follow `<type>/<short-description>` (e.g., `feat/user-auth`, `fix/login-bug`)
- **Never push directly to `main`** without a pull request unless explicitly instructed
- Write clear commit messages focused on *why*, not *what* — the diff shows what changed
- Do not amend commits that have already been pushed

---

## AI Assistant Guidelines

When working in this repository as an AI assistant:

1. **Check this file first** before making assumptions about conventions or tooling.
2. **Do not add features or refactor** beyond what the task explicitly requests.
3. **Do not add error handling** for scenarios that cannot happen in the current codebase.
4. **Default to no comments** in code — only add a comment when the reasoning is non-obvious.
5. **Prefer editing existing files** over creating new ones.
6. **Test before reporting complete** — for UI/server changes, verify the golden path works.
7. **Confirm before destructive actions** — force pushes, dropping data, deleting branches.
8. **Keep this file current** — after any significant structural change, update the relevant sections above.
