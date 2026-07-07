# WinGOES Pro — Quick Start Guide

**Professional Windows Rebuild & Migration Assistant**

| | |
|---|---|
| **Product** | WinGOES Pro 2.1 |
| **Document** | Quick Start Guide, Rev. 2 |
| **Applies to** | Windows 10 / 11, Python 3.11+ |

---

## What WinGOES Pro Does

WinGOES Pro helps you **reinstall Windows cleanly** while safely restoring your **apps and personal setup** — without bringing old Windows problems with you.

The entire product is built around one workflow:

```
CAPTURE  →  (reinstall Windows)  →  APPLY  →  VERIFY
```

> **First run:** WinGOES Pro starts a 14-day free trial automatically — no registration needed. The badge in the sidebar shows your license state at all times. See the User Manual, §3, for activation.

---

## Step 1 — Choose the Right Mode

The mode selector is in the top toolbar, next to the Dry Run switch.

| Mode | Choose it when | Safety level |
|------|----------------|--------------|
| **CLEAN REBUILD** *(default)* | New PC, fresh install, eliminating old issues | ✅ Safest — risky transfers blocked |
| **SAME-HARDWARE TRANSFER** | Reinstalling on the **same physical PC** | ⚠️ Advanced — requires hardware match |
| **CUSTOM** | Expert manual control | 🧪 Expert — safety gates still apply |

> **If unsure: choose CLEAN REBUILD.** The sidebar will grey out anything the mode forbids and tell you why.

---

## Step 2 — Select What You Want to Keep

Toggles live in the left sidebar. Enable only what you actually use.

**Package Managers** — Winget (recommended), Chocolatey, Scoop
**Developer Configs** — Git config, `.gitconfig`, SSH keys (`~/.ssh`), VS Code (settings + extensions), Windows Terminal
**Windows Settings** *(gated)* — Timezone/Region, Power plan
**Drivers** — Inventory (safe), Post-install checklist (safe), Driver transfer (⚠ advanced, gated)

Drivers are **never copied automatically**. Inventory and checklist only, unless you explicitly enable the gated transfer on matching hardware.

---

## Step 3 — CAPTURE (Before Reinstalling Windows)

1. Open WinGOES Pro on your **current** Windows installation.
2. Pick a **Bundle folder** (toolbar → *Browse…*). This is where everything is saved.
3. Select your mode and toggles.
4. Click the **teal ▶ Capture** button in the action bar.
5. Watch progress in **Live Log**; review results in **Summary** and **Step Results**.
6. Copy the bundle folder to a USB drive, external disk, or network location.

✔ Nothing is changed on your system — CAPTURE is read-only and repeatable.

---

## Step 4 — Install Windows Cleanly

Perform a normal Windows 10/11 clean install and complete initial setup. Do **not** copy old system folders or drivers across manually.

---

## Step 5 — APPLY (After Windows Is Installed)

1. Install Python 3.11+ and `pip install PyQt6` on the new system.
2. Copy your saved bundle folder onto the machine and select it in the toolbar.
3. Select the **same mode** you used during CAPTURE.
4. Leave **Dry Run ON** (the amber switch — on by default) and click the **phosphor ▶ Apply** button to preview.
5. Review the Step Results table, then switch Dry Run off and Apply for real. You'll be asked to confirm.

✔ Apps reinstall where possible • configs restore safely • risky actions are blocked automatically.

---

## Step 6 — VERIFY (Final Check)

Click the **amber ▶ Verify** button to confirm key tools are installed, check device readiness, and generate a driver/setup checklist. Use the checklist to finish any manual installs (GPU driver, chipset, vendor tools). VERIFY never modifies the system.

---

## Reading the Log

Messages like *"Installed package is not available from any source"* are **normal** — the app was detected but can't be auto-installed, and you may reinstall it manually later. Only entries marked **fatal** indicate a real failure. Failed items appear in **red** in Step Results; passes in **green**.

---

## Best Practices

- Use **CLEAN REBUILD** unless you are certain you need otherwise
- Keep your bundle backed up in two places
- Preview with **Dry Run** before any real Apply
- Read the VERIFY checklist to completion
- Never force driver transfers across different hardware

---

## In One Sentence

**WinGOES Pro gives you a clean Windows install — with your useful setup restored and your old problems left behind.**

---

*Copyright © 2026 Leon Priest (7h3v01d) • Apache License 2.0*
