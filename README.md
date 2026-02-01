# Zenith

Zenith is a pre-alpha 3D editor prototype originally built entirely in Python. It provides a lightweight scene editor with basic object manipulation, model import, and a first-pass OpenGL rendering pipeline using pygame and PyOpenGL.

Development status
- PRE-ALPHA — early development, incomplete features, and frequent breaking changes.
- DEVELOPMENT HALTED — active Python development is paused.
- NOTE: A new version of Zenith is currently being drafted in C#; this repository retains the original Python prototype for reference.

Key features (Python prototype)
- Scene view with basic lighting and depth testing
- Object selection and gizmo-based manipulation
- Model import (OBJ) and simple textured model support
- Editor and first-person navigation modes

Requirements
- Python 3.8+
- See requirements.txt for exact packages:
  - pygame
  - numpy
  - PyOpenGL
  - PyOpenGL_accelerate

Quick setup (Windows / macOS / Linux)
1. Clone the repo:
   git clone <repo-url> zenith
2. Create and activate a virtual environment:
   python -m venv .venv
   - Windows: .venv\Scripts\activate
   - macOS/Linux: source .venv/bin/activate
3. Install dependencies from requirements.txt:
   pip install -r requirements.txt

Build & run (Python prototype)
- No compiled build step required. Run the application directly after installing dependencies:
  python main.py

Notes for developers
- This repository contains the Python prototype only; active development is halted.
- The new C# implementation is being drafted separately — check repo issues or the project owner for updates.
- Main entry point for the prototype: main.py
- Core modules live under config/, editor/, obj/, utils/, etc.

Contributing
- Active feature development is paused. Feel free to open issues for discussion or archive/reference PRs, but new major changes are discouraged while the C# rewrite is in progress.

License
- See repository for license information.

Contact
- Repository owner: vannipper
- For questions or discussion, open an issue on the repo.
