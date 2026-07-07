# WinGOES Pro — GUI User Manual

**Professional Windows Rebuild & Migration Assistant**

| | |
|---|---|
| **Product** | WinGOES Pro 2.1 |
| **Document** | GUI User Manual, Rev. 2 |
| **Applies to** | Windows 10 / 11, Python 3.11+, PyQt6 |
| **Copyright** | © 2026 Leon Priest (7h3v01d) — Apache License 2.0 |

---

<img width="1362" height="892" alt="screenshot" src="https://github.com/user-attachments/assets/084c1c96-bd35-46bc-a64c-83ccfa4a8b1d" />

## Contents

1. [What WinGOES Pro Is (and What It Is Not)](#1-what-wingoes-pro-is-and-what-it-is-not)
2. [Core Concepts](#2-core-concepts)
3. [Licensing & Activation](#3-licensing--activation)
4. [The Main Window — A Guided Tour](#4-the-main-window--a-guided-tour)
5. [Feature Toggles Reference](#5-feature-toggles-reference)
6. [The Workflow in Detail](#6-the-workflow-in-detail)
7. [Reading the Output](#7-reading-the-output)
8. [Reports & the Bundle Folder](#8-reports--the-bundle-folder)
9. [Common Real-World Scenarios](#9-common-real-world-scenarios)
10. [Troubleshooting & FAQ](#10-troubleshooting--faq)
11. [Best Practices](#11-best-practices)
- [Appendix A — CLI Reference](#appendix-a--cli-reference)
- [Appendix B — Safety Policy Summary](#appendix-b--safety-policy-summary)

---

## 1. What WinGOES Pro Is (and What It Is Not)

**WinGOES Pro** is a guided assistant that helps you **safely rebuild or re-set up Windows** without dragging along old problems. It is designed around one core idea:

> **A clean Windows install is usually best — but your useful setup should not be lost.**

WinGOES Pro lets you:

- **Capture** a snapshot of your current system (apps, configs, hardware fingerprint)
- Reinstall Windows cleanly
- **Apply** only the safe, intentional parts of your setup to the fresh install
- **Verify** that the new system is healthy and complete

**WinGOES Pro is NOT:**

- A full disk-imaging or cloning tool
- A "restore everything exactly as it was" utility
- A risky driver-migration or registry-copying tool

This is intentional. WinGOES Pro prioritises **stability, clarity, and control** over convenience shortcuts. Every risky operation is either blocked by policy or gated behind an explicit, hardware-verified opt-in.

---

## 2. Core Concepts

### 2.1 The Three-Stage Workflow

```
CAPTURE  →  (reinstall Windows)  →  APPLY  →  VERIFY
```

| Stage | Runs on | Modifies system? | Purpose |
|-------|---------|------------------|---------|
| **CAPTURE** | Your existing installation | **Never** | Records what can be safely re-applied later |
| **APPLY** | The fresh installation | Only with Dry Run off | Restores selected items |
| **VERIFY** | The fresh installation | **Never** | Confirms health, produces a checklist |

You can run these stages on different days and different machines — the bundle folder carries everything between them.

### 2.2 Migration Modes

WinGOES Pro always operates in one of three modes. The mode determines what the tool will *allow* and what it will *refuse*:

- **CLEAN REBUILD** *(default)* — the safest mode. Reinstalls apps and restores portable configs; **blocks** Windows-settings transfer and all driver transfer by policy.
- **SAME-HARDWARE TRANSFER** — for reinstalling on the same physical machine. Unlocks the gated extras, but only when the hardware fingerprint matches.
- **CUSTOM** — expert control over every toggle. Known-dangerous operations remain permanently blocked even here.

See the companion document *Mode Selection Guide* for a decision flowchart.

### 2.3 Hardware Fingerprints

During CAPTURE, WinGOES Pro records an identity fingerprint of the machine: manufacturer/model, baseboard, BIOS serial and UUID, CPU, GPUs, and network adapters. During APPLY and VERIFY it fingerprints the machine it is running on and classifies the match as **PASS**, **PARTIAL**, or **FAIL**.

Gated features (Windows settings transfer, DriverStore restore) require **PASS**. This check happens in the engine, not the UI — even if a toggle is on, the engine's deny-first gates (`enforce_gates`) will strip it if the hardware doesn't match. You never configure this; it is automatic.

### 2.4 Dry Run

The amber **Dry Run** switch in the toolbar (ON by default) previews every action without changing anything. Reports, summaries, and Step Results are produced exactly as they would be in a real run, with each action labelled as simulated. Turning Dry Run off before an Apply triggers a confirmation dialog.

### 2.5 The Bundle Folder

Everything WinGOES Pro captures lives in one folder you choose — the **bundle**. It is plain files (JSON, text, configs), portable across drives and machines, and human-readable. Treat it as the single artifact to back up between CAPTURE and APPLY.

---

## 3. Licensing & Activation

### 3.1 Trial

On first launch, WinGOES Pro begins a **14-day free trial** automatically — no registration, no internet connection. The sidebar badge shows the days remaining (e.g. `Trial • 12d left`, in amber).

### 3.2 Activating a License

1. Open **License → Manage License…** (or the teal **Manage License…** button at the bottom of the sidebar).
2. Enter your key in the format `WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`.
3. Optionally name the seat (e.g. "Main Dev PC").
4. Click **Activate**.

Keys are validated **locally** with an HMAC-SHA256 checksum — there is no call-home and no internet requirement. A valid activation turns the sidebar badge phosphor-green: `✓ Licensed • PRO`.

**Editions:** PRO, HOME, TEAM (encoded into the key).

### 3.3 Deactivating

Open the same dialog while licensed and click **Deactivate License**. This removes the stored license from the machine so the key can be used elsewhere.

### 3.4 Where the License Is Stored

`%APPDATA%\WinGOES Pro\` — the file is integrity-signed; manual edits invalidate it.

---

## 4. The Main Window — A Guided Tour

The window is laid out as: menu bar → top toolbar → sidebar + output area → action bar → status bar.

### 4.1 Menu Bar

| Menu | Contents |
|------|----------|
| **File** | Select Bundle Folder…, Open Last Report, Exit |
| **License** | Manage License… |
| **Help** | How to Use, About WinGOES Pro |

### 4.2 Top Toolbar

- **Workflow strip** — `① Capture › ② Apply › ③ Verify`. The active stage is underlined in teal while an operation runs.
- **Bundle** — the bundle folder path, with **Browse…**.
- **Mode selector** — CLEAN_REBUILD / SAME_HARDWARE_TRANSFER / CUSTOM.
- **Dry Run** — amber safety switch, ON by default.

### 4.3 Sidebar (Left)

- **Brand block** — product name and version.
- **License & Admin badges** — license state (green = licensed, amber = trial) and administrator status (`✓ Admin` green, `⚠ Admin` amber if not elevated).
- **Toggle sections** — Package Managers, Developer Configs, Windows Settings, Drivers. Toggles disabled by the current mode are greyed out with an amber italic note explaining why (e.g. *"Disabled in CLEAN REBUILD mode"*).
- **Manage License…** — quick access to activation.

### 4.4 Output Tabs (Centre)

| Tab | Shows |
|-----|-------|
| **Summary** | High-level narrative of the run: header, progress notes, completion badge, and a clickable link to the report |
| **Step Results** | A table of every item — Step, Item, Status, Message — with **OK** in phosphor green and **FAIL** in red. Opens automatically if a run completes with issues |
| **Live Log** | The raw, timestamped engine log as it streams |

### 4.5 Action Bar (Bottom)

- **▶ Capture** (teal), **▶ Apply** (phosphor), **▶ Verify** (amber) — the three operations, colour-keyed to the workflow.
- **Open Report** — opens the last run's `report.json`.
- **Copy Diagnostics** — copies the last report/summary paths to the clipboard, handy for support requests.

### 4.6 Status Bar

Shows readiness, the operation in progress, and the outcome of the last run.

---

## 5. Feature Toggles Reference

### 5.1 Package Managers

| Toggle | Captures | Applies | Notes |
|--------|----------|---------|-------|
| **Winget** *(recommended)* | Exported package list | Reinstalls where available | Some apps (games, vendor installers, Store apps) can't auto-reinstall; they are recorded, not forced |
| **Chocolatey** | `choco list` output | Reinstalls via choco | Enable only if you use it |
| **Scoop** | Scoop export | Reinstalls via scoop | Enable only if you use it |

An **installed-applications inventory** is always captured alongside, as a reference for anything the package managers can't cover.

### 5.2 Developer Configs

| Toggle | Captures | Applies |
|--------|----------|---------|
| **Git global config** | `git config --global` values | Restores identity and preferences |
| **.gitconfig file** | The raw `~/.gitconfig` | Restores the file (backed up first if one exists) |
| **SSH keys** | `~/.ssh` (keys, known_hosts, config) | Restores SSH access for Git, servers, automation |
| **VS Code** | Extensions list, settings, keybindings | Reinstalls extensions, restores preferences |
| **Windows Terminal** | Profiles and appearance settings | Restores terminal configuration |

> **Security note:** SSH private keys are copied into the bundle as-is. Treat the bundle folder with the same care as the keys themselves.

### 5.3 Windows Settings *(gated)*

Timezone/Region and Power plan. A small, safe, reversible allowlist — never arbitrary registry data. Availability by mode:

| Mode | Timezone / Power plan |
|------|-----------------------|
| CLEAN REBUILD | ✗ Disabled by policy |
| SAME-HARDWARE TRANSFER | ✓ If hardware match is PASS |
| CUSTOM | ✓ If hardware match is PASS |

### 5.4 Drivers *(handled carefully)*

| Toggle | Risk | What it does |
|--------|------|--------------|
| **Driver inventory** | Safe | Records every installed driver for reference |
| **Post-install checklist** | Safe | Generates an OEM-aware "what to install manually" checklist from your fingerprint (chipset, GPU, NIC hints) |
| **Driver transfer** | ⚠ Advanced, gated | Exports the DriverStore at CAPTURE and restores it at APPLY — **only** on hardware-match PASS, only outside CLEAN REBUILD, and only with the toggle explicitly on |

WinGOES Pro never copies drivers blindly between different machines. If in doubt, use inventory + checklist and install drivers fresh from the vendor.

---

## 6. The Workflow in Detail

### 6.1 CAPTURE — before reinstalling

1. Launch WinGOES Pro on the existing system.
2. Choose the bundle folder, mode, and toggles.
3. Click **▶ Capture**. The workflow strip highlights *① Capture*; controls lock while it runs.
4. Review **Summary** for the completion badge and **Step Results** for per-item status.
5. Copy the bundle folder to external storage. Done — nothing on your system was modified.

CAPTURE is repeatable: run it as many times as you like; each run is journalled separately under `runs/`.

### 6.2 APPLY — after the fresh install

1. On the new system, install Python 3.11+ and PyQt6, copy the bundle across, and launch WinGOES Pro.
2. Select the bundle and the **same mode** used at CAPTURE.
3. **First pass:** leave Dry Run ON and click **▶ Apply**. Read the Step Results — this is exactly what a real run will do.
4. **Second pass:** switch Dry Run off, click **▶ Apply**, and confirm the warning dialog.
5. The hardware fingerprint is checked automatically; anything requiring a match you don't have is skipped and logged.

Existing config files are **backed up with a timestamp** before being replaced.

### 6.3 VERIFY — final check

1. Click **▶ Verify**.
2. WinGOES Pro confirms key tools are present, checks device readiness (flagging devices with driver problems), and prints a completion checklist in Summary.
3. Work through the checklist — typically GPU driver, chipset package, and any vendor tools.

VERIFY never modifies the system and can be re-run any time.

---

## 7. Reading the Output

### 7.1 Warnings vs. Failures

Most log lines are informational. The classic example:

> *"Installed package is not available from any source"*

This means Winget detected the app but cannot reinstall it automatically — **nothing is broken**. WinGOES Pro records it so *you* know what to reinstall manually. Only entries marked **fatal** indicate a real failure.

### 7.2 The Completion Badge

At the end of every run the Summary tab shows either **✓ COMPLETED** (phosphor) or **⚠ COMPLETED WITH ISSUES** (red). "Issues" usually means best-effort items that need manual follow-up — check Step Results for the red rows, read their Message column, and act on anything genuinely fatal.

### 7.3 Step Results Colour Code

| Colour | Meaning |
|--------|---------|
| Phosphor green **OK** | Item completed (or simulated) successfully |
| Red **FAIL** | Item did not complete — read the message |
| Grey | Informational / skipped |

---

## 8. Reports & the Bundle Folder

```
my_bundle/
├── fingerprints/          # source_/target_fingerprint.json
├── packages/              # winget/choco/scoop exports + app inventory
├── configs/               # git, ssh, vscode, terminal, settings
├── drivers/               # inventory, checklist, optional DriverStore export
└── runs/
    └── <run_id>/
        ├── report.json    # full machine-readable result
        ├── summary.txt    # human-readable summary
        └── run.log        # complete timestamped log
```

Every run — dry or real — writes a complete journal under `runs/`. **Open Report** in the action bar opens the most recent `report.json`; **File → Open Last Report** does the same.

---

## 9. Common Real-World Scenarios

**Scenario 1 — New PC build.** Mode: CLEAN REBUILD. Enable Winget, Git, SSH, VS Code, Windows Terminal. CAPTURE on the old machine, APPLY + VERIFY on the new one. Result: clean Windows, dev environment restored, zero legacy baggage.

**Scenario 2 — Same PC, fresh Windows.** Mode: SAME-HARDWARE TRANSFER. Enable the extras you want (timezone, power plan); the fingerprint match unlocks them automatically. Everything else as Scenario 1.

**Scenario 3 — "I just want a checklist."** Enable Driver inventory + Post-install checklist only, run CAPTURE, and use the files in `drivers/` and `packages/` as a manual rebuild reference. You never need to run APPLY at all.

**Scenario 4 — Family PC rescue.** CLEAN REBUILD with Winget only. Capture, reinstall Windows, Apply. The post-install checklist tells you which vendor drivers to fetch. Ten minutes of clicking replaced by one bundle.

---

## 10. Troubleshooting & FAQ

**The Apply/Verify extras are greyed out.** Working as intended — you're in CLEAN REBUILD, or the hardware fingerprint didn't return PASS. The amber note under the toggle explains which.

**The admin badge shows ⚠ Admin.** Some captures (driver inventory, DriverStore export) and applies work best elevated. Close and relaunch WinGOES Pro as administrator.

**"COMPLETED WITH ISSUES" after Apply.** Open Step Results, filter your eyes to the red rows. Most are best-effort package installs that need a manual download; genuine failures say *fatal* in the log.

**My license key isn't accepted.** Check for typos — keys are 25 characters in five groups, letters and digits from the Base32 alphabet (no `0`, `1`, `8`, `9`). The dialog reports whether the format or the checksum failed.

**Can I use one bundle on several machines?** Yes for CLEAN REBUILD content (apps, configs). The gated extras will simply be skipped on non-matching hardware.

**Does WinGOES Pro touch my browser passwords?** Never. Password migration is permanently blocked by policy, in every mode.

---

## 11. Best Practices

- **CLEAN REBUILD is the safest choice** — reach for the other modes only with a reason.
- Keep the bundle backed up in **two** places before wiping a machine.
- Always Dry Run an Apply first; it costs one click and shows you everything.
- Read the VERIFY checklist to the end — it exists so nothing gets forgotten.
- Logs are your friend, not a sign of failure.

---

## Appendix A — CLI Reference

All GUI operations are available headless:

```bash
# Operations
python gui_app.py --cli capture --bundle C:\MyBundle --mode CLEAN_REBUILD --dry-run
python gui_app.py --cli apply   --bundle C:\MyBundle --mode CLEAN_REBUILD
python gui_app.py --cli verify  --bundle C:\MyBundle

# Toggle flags (defaults mirror the GUI)
--no-winget --choco --scoop
--no-git --no-gitconfig --no-ssh --no-vscode --no-terminal
--tz-region --power-plan
--no-driver-inventory --no-driver-checklist --driver-transfer

# License tooling (developer use — not for retail builds)
python gui_app.py --cli --genkey PRO
python gui_app.py --cli --validate-key WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
```

Exit codes: `0` success, `1` completed with failed items, `2` usage error.

## Appendix B — Safety Policy Summary

Enforced in the engine regardless of UI state:

| Action | Policy |
|--------|--------|
| Raw registry import/export | **Never** |
| Browser passwords/cookies | **Never** |
| Shell/context-menu handler migration | **Never** |
| Silent downloads | **Never** |
| Windows settings transfer | SAME-HW / CUSTOM + hardware PASS only |
| DriverStore transfer | SAME-HW / CUSTOM + hardware PASS + explicit toggle |
| Dry Run default | **ON** |
| Real Apply | Requires explicit confirmation dialog |

---

*WinGOES Pro — Safety-first. Every action explicit, logged, and reversible.*
