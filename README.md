# Clim4Cast Image Generation

A run-once pipeline that turns daily climate raster forecasts into ready-to-publish
map images for the [Clim4Cast](https://clim4cast.eu) website.

For every forecast day it clips the source rasters to the area of interest,
reprojects them, renders coloured maps with country and sea outlines, places those
maps on localised background templates (7 languages), and uploads the result to the
website API.

**Output**

| Folder | Content |
|---|---|
| `temp/final/layers/{normal,reduced}/` | individual map images, one per parameter and day |
| `temp/final/downloads/{normal,reduced}/{lang}/` | composite images built on language templates |

Two palette variants are produced for every parameter: `normal` (full colour scale)
and `reduced` (simplified scale).

---

## Requirements

- **Python 3.10 or newer**
- Access to the source data share `//monospace/mendelu/Windy/SoilClim2_Windy/Prediction`
- Background templates in `data/raster_templates/background_templates/`
  (**not** included in this repository — see below)

### Background templates

Templates must follow the naming convention `bg_<parameter>_<depth, if applicable>`:

| Template | Parameter |
|---|---|
| `bg_AWD_0-40cm`, `bg_AWD_0-100cm`, `bg_AWD_0-200cm` | Available Water Depth |
| `bg_AWR_0-40cm`, `bg_AWR_0-100cm`, `bg_AWR_0-200cm` | Available Water Reserve |
| `bg_AWP_0-40cm`, `bg_AWP_0-100cm`, `bg_AWP_0-200cm` | Available Water Potential |
| `bg_FWI_GenZ` | Fire Weather Index |
| `bg_DFM1H`, `bg_DFM10H`, `bg_DFM100H`, `bg_DFM1000H` | Dead Fuel Moisture (1/10/100/1000 hours) |
| `bg_HI` | Heat Index |
| `bg_UTCI` | Universal Thermal Climate Index |

The directory hierarchy and folder names must be kept exactly as follows:

```
data/raster_templates/background_templates/
├── normal/
│   └── cs/  de/  en/  hr/  pl/  sk/  sl/
└── reduced/
    └── cs/  de/  en/  hr/  pl/  sk/  sl/
```

---

## Installation

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e .                # runtime only
pip install -e ".[dev]"         # with development tools
```

---

## Configuration

Configuration is split in two: **paths** live in `config.yaml` (safe to commit) and
**secrets** live in `.env`.

### Environment variables

Copy `.env.example` to `.env` and fill in the values.

| Variable | Default | Purpose |
|---|---|---|
| `API_USERNAME` | — (**required**) | Basic-auth user for the upload API. Startup fails if it is missing. |
| `API_PASSWORD` | — (**required**) | Basic-auth password. |
| `CLIM4CAST_DRY_RUN` | `true` | `false`, `0` or `no` enable the real upload. Any other value skips it. |
| `CLIM4CAST_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. |
| `CLIM4CAST_LOG_FILE` | *(unset)* | When set, logs are written to this file **in addition to** stdout. |
| `APP_ROOT` | package parent directory | Overrides the project root used to resolve relative paths. |

> **Safe by default:** uploading is disabled unless `CLIM4CAST_DRY_RUN` is explicitly
> turned off. A missing or misspelled value never triggers an accidental upload.

### `config.yaml`

Holds the source data path, the template and shapefile locations, the font, and the
API base URL. All relative paths are resolved against the project root.

---

## Usage

```bash
clim4cast-imagegen              # console command
python -m clim4cast_imagegen    # equivalent
```

### Run-once model

The pipeline performs **one pass and exits** — it never waits in a loop. Repetition
is the job of an external scheduler.

Each run:

1. If today's data is already processed (`state/last_processed.txt`) → exit **0**, nothing to do.
2. If today's input folder does not exist yet → exit **0**, the scheduler will try again later.
3. Otherwise: clip and reproject rasters → render maps → build composites →
   upload (unless dry-run) → record the day as processed → clean the temporary files.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success, **or** there was nothing to do |
| `1` | Failure — see the log for the reason |

"Data is not ready yet" is a normal outcome, not an error, so it returns `0` and does
not raise a false alarm.

---

## Deployment

The pipeline is designed to run once per invocation, so it works with any scheduler
(systemd timer, cron, Windows Task Scheduler).

A short polling interval is recommended during the publishing window, because the
processed-day marker prevents duplicate work: once a day has been delivered, every
later run exits immediately.

> Detailed setup instructions will be added once the target server is confirmed.

---

## Development

```bash
pytest                          # run the test suite
ruff check .                    # lint
mypy clim4cast_imagegen         # static type check
pre-commit install              # enable git hooks (once)
pre-commit run --all-files      # run every check manually
```

The same three checks run automatically on GitHub Actions for every push and pull
request.

---

## Project structure

```
clim4cast_imagegen/
├── core/       configuration, constants, exceptions, logging, pipeline helpers
├── io/         everything that touches the outside world: files, rasters, images, API
├── services/   business logic: raster processing, visualization, templates
├── utils/      small pure helpers (filenames, palettes)
└── cli.py      entry point that orchestrates the steps
```

**Layer rule:** `core` depends on nothing inside the project, `io` may use `core`, and
`services` reach the disk only through `io`. Keeping this direction makes the business
logic easy to test without touching the file system.
