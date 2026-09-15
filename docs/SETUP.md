# Qanat Setup & Run Guide

This document is the canonical local-development setup guide. Keep it updated whenever dependencies, entry points, or supported Python versions change.

## 1. Requirements

- Git
- Python **3.11 or 3.12**
- Internet access for Python package installation and, later, external data acquisition
- A terminal: PowerShell/Command Prompt on Windows, or Bash on macOS/Linux

The repository currently declares `>=3.11,<3.13` in `pyproject.toml`.

## 2. Clone the repository

```bash
git clone https://github.com/kokoosabzi/Qanat.git
cd Qanat
```

If the repository is already cloned:

```bash
git pull origin main
```

## 3. Create a virtual environment

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, use Command Prompt instead:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

After activation, the terminal should show `(.venv)`.

## 4. Upgrade packaging tools

### Windows

```powershell
py -m pip install --upgrade pip setuptools wheel
```

### macOS / Linux

```bash
python -m pip install --upgrade pip setuptools wheel
```

Using a virtual environment and `pip` is the recommended Python packaging workflow. See the Python Packaging User Guide: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/

## 5. Install the core application

The core installation intentionally stays lightweight:

### Windows

```powershell
py -m pip install -e .
```

### macOS / Linux

```bash
python -m pip install -e .
```

Editable installation means local source changes are immediately reflected in the installed project.

## 6. Install development/test dependencies

```bash
python -m pip install -e ".[test]"
```

On Windows PowerShell this command is also valid as written.

Then verify:

```bash
python -m pytest
```

## 7. Install the geospatial stack

When working on DEM/raster/terrain functionality:

```bash
python -m pip install -e ".[geo]"
```

This currently installs NumPy, Rasterio, PyProj, Shapely, SciPy, pandas and Matplotlib through the project's optional dependency group.

## 8. Install groundwater dependencies

When working on MODFLOW/FloPy integration:

```bash
python -m pip install -e ".[groundwater]"
```

This installs FloPy. The MODFLOW 6 executable itself is a separate scientific engine and will be integrated/configured when the groundwater phase is implemented.

## 9. Install hydrology dependencies

When working on process-based hydrology:

```bash
python -m pip install -e ".[hydrology]"
```

This installs pywatershed.

## 10. Install the complete development environment

For developers working across all currently defined engines:

```bash
python -m pip install -e ".[geo,groundwater,hydrology,test]"
```

This is the preferred command for the main development workstation once geospatial and numerical engine work begins.

## 11. Start the Streamlit application

From the repository root, with `.venv` active:

```bash
python -m streamlit run app/main.py
```

The equivalent command is:

```bash
streamlit run app/main.py
```

Streamlit starts a local web server and normally opens the application in the default browser. Official Streamlit documentation: https://docs.streamlit.io/develop/concepts/architecture/run-your-app

Stop the application with `Ctrl+C`.

## 12. Run tests

```bash
python -m pytest
```

For more output:

```bash
python -m pytest -v
```

Run a specific test file:

```bash
python -m pytest tests/test_config.py -v
```

## 13. Verify the installed project

```bash
python -c "import qanat; print(qanat.__version__)"
```

Verify Streamlit:

```bash
python -m streamlit version
```

Verify the application can be imported without starting the server:

```bash
python -c "from app.main import main; print('Qanat app import: OK')"
```

## 14. First application workflow

1. Start the application.
2. Open the **Location** tab and confirm latitude/longitude.
3. Select the analysis extent.
4. Select source DEM and requested output resolution.
5. Select the terrain/hydrology/weather/hydrogeology layers.
6. Select analysis modules.
7. Select desired outputs.
8. Click **Validate and save project**.
9. Inspect the generated project manifest.

The current UI is a configuration foundation. It does **not** yet perform the complete DEM-to-groundwater scientific pipeline.

## 15. Default project seed

The initial default location is:

```text
Latitude:  36.3916139
Longitude: 57.6854968
```

Default analysis seed:

```yaml
extent:
  mode: radius
  radius_m: 5000
resolution:
  source_dem_m: 30
  output_m: 30
```

These are editable project defaults, not fixed scientific assumptions.

## 16. Data directories

Large datasets must not be committed to Git.

Expected future local layout:

```text
data/
  raw/          downloaded source data
  processed/    processed rasters/vectors
  cache/        reusable download/cache files
  fixtures/     tiny deterministic test datasets

projects/
  <project-id>/
    project.json
    runs/
    artifacts/
```

The repository should contain metadata, manifests, checksums and small fixtures rather than large DEM/weather/raster datasets.

## 17. External scientific tools

The architecture may use established tools such as QGIS, GRASS/SAGA, WhiteboxTools, MODFLOW 6 and Blender. They are **not all required for the current configuration MVP**.

Do not install every external tool merely to start the current application. Add an external dependency to this guide when its corresponding engine becomes active and tested.

## 18. Troubleshooting

### `python` is not recognized on Windows

Try:

```powershell
py --version
```

If `py` works, use `py -m pip ...` and `py -3.11 -m venv .venv`.

### Wrong Python version

Check:

```bash
python --version
```

The current project requires Python 3.11 or 3.12.

### PowerShell activation is blocked

Use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Or configure the PowerShell execution policy according to your organization's security policy. Do not weaken system security settings unnecessarily.

### Streamlit does not start

Check installation:

```bash
python -m streamlit version
```

Then run:

```bash
python -m streamlit run app/main.py
```

### Rasterio installation fails

Do not add ad-hoc GDAL DLLs to the repository. First confirm the Python version and retry inside a clean virtual environment. Rasterio installation is intentionally an optional `geo` dependency because compiled geospatial packages can have platform-specific constraints.

### Tests fail after changing dependencies

Recreate the environment:

```bash
# deactivate first if active
deactivate
```

Windows:

```powershell
Remove-Item -Recurse -Force .venv
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip setuptools wheel
py -m pip install -e ".[geo,groundwater,hydrology,test]"
```

macOS/Linux:

```bash
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[geo,groundwater,hydrology,test]"
```

## 19. Agent continuation procedure

An AI coding agent should not begin implementation from the README alone. It should first read:

```text
docs/AGENT_CONTEXT.md
docs/ARCHITECTURE.md
docs/PROJECT_STATE.md
docs/ROADMAP.md
docs/DECISIONS.md
docs/SETUP.md
```

Then inspect the current Git tree and tests before modifying code.

After meaningful implementation work, update `PROJECT_STATE.md` and, when an architectural decision changes, `DECISIONS.md`.

## 20. Canonical commands — quick reference

```bash
# create environment
python3.11 -m venv .venv
source .venv/bin/activate

# install core
python -m pip install -e .

# install everything currently defined
python -m pip install -e ".[geo,groundwater,hydrology,test]"

# test
python -m pytest

# run application
python -m streamlit run app/main.py
```

Windows PowerShell equivalents:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip setuptools wheel
py -m pip install -e ".[geo,groundwater,hydrology,test]"
py -m pytest
py -m streamlit run app/main.py
```

## Scientific boundary

Installation and execution of the application do not imply that its outputs are sufficient for field excavation. Qanat is a decision-support and evidence-ranking system. Groundwater conclusions require appropriate hydrogeological evidence, and any physical excavation requires qualified geological/geotechnical assessment and applicable local requirements.
