# WinGOES Pro — Changelog

## v2.1 — Dark Industrial

### Theme
- Full visual redesign to the signature dark-industrial system: obsidian `#0b0f14` base, teal `#2fd6c3` accent, phosphor `#4be08a` success, amber `#ffb454` warning, red `#ff5c66` danger, steel `#232b35` hairlines
- JetBrains Mono typography (Cascadia Mono / Consolas fallback), flat zero-radius controls throughout
- Action buttons re-keyed: Capture (teal), Apply (phosphor), Verify (amber) — purple removed
- Help / About dialogs, license dialog, summary rich-text, and results-table status colours migrated to the same palette
- `LIGHT_STYLE` renamed to `THEME_STYLE`

### Fixed
- **Capture / Apply / Verify crashed on click** — `build_toggles()` (GUI) and `cli_main()` (CLI) passed the removed `Toggles.drv_same_hw_transfer` field; now mapped to `drv_export_driverstore` + `drv_restore_driverstore`
- **Action buttons rendered dark/unreadable** — the action bar's widget-level stylesheet used bare declarations, which cascade to child widgets in Qt and override app-level QSS; scoped with `#actionBar { }` (same fix applied to the sidebar license row)
- **Malformed/legacy fingerprint JSON could crash APPLY / VERIFY** — added type guards in `generate_oem_driver_checklist_from_fp` and `classify_hardware_match`
- **License dialog styling never applied** — objectName mismatches (`licenseKeyInput` vs `#keyInput`, `successChip`/`warningChip` vs `#chipSuccess`/`#chipWarn`) corrected
- **License badge truncated in sidebar** — now displays edition code (`✓ Licensed • PRO`)

### Improvements
- Version bumped to 2.1 across app title, sidebar badge, About dialog, and AppUserModelID
- Tests updated for the current `Toggles` fields — suite green (5/5)
- Added Apache 2.0 LICENSE file; copyright Leon Priest (7h3v01d)

---

## v2.0 — Professional Retail Release

### New: License System
- **License key activation** — HMAC-SHA256 signed keys, format `WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`
- **Edition support** — PRO, HOME, and TEAM editions encoded into key
- **14-day free trial** — starts automatically on first run, no registration required
- **Offline validation** — no call-home or internet connection required for activation
- **Persistent license storage** — stored in `%APPDATA%\WinGOES Pro\` with tamper detection
- **Deactivation** — remove license from a machine via License → Manage License
- **Key generator** — `python gui_app.py --cli --genkey PRO` (developer/publisher use)

### New: Professional GUI (Dark Theme)
- Complete UI redesign — professional dark theme, production quality
- **Header banner** — branding, admin status badge, license status badge
- **Workflow strip** — numbered step indicators (CAPTURE → APPLY → VERIFY) with active state
- **Tabbed output panel** — Summary, Step Results, and Live Log in separate tabs
- **Colour-coded results table** — OK rows in green, FAIL rows in red
- **Styled action buttons** — distinct colours per operation (blue/green/purple)
- **Mode + Dry Run** in workflow strip for quick access
- **Status bar** — shows current operation progress and last result
- **License dialog** — activate, view, or deactivate license directly in-app
- Improved mode-gating UX — labels explain why options are disabled

### Improvements
- `models_and_utils.py` — updated `APP_TITLE` to "WinGOES Pro 2.0"
- CLI — added `--genkey EDITION` and `--validate-key KEY` developer flags
- Dry Run now defaults to ON (was already the case; now more prominently labelled)
- HTML help and about pages styled to match dark theme

### Compatibility
- All v1 functionality preserved — no breaking changes to core engine or bundle format
- Existing v1 bundles are fully compatible with v2.0

---

## v1.0 — Initial Release

- CAPTURE / APPLY / VERIFY workflow
- CLEAN_REBUILD, SAME_HARDWARE_TRANSFER, CUSTOM modes
- Hardware fingerprinting and matching
- Winget, Chocolatey, Scoop package management
- Git, SSH, VS Code, Windows Terminal config portability
- Driver inventory and post-install checklist
- Safe Windows settings allowlist (timezone, power plan)
- Dry Run mode
- JSON reports and plain-text summaries
- PyQt6 GUI + CLI interface
