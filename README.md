# WinGOES Pro 2.0

**Professional Windows Rebuild & Migration Assistant**

> *Rebuild Windows cleanly. Restore only what matters.*

WinGOES Pro captures your essential setup, lets you install Windows fresh, then restores only what's safe — leaving old Windows problems behind.

---

## What's New in 2.0

- **License system** — retail-ready key activation with 14-day free trial
- **Professional dark GUI** — completely redesigned interface
- **Workflow strip** — numbered step indicators (CAPTURE → APPLY → VERIFY)
- **Tabbed output** — Summary, Step Results, and Live Log panels
- **Colour-coded results** — at-a-glance pass/fail for every step
- **No breaking changes** — all v1 bundles fully compatible

---

## The Three-Step Workflow

```
CAPTURE  →  (reinstall Windows)  →  APPLY  →  VERIFY
```

**1. CAPTURE** — Run on your existing system. Records apps, configs, a hardware fingerprint. Does not modify your system.

**2. APPLY** — Run on your fresh Windows install. Restores only what's safe and intentional.

**3. VERIFY** — Confirms tools are working, flags missing drivers, produces a final checklist. Never modifies the system.

---

## Migration Modes

| Mode | Use When |
|------|----------|
| **CLEAN REBUILD** | Default. New PC, fresh install, eliminating legacy issues. |
| **SAME-HARDWARE TRANSFER** | Reinstalling Windows on the same physical machine. |
| **CUSTOM** | Expert control. Safety gates still apply. |

---

## What Gets Captured and Restored

| Category | Items |
|----------|-------|
| **Packages** | Winget, Chocolatey, Scoop |
| **Dev Configs** | Git, .gitconfig, SSH keys, VS Code, Windows Terminal |
| **Windows Settings** | Timezone, power plan (allowlist only, gated) |
| **Drivers** | Inventory + post-install checklist (transfer is advanced/gated) |

---

## What WinGOES Pro Will Never Do

- Import or export raw registry blobs
- Copy drivers blindly across hardware
- Clone system images
- Download files silently from the internet
- Migrate browser passwords

These are the most common sources of long-term Windows instability.

---

## Licensing

WinGOES Pro includes a **14-day free trial** with no registration required.

After the trial, a license key is required. Keys are activated locally — no internet connection needed.

**Key format:** `WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`

Activate via **License → Manage License** in the application.

**Editions:** PRO, HOME, TEAM

---

## Requirements

- Windows 10 Pro
- Python 3.11+
- PyQt6

```bash
pip install PyQt6
```

Optional tools (only needed if you use those features): `winget`, `choco`, `scoop`, `git`, `code` (VS Code CLI)

---

## Running

```bash
# GUI mode
python gui_app.py

# CLI — capture
python gui_app.py --cli capture --bundle C:\MyBundle --mode CLEAN_REBUILD --dry-run

# CLI — apply
python gui_app.py --cli apply --bundle C:\MyBundle --mode CLEAN_REBUILD

# CLI — verify
python gui_app.py --cli verify --bundle C:\MyBundle

# Developer: generate a license key
python gui_app.py --cli --genkey PRO

# Developer: validate a key
python gui_app.py --cli --validate-key WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
```

---

## Architecture

| File | Purpose |
|------|---------|
| `gui_app.py` | PyQt6 GUI + CLI entry point |
| `license_manager.py` | License key validation, activation, trial management |
| `models_and_utils.py` | Data models, hardware fingerprinting, utilities |
| `orchestrator_core.py` | CAPTURE / APPLY / VERIFY operation logic |

---

## Bundle Folder Structure

```
my_bundle/
├── fingerprints/
├── packages/
├── configs/
├── drivers/
└── runs/
    └── <run_id>/
        ├── report.json
        ├── summary.txt
        └── run.log
```

---

*WinGOES Pro — Safety-first. Every action explicit, logged, and reversible.*
