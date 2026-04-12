# Virtual Environment Setup - Complete Guide

## ✅ Status: WORKING!

Your Python 3.12 virtual environment is now fully set up and ready to use.

---

## What's Installed

### Core Packages (29 total)

**Web Framework:**
- Flask 3.1.3
- flask-cors 6.0.2

**Utilities:**
- requests 2.33.1
- python-dotenv 1.2.2
- python-json-logger 4.1.0

**Testing & Development:**
- pytest 9.0.3
- pytest-cov 7.1.0
- flake8 7.3.0

**Plus 15+ dependencies** (blinker, Jinja2, Werkzeug, colorama, etc.)

---

## Quick Start - Activate Venv

### Windows PowerShell

```powershell
# In your project directory
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
(venv) PS C:\Users\...\SlimZero v1>
```

### Windows Command Prompt (cmd.exe)

```cmd
venv\Scripts\activate.bat
```

### macOS/Linux (if you copy this project)

```bash
source venv/bin/activate
```

### Deactivate (when done)

```powershell
deactivate
```

---

## Using Python in Your Project

Once venv is activated:

```powershell
# Run Python
python --version

# Run a script
python my_script.py

# Start interactive Python shell
python

# Use pip to install more packages
pip install package_name
```

---

## Installing Additional Packages

If you need packages that require C++ compilation (pydantic, sqlalchemy, mypy, black):

### Option 1: Install Visual C++ Build Tools (Recommended)

1. Download: https://visualstudio.microsoft.com/downloads/
2. Choose "Build Tools for Visual Studio"
3. During installation, check: "Desktop development with C++"
4. Restart your terminal
5. Uncomment packages in `requirements.txt`
6. Run: `pip install -r requirements.txt`

### Option 2: Use Pre-built Wheels (Faster)

Some packages have pre-built wheels available. Try:

```powershell
# Example: Install pydantic with pre-built wheel
pip install --only-binary :all: pydantic
```

### Option 3: Skip Compilation-Heavy Packages

Use alternatives:
- Instead of `pydantic` → use `dataclasses` (Python stdlib)
- Instead of `sqlalchemy` → use `sqlite3` (Python stdlib) or `peewee`
- Instead of `mypy` → use `pylint` or `flake8` (already installed)

---

## Project Structure

```
SlimZero v1/
├── venv/                    # Virtual environment (DO NOT EDIT)
│   ├── Scripts/             # Python executables
│   │   ├── python.exe
│   │   ├── pip.exe
│   │   └── activate.ps1
│   ├── Lib/                 # Installed packages
│   └── Include/             # Headers
│
├── requirements.txt         # Package list (edit to add more)
├── python.ini               # Python configuration
├── docs/PYTHON.md           # Python documentation
└── [your code files]
```

---

## Common Commands

```powershell
# List installed packages
pip list

# Show package details
pip show flask

# Install a specific version
pip install flask==2.0.0

# Upgrade a package
pip install --upgrade flask

# Uninstall a package
pip uninstall flask

# Export current packages to requirements.txt
pip freeze > requirements.txt

# Install from requirements file
pip install -r requirements.txt
```

---

## Troubleshooting

### "Cannot find python command"

**Issue:** `python: command not found`

**Solution:** Make sure venv is activated - you should see `(venv)` in your prompt.

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1
```

### "pip is not recognized"

**Issue:** `pip: command not found`

**Solution:** Use the module syntax:

```powershell
python -m pip install package_name
```

### "Permission denied" (macOS/Linux)

**Issue:** `error: Permission denied`

**Solution:** Make sure venv is activated and don't use `sudo`:

```bash
source venv/bin/activate
pip install package_name
```

### "ModuleNotFoundError: No module named 'X'"

**Issue:** Package not installed

**Solution:** Install it:

```powershell
pip install package_name
```

### Build errors with packages

**Issue:** `error: linker 'link.exe' not found` or similar

**Solution:** Install Visual C++ Build Tools (see "Installing Additional Packages" section above)

---

## For Ralph & GSD Integration

### Adding Python Quality Checks to Ralph

Edit `scripts/ralph/prompt.md` and add:

```bash
# Python quality checks
python -m flake8 src/
python -m pytest tests/
```

### Using Python with GSD

In Claude Code:

```
/gsd-plan Create a Python Flask API endpoint

# GSD will suggest using your venv automatically
```

---

## Virtual Environment Best Practices

✅ **DO:**
- Activate venv before installing packages
- Use `requirements.txt` to track dependencies
- Commit `requirements.txt` to git
- Create new venv for each project
- Use different venv for different Python versions

❌ **DON'T:**
- Edit files inside `venv/` directory
- Commit `venv/` to git (it's too big)
- Share venv between projects
- Run `pip install` without venv activated
- Use system Python for projects

---

## Next Steps

1. ✅ Virtual environment created and working
2. → Activate it: `.\venv\Scripts\Activate.ps1`
3. → Install your specific project packages
4. → Add `*.pyc` and `venv/` to `.gitignore`
5. → Commit `requirements.txt` to git

---

## Files Reference

| File | Purpose | Edit? |
|------|---------|-------|
| `venv/` | Virtual environment | NO |
| `requirements.txt` | Package list | YES (to add packages) |
| `python.ini` | Python config | MAYBE |
| `docs/PYTHON.md` | Python guide | NO |

---

## Need to Reinstall?

```powershell
# Remove old venv
Remove-Item -Recurse -Force venv

# Create fresh venv
python -m venv venv

# Activate and install
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

**Status:** ✅ Virtual Environment Ready  
**Python Version:** 3.12.0  
**Packages Installed:** 29  
**Last Updated:** 2026-04-11 17:57 UTC
