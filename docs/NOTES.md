[← Back to Main Menu](../README.md)

# Python Project Notes: `uv` and `pyproject.toml`

## What is `pyproject.toml`?

`pyproject.toml` is the configuration file for a Python project. It tells tools like `uv`:  
Think of it as the configuration file for your Python project. It stores things like:

* Project name and version
* Required Python version
* Project dependencies (libraries)
* Build and tool configuration

Think of it as the Python equivalent of:

* `package.json` (Node.js)
* `Cargo.toml` (Rust)  
Instead of remembering every package you installed, they're all listed in one place.
---

## Why use `pyproject.toml`?

Without it:

* Packages are installed into the virtual environment only.
* There is no record of which libraries the project depends on.
* Someone else cannot easily recreate the same environment.

With it:

* All dependencies are tracked.
* `uv` knows which packages belong to the project.
* Anyone can clone the project and run `uv sync` to install the correct dependencies.

---

## `uv` Commands

### Create a project

```bash
uv init
```

Creates `pyproject.toml` and initializes the project.

---

### Create a virtual environment

```bash
uv venv
```

Creates `.venv/`.

---

### Activate the environment

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```cmd
.venv\Scripts\activate
```

---

### Install a dependency (recommended)

```bash
uv add pandas
```

This:

1. Installs the package.
2. Updates `pyproject.toml`.
3. Updates `uv.lock`.

---

### Install without a `pyproject.toml`

```bash
uv pip install pandas
```

This behaves like `pip install`:

* Installs the package into the active venv.
* Does **not** record it as a project dependency.

---

### Install all project dependencies

```bash
uv sync
```

Reads `pyproject.toml` and `uv.lock` and installs everything.

---

## When to use what?

**Small scripts / experiments**

```bash
uv venv
uv pip install <package>
```

No `pyproject.toml` needed.

**Real projects (recommended)**

```bash
uv init
uv venv
uv add <package>
```

This is the modern Python workflow.

---

## Quick Rule to Remember

* `uv venv` → Creates an isolated Python environment.
* `uv init` → Makes the folder a managed Python project.
* `uv add` → Installs + records dependencies.
* `uv pip install` → Only installs, like `pip`.
* `uv sync` → Recreates the project's environment from the project files.

**Mnemonic:**

* **venv = environment**
* **pyproject.toml = project information**
* **uv add = install + remember**
* **uv pip install = install only**



# Why is this useful?

Imagine you push your project to GitHub.

Another developer (or future you) clones it:

git clone <repo>
cd your-project
uv sync

That's it. They get the same dependencies and versions you used, without manually installing packages one by one.