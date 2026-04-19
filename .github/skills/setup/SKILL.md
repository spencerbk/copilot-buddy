---
name: setup
description: "Detect the project ecosystem and set up the development environment — install dependencies, create virtual environments, resolve packages, and verify the setup works."
---

# Project Setup

Detect the project's language ecosystem from marker files and run the appropriate setup commands to get a fully working development environment.

## Detection

Scan the repository root for ecosystem marker files. A project may have multiple ecosystems (e.g., a Tauri app with both `Cargo.toml` and `package.json`).

| Marker file | Ecosystem |
|-------------|-----------|
| `pyproject.toml` | Python |
| `setup.py` or `setup.cfg` (without `pyproject.toml`) | Python (legacy) |
| `requirements.txt` (without above) | Python (minimal) |
| `Cargo.toml` | Rust |
| `package.json` | TypeScript / JavaScript |
| `Package.swift` | Swift (SPM) |
| `.xcodeproj` or `.xcworkspace` directory | Swift (Xcode) |
| `go.mod` | Go |

If multiple ecosystems are detected, set up all of them and note the multi-ecosystem layout.

If the user provides an ecosystem hint (e.g., "setup python"), limit setup to that ecosystem.

## Python

### Virtual environment

1. Check if already inside a virtual environment (`VIRTUAL_ENV` is set).
2. If not, create and activate one:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   On Windows:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

### Dependencies

**`pyproject.toml` present (preferred path):**

1. Read `pyproject.toml` and inspect `[project.optional-dependencies]` for dev-related groups.
2. Common group names: `dev`, `test`, `lint`, `docs`, `typing`, `all`.
3. Install as editable with all dev-related groups:
   ```bash
   pip install -e ".[dev,test,lint]"
   ```
   Adapt the group names to what actually exists in the file. If a catch-all group (like `dev` or `all`) already includes the others, use just that one.
4. If no optional-dependency groups exist, install as editable:
   ```bash
   pip install -e .
   ```

**`setup.py` / `setup.cfg` present (legacy):**
```bash
pip install -e ".[dev]"    # try first; fall back to pip install -e . if no extras
```

**`requirements.txt` only:**
```bash
pip install -r requirements.txt
```
Also check for and install any of these if they exist:
- `requirements-dev.txt`
- `requirements-test.txt`
- `dev-requirements.txt`
- `test-requirements.txt`

### Verification

```bash
python --version && pip list | head -20
```

## Rust

1. Verify toolchain:
   ```bash
   rustc --version && cargo --version
   ```
2. Fetch and build:
   ```bash
   cargo build
   ```
3. If the project uses clippy (most do):
   ```bash
   rustup component add clippy 2>/dev/null; cargo clippy --version
   ```

## TypeScript / JavaScript

1. Detect package manager from lockfile:
   - `pnpm-lock.yaml` → use `pnpm`
   - `yarn.lock` → use `yarn`
   - `bun.lockb` → use `bun`
   - `package-lock.json` or no lockfile → use `npm`
2. Install dependencies:
   ```bash
   npm install    # or pnpm install / yarn install / bun install
   ```
3. If TypeScript is present (`tsconfig.json` exists), verify:
   ```bash
   npx tsc --version
   ```

## Swift

**Swift Package Manager (`Package.swift`):**
```bash
swift --version
swift package resolve
swift build
```

**Xcode project (`.xcodeproj` / `.xcworkspace`):**
```bash
xcodebuild -version
xcodebuild -resolvePackageDependencies
xcodebuild -list
```
Report available schemes so the user knows what to build/test.

## Go

```bash
go version
go mod download
go build ./...
```

## Output

After setup completes, report:
- Detected ecosystem(s)
- Key commands run and their pass/fail status
- Installed dependency count or summary (e.g., `pip list | wc -l` packages installed)
- Any warnings or issues encountered
- How to activate the environment if a venv was created
- A one-line "ready to go" confirmation or clear next step if something failed
