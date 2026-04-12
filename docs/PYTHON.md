# Python Setup for SlimZero v1

## Installation Summary

✅ **Python 3.12.0** has been installed and configured for this project.

### System Details

| Item | Value |
|------|-------|
| Version | 3.12.0 |
| Installation Path | `C:\Program Files\Python312` |
| PIP Version | 23.2.1 |
| Status | Ready to Use ✅ |

---

## Quick Start

### Verify Installation

```bash
python --version          # Should show: Python 3.12.0
python -m pip --version   # Should show: pip 23.2.1
```

### Create Virtual Environment

```bash
# Create venv in project
python -m venv venv

# Activate it
venv\Scripts\activate    # Windows
# or
source venv/bin/activate # macOS/Linux

# Deactivate later
deactivate
```

### Install Packages

```bash
# With venv activated
pip install flask
pip install requests
pip install pytest

# Or install from requirements.txt
pip install -r requirements.txt
```

---

## Project Configuration

### Python Configuration File

See `python.ini` in the project root for current settings.

### Requirements File

Create `requirements.txt` with your project dependencies:

```txt
flask==2.3.0
requests==2.31.0
pytest==7.4.0
python-dotenv==1.0.0
```

Then install all at once:
```bash
pip install -r requirements.txt
```

---

## Common Commands

```bash
# Show installed packages
pip list

# Search for a package
pip search flask

# Install specific version
pip install flask==2.3.0

# Upgrade a package
pip install --upgrade flask

# Uninstall a package
pip uninstall flask

# Freeze current dependencies
pip freeze > requirements.txt

# Show package info
pip show flask
```

---

## Python in Ralph & GSD

### Using Python with Ralph

Edit `scripts/ralph/prompt.md` to add Python-specific quality checks:

```bash
# Example quality checks for Python
python -m pytest              # Run tests
python -m mypy src/           # Type checking
python -m pylint src/         # Linting
python -m black --check src/  # Format check
```

### Using Python with GSD

GSD can invoke Python commands for testing and verification. Add to your GSD plan:

```
- Quality gates: pytest, mypy, pylint
- Runtime: Python 3.12
- Virtual environment: venv/
```

---

## Virtual Environments (Recommended)

Using a virtual environment isolates your project dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Now install packages (they go into venv, not system)
pip install flask
pip install pytest

# Deactivate when done
deactivate
```

Benefits:
- ✅ No conflicts with system packages
- ✅ Can have different versions per project
- ✅ Easier deployment (just copy `requirements.txt`)
- ✅ Cleaner system Python

---

## IDE/Editor Setup

### VS Code

1. Install Python extension
2. Ctrl+Shift+P → "Python: Select Interpreter"
3. Choose `./venv/bin/python` (or `./venv/Scripts/python` on Windows)
4. VS Code will auto-detect and use that environment

### Other Editors

Most modern editors can auto-detect Python virtual environments in the project root.

---

## Troubleshooting

### Python not found after installation

In a new terminal, run:
```powershell
$env:Path = "C:\Program Files\Python312;C:\Program Files\Python312\Scripts;$env:Path"
```

Or restart your terminal completely (Windows PATH changes sometimes require restart).

### Venv activation fails

On Windows PowerShell, you might need to enable scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try again:
```powershell
venv\Scripts\activate
```

### Pip not found

Use the module format instead:
```bash
python -m pip install flask
```

### Version conflicts

Use virtual environments to isolate versions:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Next Steps

1. ✅ Python 3.12 installed
2. → Create virtual environment: `python -m venv venv`
3. → Activate it: `venv\Scripts\activate`
4. → Create `requirements.txt` with your dependencies
5. → Install: `pip install -r requirements.txt`
6. → Add quality checks to `scripts/ralph/prompt.md`

---

## Resources

- [Python Official Docs](https://docs.python.org/3.12/)
- [PIP Documentation](https://pip.pypa.io/)
- [Virtual Environments Guide](https://docs.python.org/3.12/tutorial/venv.html)
- [PyPI (Package Index)](https://pypi.org/)

---

**Python Version:** 3.12.0  
**Setup Date:** 2026-04-11  
**Status:** ✅ Ready
