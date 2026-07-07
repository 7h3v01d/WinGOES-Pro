# WinGOES Pro 2.1

**Professional Windows Rebuild & Migration Assistant**

> *Rebuild Windows cleanly. Restore only what matters.*

WinGOES Pro captures your essential setup, lets you install Windows fresh, then restores only what's safe — leaving old Windows problems behind.

---

<img width="1362" height="892" alt="screenshot" src="https://github.com/user-attachments/assets/70aac1e8-481c-4657-afaf-a4d450a6cbfb" />


## What's New in 2.1

- **Dark-industrial theme** — full visual redesign: obsidian base, teal accent, phosphor/amber/red status colours, JetBrains Mono typography, flat zero-radius controls, 1px steel hairlines
- **Action buttons re-keyed to the status palette** — Capture (teal), Apply (phosphor), Verify (amber)
- **Fixed:** Capture / Apply / Verify buttons crashed on click due to a stale `Toggles` field (`drv_same_hw_transfer` → `drv_export_driverstore` / `drv_restore_driverstore`); affected both GUI and CLI
- **Fixed:** action-bar stylesheet cascaded onto child buttons, rendering them unreadable (widget-level QSS now scoped by objectName)
- **Fixed:** malformed or legacy fingerprint JSON could crash APPLY / VERIFY (type guards added to checklist generation and hardware matching)
- **Fixed:** license dialog styling never applied due to objectName mismatches; key field now renders in themed monospace
- **Fixed:** license badge truncation — now shows edition code (`✓ Licensed • PRO`)
- Test suite green (5/5) including policy-gate invariants and deterministic capture artifacts

## What's New in 2.0

- **License system** — retail-ready key activation with 14-day free trial
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
| **Drivers** | Inventory + post-install checklist (DriverStore transfer is advanced/gated, requires hardware-match PASS) |

---

## What WinGOES Pro Will Never Do

- Import or export raw registry blobs
- Copy drivers blindly across hardware
- Clone system images
- Download files silently from the internet
- Migrate browser passwords

These are the most common sources of long-term Windows instability.

---

## Licensing (Product Activation)

WinGOES Pro includes a **14-day free trial** with no registration required.

After the trial, a license key is required. Keys are validated locally with HMAC-SHA256 — no call-home, no internet connection needed.

**Key format:** `WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`

Activate via **License → Manage License** in the application.

**Editions:** PRO, HOME, TEAM

---

## Requirements

- Windows 10 / 11
- Python 3.11+
- PyQt6

```bash
pip install PyQt6
```

Optional tools (only needed if you use those features): `winget`, `choco`, `scoop`, `git`, `code` (VS Code CLI)

For best visual results install the [JetBrains Mono](https://www.jetbrains.com/lp/mono/) font; the UI falls back to Cascadia Mono / Consolas if it's absent.

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

# Developer: generate a license key (do not ship in retail builds)
python gui_app.py --cli --genkey PRO

# Developer: validate a key
python gui_app.py --cli --validate-key WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
```

Run the test suite:

```bash
python -m unittest tests.test_wingoes_suite -v
```

---

## Architecture

| File | Purpose |
|------|---------|
| `gui_app.py` | PyQt6 GUI + CLI entry point, dark-industrial theme |
| `license_manager.py` | License key validation, activation, trial management |
| `models_and_utils.py` | Data models, policy gates, hardware fingerprinting, utilities |
| `orchestrator_core.py` | CAPTURE / APPLY / VERIFY operation logic |
| `tests/test_wingoes_suite.py` | Policy invariants + deterministic artifact tests |

**Safety model:** deny-first policy gates (`enforce_gates`) run in the engine regardless of UI state. CLEAN REBUILD forces risky toggles off; DriverStore restore and Windows-settings transfer require a hardware-fingerprint match of PASS; browser passwords and shell-extension migration are permanently off by policy.

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

## Theme

Signature dark-industrial palette:

| Role | Hex |
|------|-----|
| Base (obsidian) | `#0b0f14` |
| Accent (teal) | `#2fd6c3` |
| Success (phosphor) | `#4be08a` |
| Warning (amber) | `#ffb454` |
| Danger (red) | `#ff5c66` |
| Hairline (steel) | `#232b35` |

Flat controls, zero border-radius, monospace throughout.

---

## License

Copyright © 2026 Leon Priest (7h3v01d)

Licensed under the [PETL v1.0](LICENSE).

---

*WinGOES Pro — Safety-first. Every action explicit, logged, and reversible.*
