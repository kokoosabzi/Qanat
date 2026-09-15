# Qanat Setup & Run Guide

این فایل راهنمای canonical برای نصب و اجرای نسخه پایدار `Qanat 0.1.0` است.

## 1. Requirements

- Git
- Python **3.11 یا 3.12**
- Internet access برای نصب packageها و اجرای زنده Copernicus/Open-Meteo
- PowerShell/Command Prompt در Windows یا Bash در macOS/Linux

نسخه Python پروژه در `pyproject.toml` برابر `>=3.11,<3.13` است.

## 2. دریافت نسخه پایدار

نسخه تثبیت‌شده روی branch زیر قرار می‌گیرد:

```text
stable/0.1.0
```

### Windows PowerShell

```powershell
git clone https://github.com/kokoosabzi/Qanat.git
cd Qanat
git fetch origin
git checkout stable/0.1.0
git pull --ff-only origin stable/0.1.0
```

### macOS / Linux

```bash
git clone https://github.com/kokoosabzi/Qanat.git
cd Qanat
git fetch origin
git checkout stable/0.1.0
git pull --ff-only origin stable/0.1.0
```

## 3. Virtual environment

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

اگر activation در PowerShell محدود بود:

```bat
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

## 4. نصب

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[geo,test]"
```

برای اجرای milestone فعلی نیازی به `groundwater` یا `hydrology` extras نیست؛ MODFLOW/pywatershed هنوز بخشی از stable milestone نیستند.

## 5. تست نصب

```powershell
python -m compileall -q app qanat
python -c "import app.main; import qanat.pipeline; print('Qanat import smoke test: OK')"
python -m pytest -v
```

تست‌های CI بدون دسترسی شبکه اجرا می‌شوند؛ provider اقلیمی در integration testها fake است.

## 6. اجرای Streamlit

```powershell
python -m streamlit run app/main.py
```

در macOS/Linux نیز:

```bash
python -m streamlit run app/main.py
```

## 7. اولین اجرای واقعی

در UI:

1. Location را بررسی کن.
2. Extent و Resolution را بررسی کن.
3. روی **Validate and save project** بزن.
4. سپس روی **Run terrain + hydrology + climate** بزن.

این اجرا مسیر زیر را طی می‌کند:

```text
ProjectConfig
    ↓
Copernicus GLO-30 DEM
    ↓
Terrain processing
    ↓
D8 flow + accumulation + drainage + stream order
    ↓
Automatic outlet / watershed.tif
    ↓
Open-Meteo historical precipitation + ET0
    ↓
Deterministic climate water balance
    ↓
Watershed runoff / recharge-indicator / deficit volumes
```

برای اجرای واقعی به اینترنت نیاز است، چون DEM و داده آب‌وهوایی از سرویس‌های خارجی دریافت می‌شوند.

## 8. خروجی‌های اصلی

```text
data/processed/terrain/
  dem.tif
  slope.tif
  aspect.tif
  hillshade.tif
  contours.geojson
  terrain_provenance.json

data/processed/hydrology/
  flow_direction.tif
  flow_accumulation.tif
  drainage.tif
  stream_order.tif
  drainage_network.geojson
  watershed.tif

data/processed/climate/
  climate_provenance.json
```

داده‌های بزرگ نباید commit شوند.

## 9. Default project seed

```text
Latitude:  36.3916139
Longitude: 57.6854968
Radius:    5000 m
Source DEM: 30 m
Output:     30 m
```

این‌ها defaultهای قابل‌تغییر هستند، نه فرض‌های ثابت علمی.

## 10. Stable milestone scope

`0.1.0` شامل این بخش‌هاست:

- configuration و validation
- Streamlit UI
- Copernicus GLO-30 terrain acquisition/processing
- elevation/slope/aspect/hillshade/contours/provenance
- deterministic D8 hydrology
- automatic watershed generation
- historical Open-Meteo precipitation/ET0 adapter
- deterministic climate water-balance indicators
- watershed-scale volume conversion
- terrain → hydrology → climate orchestration
- automated regression tests و CI برای Python 3.11/3.12

این موارد هنوز جزو stable milestone نیستند:

- hydrogeological evidence ingestion
- wells/springs/geology/fault fusion
- MODFLOW 6/FloPy execution
- calibrated recharge model
- candidate ranking/AI evidence fusion
- forecast comparison pipeline
- production 3D/video outputs
- live field validation

## 11. Troubleshooting

### `py` یا `python` پیدا نمی‌شود

```powershell
py --version
```

و مطمئن شو Python 3.11 یا 3.12 نصب است.

### Rasterio نصب نمی‌شود

در یک virtual environment تمیز نصب را تکرار کن و Python 3.12 را ترجیح بده. GDAL DLL دستی را به repository اضافه نکن.

### Streamlit بالا نمی‌آید

```powershell
python -m streamlit version
python -c "import app.main; print('Qanat app import: OK')"
python -m streamlit run app/main.py
```

### تست fail می‌شود

```powershell
python -m pytest -v
```

ابتدا مطمئن شو روی `stable/0.1.0` هستی و branch محلی با remote یکی است:

```powershell
git status
git rev-parse HEAD
git rev-parse origin/stable/0.1.0
```

## 12. Agent continuation procedure

قبل از تغییرات مهم این فایل‌ها را بخوان:

```text
docs/AGENT_CONTEXT.md
docs/ARCHITECTURE.md
docs/PROJECT_STATE.md
docs/ROADMAP.md
docs/DECISIONS.md
docs/SETUP.md
```

بعد از هر milestone مهم، `PROJECT_STATE.md` و در صورت نیاز `DECISIONS.md` را به‌روز کن.

## Scientific boundary

خروجی Qanat برای screening و decision support است. `recharge_indicator_mm` یک proxy غربالگری است و recharge کالیبره‌شده groundwater نیست. نتیجه‌گیری نهایی درباره آب زیرزمینی و هرگونه عملیات حفاری/تونل‌زنی به شواهد هیدروژئولوژیک، ژئوفیزیک، داده چاه/چشمه و بررسی حرفه‌ای میدانی نیاز دارد.
