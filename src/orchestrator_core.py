# orchestrator_core.py
from __future__ import annotations

import os
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models_and_utils import (
    MATCH_PASS,
    MODE_CLEAN,
    MODE_SAME,
    MODE_CUSTOM,
    Toggles,
    RunContext,
    StepItem,
    StepReport,
    append_log,
    backup_if_exists,
    capture_fingerprint,
    classify_hardware_match,
    compute_disabled_features,
    copy_tree_best_effort,
    enforce_gates,
    ensure_dir,
    is_windows,
    load_fingerprint,
    make_run_context,
    run_cmd,
    safe_write_json,
    safe_write_text,
    which,
    write_report,
    write_summary,
)

# -----------------------------
# Packages
# -----------------------------


def capture_winget(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    pkg_dir = ctx.bundle_dir / "packages"
    ensure_dir(pkg_dir)
    out = pkg_dir / "winget.json"
    if which("winget") is None:
        step.items.append(
            StepItem("winget_status", "Winget status", False, message="Not found. Install App Installer / winget manually.")
        )
        return
    cmd = ["winget", "export", "-o", str(out), "--include-versions"]
    run_cmd(ctx, step, "winget_export", "Capture winget export", cmd, stream_cb=stream_cb, allow_fail=True)


def apply_winget(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    in_path = ctx.bundle_dir / "packages" / "winget.json"
    if which("winget") is None:
        step.items.append(
            StepItem("winget_status", "Winget status", False, message="Not found. Install App Installer / winget manually.")
        )
        return
    if not in_path.exists():
        step.items.append(StepItem("winget_missing", "Winget import file", False, message=f"Missing: {in_path}"))
        return
    if ctx.dry_run:
        step.items.append(StepItem("winget_import_dryrun", "Winget import (dry-run)", True, message=f"Would import: {in_path}"))
        return
    cmd = ["winget", "import", "-i", str(in_path), "--accept-package-agreements", "--accept-source-agreements"]
    run_cmd(ctx, step, "winget_import", "Apply winget import", cmd, stream_cb=stream_cb, allow_fail=True)


def capture_choco(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    pkg_dir = ctx.bundle_dir / "packages"
    ensure_dir(pkg_dir)
    out = pkg_dir / "choco_list.txt"
    if which("choco") is None:
        step.items.append(
            StepItem("choco_status", "Chocolatey status", False, message="Not found. Install Chocolatey manually if desired.")
        )
        return
    cmd = ["choco", "list", "--local-only"]
    it = run_cmd(ctx, step, "choco_list", "Capture Chocolatey local package list", cmd, stream_cb=stream_cb, allow_fail=True)
    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            shutil.copy2(it.stdout_path, out)
            step.items.append(StepItem("choco_list_saved", "Saved Chocolatey list", True, message=str(out)))
    except Exception as e:
        step.items.append(StepItem("choco_list_save_err", "Save Chocolatey list", False, message=str(e)))


def parse_choco_list(text: str) -> List[str]:
    pkgs: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("chocolatey"):
            continue
        parts = line.split()
        if parts:
            name = parts[0].strip()
            if name.replace(".", "").isdigit():
                continue
            if name.lower() in ("packages", "installed", "validation", "warnings", "errors"):
                continue
            if any(c.isalnum() for c in name):
                pkgs.append(name)
    seen = set()
    out: List[str] = []
    for p in pkgs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def apply_choco(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    in_path = ctx.bundle_dir / "packages" / "choco_list.txt"
    if which("choco") is None:
        step.items.append(
            StepItem("choco_status", "Chocolatey status", False, message="Not found. Install Chocolatey manually if desired.")
        )
        return
    if not in_path.exists():
        step.items.append(StepItem("choco_missing", "Chocolatey package list", False, message=f"Missing: {in_path}"))
        return
    txt = in_path.read_text(encoding="utf-8", errors="replace")
    pkgs = parse_choco_list(txt)
    if not pkgs:
        step.items.append(StepItem("choco_none", "Chocolatey packages", True, message="No packages parsed."))
        return
    if ctx.dry_run:
        step.items.append(
            StepItem("choco_install_dryrun", "Chocolatey install (dry-run)", True, message=f"Would install: {', '.join(pkgs[:30])}{'...' if len(pkgs)>30 else ''}")
        )
        return
    cmd = ["choco", "install", "-y"] + pkgs
    run_cmd(ctx, step, "choco_install", "Apply Chocolatey installs", cmd, stream_cb=stream_cb, allow_fail=True)


def capture_scoop(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    pkg_dir = ctx.bundle_dir / "packages"
    ensure_dir(pkg_dir)
    out = pkg_dir / "scoop_export.txt"
    if which("scoop") is None:
        step.items.append(StepItem("scoop_status", "Scoop status", False, message="Not found. Install Scoop manually if desired."))
        return
    cmd = ["scoop", "export"]
    it = run_cmd(ctx, step, "scoop_export", "Capture Scoop export", cmd, stream_cb=stream_cb, allow_fail=True)
    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            shutil.copy2(it.stdout_path, out)
            step.items.append(StepItem("scoop_saved", "Saved Scoop export", True, message=str(out)))
    except Exception as e:
        step.items.append(StepItem("scoop_save_err", "Save Scoop export", False, message=str(e)))


def parse_scoop_export(text: str) -> List[str]:
    pkgs: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.lower().startswith("scoop"):
            continue
        if " " in line:
            line = line.split()[0]
        if line.startswith("{") or line.startswith("["):
            break
        pkgs.append(line)
    seen = set()
    out: List[str] = []
    for p in pkgs:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def apply_scoop(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    in_path = ctx.bundle_dir / "packages" / "scoop_export.txt"
    if which("scoop") is None:
        step.items.append(StepItem("scoop_status", "Scoop status", False, message="Not found. Install Scoop manually if desired."))
        return
    if not in_path.exists():
        step.items.append(StepItem("scoop_missing", "Scoop export file", False, message=f"Missing: {in_path}"))
        return
    txt = in_path.read_text(encoding="utf-8", errors="replace")
    pkgs = parse_scoop_export(txt)
    if not pkgs:
        step.items.append(StepItem("scoop_none", "Scoop packages", True, message="No packages parsed."))
        return
    if ctx.dry_run:
        step.items.append(
            StepItem("scoop_install_dryrun", "Scoop install (dry-run)", True, message=f"Would install: {', '.join(pkgs[:30])}{'...' if len(pkgs)>30 else ''}")
        )
        return
    cmd = ["scoop", "install"] + pkgs
    run_cmd(ctx, step, "scoop_install", "Apply Scoop installs", cmd, stream_cb=stream_cb, allow_fail=True)


def capture_installed_apps_inventory(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    inv_dir = ctx.bundle_dir / "inventory"
    ensure_dir(inv_dir)
    out = inv_dir / "installed_apps_registry.txt"
    if not (is_windows() and which("powershell")):
        step.items.append(StepItem("apps_inv_status", "Installed apps inventory", False, message="PowerShell not found."))
        return
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        r"""
$paths = @(
'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
$apps = foreach($p in $paths){
  Get-ItemProperty $p -ErrorAction SilentlyContinue |
    Select-Object DisplayName,DisplayVersion,Publisher,InstallDate |
    Where-Object { $_.DisplayName -and $_.DisplayName.Trim().Length -gt 0 }
}
$apps | Sort-Object DisplayName | Format-Table -AutoSize | Out-String -Width 4096
""".strip(),
    ]
    it = run_cmd(ctx, step, "apps_registry_inv", "Capture installed apps inventory (registry, inventory-only)", cmd, stream_cb=stream_cb, allow_fail=True)
    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            shutil.copy2(it.stdout_path, out)
            step.items.append(StepItem("apps_inv_saved", "Saved installed apps inventory", True, message=str(out)))
    except Exception as e:
        step.items.append(StepItem("apps_inv_save_err", "Save installed apps inventory", False, message=str(e)))


# -----------------------------
# Portable userland configs
# -----------------------------


def capture_git(ctx: RunContext, step: StepReport, include_gitconfig: bool, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "git"
    ensure_dir(cfg_dir)
    if which("git") is None:
        step.items.append(StepItem("git_status", "Git status", False, message="git not found. Install manually if needed."))
        return
    cmd = ["git", "config", "--global", "--list"]
    it = run_cmd(ctx, step, "git_global_list", "Capture git global config list", cmd, stream_cb=stream_cb, allow_fail=True)
    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            shutil.copy2(it.stdout_path, cfg_dir / "git_global_config.txt")
    except Exception:
        pass

    if include_gitconfig:
        src = Path((os.environ.get("USERPROFILE", ""))) / ".gitconfig"
        dst = cfg_dir / ".gitconfig"
        if src.exists():
            try:
                ensure_dir(dst.parent)
                shutil.copy2(src, dst)
                step.items.append(StepItem("gitconfig_copy", "Copy .gitconfig", True, message=str(dst)))
            except Exception as e:
                step.items.append(StepItem("gitconfig_copy_err", "Copy .gitconfig", False, message=str(e)))
        else:
            step.items.append(StepItem("gitconfig_missing", "Copy .gitconfig", False, message=f"Not found: {src}"))


def apply_git(ctx: RunContext, step: StepReport, restore_gitconfig: bool, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "git"
    if restore_gitconfig:
        src = cfg_dir / ".gitconfig"
        dst = Path((os.environ.get("USERPROFILE", ""))) / ".gitconfig"
        if not src.exists():
            step.items.append(StepItem("gitconfig_missing", "Restore .gitconfig", False, message=f"Missing in bundle: {src}"))
            return
        if ctx.dry_run:
            step.items.append(StepItem("gitconfig_restore_dryrun", "Restore .gitconfig (dry-run)", True, message=f"Would restore to: {dst}"))
            return
        try:
            backup_if_exists(dst)
            ensure_dir(dst.parent)
            shutil.copy2(src, dst)
            step.items.append(StepItem("gitconfig_restore", "Restore .gitconfig", True, message=str(dst)))
        except Exception as e:
            step.items.append(StepItem("gitconfig_restore_err", "Restore .gitconfig", False, message=str(e)))


def capture_ssh(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "ssh"
    ensure_dir(cfg_dir)
    src = Path((os.environ.get("USERPROFILE", ""))) / ".ssh"
    dst = cfg_dir / ".ssh"
    ok, msg = copy_tree_best_effort(src, dst)
    step.items.append(StepItem("ssh_copy", "Copy ~/.ssh", ok, message=msg))


def apply_ssh(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "ssh" / ".ssh"
    dst = Path((os.environ.get("USERPROFILE", ""))) / ".ssh"
    if not cfg_dir.exists():
        step.items.append(StepItem("ssh_missing", "Restore ~/.ssh", False, message=f"Missing in bundle: {cfg_dir}"))
        return
    if ctx.dry_run:
        step.items.append(StepItem("ssh_restore_dryrun", "Restore ~/.ssh (dry-run)", True, message=f"Would restore to: {dst}"))
        return
    try:
        if dst.exists() and dst.is_dir():
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            bak = dst.with_name(f".ssh.bak_{stamp}")
            shutil.move(str(dst), str(bak))
        ensure_dir(dst)
        shutil.copytree(cfg_dir, dst, dirs_exist_ok=True)
        step.items.append(StepItem("ssh_restore", "Restore ~/.ssh", True, message=str(dst)))
    except Exception as e:
        step.items.append(StepItem("ssh_restore_err", "Restore ~/.ssh", False, message=str(e)))


def capture_vscode(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "vscode"
    ensure_dir(cfg_dir)

    if which("code") is None and which("code.cmd") is None:
        step.items.append(
            StepItem(
                "vscode_status",
                "VS Code status",
                False,
                message="code CLI not found. Install VS Code and ensure 'code' is on PATH if you want extensions capture/apply.",
            )
        )
    else:
        code_exe = "code" if which("code") is not None else "code.cmd"
        cmd = [code_exe, "--list-extensions"]
        it = run_cmd(ctx, step, "vscode_ext", "Capture VS Code extensions list", cmd, stream_cb=stream_cb, allow_fail=True)
        try:
            if it.stdout_path and Path(it.stdout_path).exists():
                shutil.copy2(it.stdout_path, cfg_dir / "extensions.txt")
        except Exception:
            pass

    appdata = Path(os.environ.get("APPDATA", ""))
    user_dir = appdata / "Code" / "User"
    for fname in ("settings.json", "keybindings.json"):
        src = user_dir / fname
        if src.exists():
            try:
                shutil.copy2(src, cfg_dir / fname)
                step.items.append(StepItem(f"vscode_{fname}_copy", f"Copy VS Code {fname}", True, message=str(cfg_dir / fname)))
            except Exception as e:
                step.items.append(StepItem(f"vscode_{fname}_err", f"Copy VS Code {fname}", False, message=str(e)))
        else:
            step.items.append(StepItem(f"vscode_{fname}_missing", f"Copy VS Code {fname}", False, message=f"Not found: {src}"))


def apply_vscode(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "vscode"
    if not cfg_dir.exists():
        step.items.append(StepItem("vscode_bundle_missing", "VS Code bundle", False, message=f"Missing: {cfg_dir}"))
        return

    appdata = Path(os.environ.get("APPDATA", ""))
    user_dir = appdata / "Code" / "User"
    ensure_dir(user_dir)

    for fname in ("settings.json", "keybindings.json"):
        src = cfg_dir / fname
        dst = user_dir / fname
        if src.exists():
            if ctx.dry_run:
                step.items.append(StepItem(f"vscode_restore_{fname}_dryrun", f"Restore VS Code {fname} (dry-run)", True, message=f"Would restore to: {dst}"))
            else:
                try:
                    backup_if_exists(dst)
                    shutil.copy2(src, dst)
                    step.items.append(StepItem(f"vscode_restore_{fname}", f"Restore VS Code {fname}", True, message=str(dst)))
                except Exception as e:
                    step.items.append(StepItem(f"vscode_restore_{fname}_err", f"Restore VS Code {fname}", False, message=str(e)))

    ext_file = cfg_dir / "extensions.txt"
    if which("code") is None:
        step.items.append(StepItem("vscode_code_missing", "VS Code extensions apply", False, message="code CLI not found. Install VS Code and enable code on PATH."))
        return
    if ext_file.exists():
        exts = [ln.strip() for ln in ext_file.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        if not exts:
            step.items.append(StepItem("vscode_ext_none", "VS Code extensions apply", True, message="No extensions in bundle."))
            return
        if ctx.dry_run:
            step.items.append(StepItem("vscode_ext_dryrun", "Install VS Code extensions (dry-run)", True, message=f"Would install: {', '.join(exts[:30])}{'...' if len(exts)>30 else ''}"))
            return
        for i, ext in enumerate(exts[:500]):
            cmd = ["code", "--install-extension", ext, "--force"]
            run_cmd(ctx, step, f"vscode_install_ext_{i+1}", f"Install VS Code extension: {ext}", cmd, stream_cb=stream_cb, allow_fail=True)
    else:
        step.items.append(StepItem("vscode_ext_missing", "VS Code extensions apply", False, message=f"Missing: {ext_file}"))


def capture_windows_terminal(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "windows_terminal"
    ensure_dir(cfg_dir)

    localapp = Path(os.environ.get("LOCALAPPDATA", ""))
    src = localapp / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"
    if src.exists():
        try:
            shutil.copy2(src, cfg_dir / "settings.json")
            step.items.append(StepItem("wt_settings_copy", "Copy Windows Terminal settings.json", True, message=str(cfg_dir / "settings.json")))
        except Exception as e:
            step.items.append(StepItem("wt_settings_copy_err", "Copy Windows Terminal settings.json", False, message=str(e)))
    else:
        step.items.append(StepItem("wt_settings_missing", "Copy Windows Terminal settings.json", False, message=f"Not found: {src}"))


def apply_windows_terminal(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_file = ctx.bundle_dir / "configs" / "windows_terminal" / "settings.json"
    if not cfg_file.exists():
        step.items.append(StepItem("wt_bundle_missing", "Restore Windows Terminal settings.json", False, message=f"Missing in bundle: {cfg_file}"))
        return
    localapp = Path(os.environ.get("LOCALAPPDATA", ""))
    dst = localapp / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"
    if ctx.dry_run:
        step.items.append(StepItem("wt_restore_dryrun", "Restore Windows Terminal settings.json (dry-run)", True, message=f"Would restore to: {dst}"))
        return
    try:
        ensure_dir(dst.parent)
        backup_if_exists(dst)
        shutil.copy2(cfg_file, dst)
        step.items.append(StepItem("wt_restore", "Restore Windows Terminal settings.json", True, message=str(dst)))
    except Exception as e:
        step.items.append(StepItem("wt_restore_err", "Restore Windows Terminal settings.json", False, message=str(e)))


# -----------------------------
# Windows settings allowlist
# -----------------------------


def capture_timezone(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "windows_settings"
    ensure_dir(cfg_dir)
    if which("tzutil") is None:
        step.items.append(StepItem("tzutil_missing", "Capture timezone", False, message="tzutil not found."))
        return
    it = run_cmd(ctx, step, "tz_get", "Capture timezone", ["tzutil", "/g"], stream_cb=stream_cb, allow_fail=True)
    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            tz = Path(it.stdout_path).read_text(encoding="utf-8", errors="replace").strip()
            safe_write_text(cfg_dir / "timezone.txt", tz + "\n")
            step.items.append(StepItem("tz_saved", "Saved timezone", True, message=str(cfg_dir / "timezone.txt")))
    except Exception as e:
        step.items.append(StepItem("tz_save_err", "Save timezone", False, message=str(e)))


def apply_timezone_region(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    tz_file = ctx.bundle_dir / "configs" / "windows_settings" / "timezone.txt"
    if not tz_file.exists():
        step.items.append(StepItem("tz_missing", "Timezone apply", False, message="No captured timezone."))
        return
    tz = tz_file.read_text(encoding="utf-8", errors="replace").strip()
    if not tz:
        step.items.append(StepItem("tz_empty", "Timezone apply", False, message="Captured timezone is empty."))
        return
    if ctx.dry_run:
        step.items.append(StepItem("tz_dryrun", "Set timezone (dry-run)", True, message=f"Would set timezone: {tz}"))
        return
    if which("tzutil") is None:
        step.items.append(StepItem("tzutil_missing", "Set timezone", False, message="tzutil not found."))
        return
    run_cmd(ctx, step, "tz_set", f"Set timezone: {tz}", ["tzutil", "/s", tz], stream_cb=stream_cb, allow_fail=True)


def capture_power_plan(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    cfg_dir = ctx.bundle_dir / "configs" / "windows_settings"
    ensure_dir(cfg_dir)
    if which("powercfg") is None:
        step.items.append(StepItem("powercfg_missing", "Capture power plan", False, message="powercfg not found."))
        return
    it = run_cmd(ctx, step, "powerplan_get", "Capture active power plan", ["powercfg", "/getactivescheme"], stream_cb=stream_cb, allow_fail=True)
    try:
        txt = ""
        if it.stdout_path and Path(it.stdout_path).exists():
            txt = Path(it.stdout_path).read_text(encoding="utf-8", errors="replace")
        guid = ""
        for token in txt.replace("(", " ").replace(")", " ").split():
            if len(token) == 36 and token.count("-") == 4:
                guid = token
                break
        if guid:
            safe_write_text(cfg_dir / "powerplan_guid.txt", guid + "\n")
            step.items.append(StepItem("powerplan_saved", "Saved power plan GUID", True, message=str(cfg_dir / "powerplan_guid.txt")))
        else:
            step.items.append(StepItem("powerplan_parse_fail", "Parse power plan GUID", False, message="Could not parse GUID from powercfg output."))
    except Exception as e:
        step.items.append(StepItem("powerplan_save_err", "Save power plan GUID", False, message=str(e)))


def apply_power_plan(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    plan_file = ctx.bundle_dir / "configs" / "windows_settings" / "powerplan_guid.txt"
    if not plan_file.exists():
        step.items.append(StepItem("powerplan_missing", "Power plan apply", False, message="No captured power plan GUID."))
        return
    guid = plan_file.read_text(encoding="utf-8", errors="replace").strip()
    if not guid:
        step.items.append(StepItem("powerplan_empty", "Power plan apply", False, message="Captured GUID is empty."))
        return
    if ctx.dry_run:
        step.items.append(StepItem("powerplan_dryrun", "Set power plan (dry-run)", True, message=f"Would set power plan: {guid}"))
        return
    if which("powercfg") is None:
        step.items.append(StepItem("powercfg_missing", "Set power plan", False, message="powercfg not found."))
        return
    run_cmd(ctx, step, "powerplan_set", f"Set power plan: {guid}", ["powercfg", "/setactive", guid], stream_cb=stream_cb, allow_fail=True)


# -----------------------------
# Drivers (inventory + checklists + DriverStore export/restore)
# -----------------------------


def capture_driver_inventory(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    drv_dir = ctx.bundle_dir / "drivers" / "inventory"
    ensure_dir(drv_dir)

    if which("pnputil") is not None:
        it = run_cmd(ctx, step, "pnputil_enum", "Capture pnputil /enum-drivers", ["pnputil", "/enum-drivers"], stream_cb=stream_cb, allow_fail=True)
        try:
            if it.stdout_path and Path(it.stdout_path).exists():
                shutil.copy2(it.stdout_path, drv_dir / "pnputil_enum_drivers.txt")
        except Exception:
            pass
    else:
        step.items.append(StepItem("pnputil_missing", "pnputil inventory", False, message="pnputil not found."))

    if which("driverquery") is not None:
        it = run_cmd(ctx, step, "driverquery_v", "Capture driverquery /v", ["driverquery", "/v"], stream_cb=stream_cb, allow_fail=True)
        try:
            if it.stdout_path and Path(it.stdout_path).exists():
                shutil.copy2(it.stdout_path, drv_dir / "driverquery_v.txt")
        except Exception:
            pass
    else:
        step.items.append(StepItem("driverquery_missing", "driverquery inventory", False, message="driverquery not found."))


def capture_driverstore_export(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    """
    HIGH VALUE / HIGH RISK-IF-RESTORED:
      - Backup is safe (CAPTURE): pnputil /export-driver * <bundle>/drivers/driverstore_export
    """
    export_dir = ctx.bundle_dir / "drivers" / "driverstore_export"
    ensure_dir(export_dir)
    if which("pnputil") is None:
        step.items.append(StepItem("drvstore_status", "DriverStore export", False, message="pnputil not found."))
        return
    cmd = ["pnputil", "/export-driver", "*", str(export_dir)]
    run_cmd(ctx, step, "drvstore_export", f"Export DriverStore -> {export_dir}", cmd, stream_cb=stream_cb, allow_fail=True, timeout_s=600)
    step.items.append(StepItem("drvstore_export_path", "DriverStore export path", True, message=str(export_dir)))


def apply_driverstore_restore(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    """
    HIGH RISK:
      - Restore is only attempted when gates permit (SAME/CUSTOM + hardware PASS + user enabled)
      - Applies drivers from the export folder using pnputil /add-driver ... /install
    """
    export_dir = ctx.bundle_dir / "drivers" / "driverstore_export"
    if not export_dir.exists():
        step.items.append(StepItem("drvstore_missing", "DriverStore restore", False, message=f"Missing in bundle: {export_dir}"))
        return
    if which("pnputil") is None:
        step.items.append(StepItem("drvstore_status", "DriverStore restore", False, message="pnputil not found."))
        return
    if ctx.dry_run:
        step.items.append(StepItem("drvstore_restore_dryrun", "DriverStore restore (dry-run)", True, message=f"Would restore from: {export_dir}"))
        return
    # Best-effort: let pnputil discover .inf files in subdirs
    cmd = ["pnputil", "/add-driver", str(export_dir / "*.inf"), "/subdirs", "/install"]
    run_cmd(ctx, step, "drvstore_restore", f"Restore DriverStore from {export_dir} (HIGH RISK)", cmd, stream_cb=stream_cb, allow_fail=True, timeout_s=900)


def _norm_s(s: Any) -> str:
    return (str(s).strip() if s is not None else "").strip()


def _as_dict(v: Any) -> Dict[str, Any]:
    """Guard for legacy/malformed fingerprint fields that may not be dicts."""
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def generate_oem_driver_checklist_from_fp(fp: Dict[str, Any]) -> List[str]:
    mm = _as_dict(fp.get("manufacturer_model"))
    bb = _as_dict(fp.get("baseboard"))
    cpu = _as_dict(fp.get("cpu")).get("name")
    gpus = _as_list(fp.get("gpus"))
    nics = _as_list(fp.get("nics"))

    mfg = _norm_s(mm.get("Manufacturer"))
    model = _norm_s(mm.get("Model"))
    bb_mfg = _norm_s(bb.get("Manufacturer"))
    bb_prod = _norm_s(bb.get("Product"))

    mfg_l = mfg.lower()
    lines: List[str] = []
    lines.append("OEM Driver Checklist (WinGOES)")
    lines.append("")
    lines.append("Goal: Install drivers from official sources only (OEM support pages / Microsoft Update / GPU vendor).")
    lines.append("WinGOES does not download installers; this is a checklist only.")
    lines.append("")
    lines.append(f"System: {mfg} {model}".strip())
    if bb_mfg or bb_prod:
        lines.append(f"Baseboard: {bb_mfg} {bb_prod}".strip())
    if cpu:
        lines.append(f"CPU: {_norm_s(cpu)}")
    if gpus:
        lines.append("GPU(s): " + ", ".join([_norm_s(g.get("name")) for g in gpus if g.get("name")]))
    if nics:
        lines.append("NIC(s): " + ", ".join([_norm_s(n.get("name")) for n in nics if n.get("name")]))

    lines.append("")
    lines.append("Recommended order:")
    lines.append("  1) Chipset / Platform driver (OEM/motherboard support page)")
    lines.append("  2) Storage / SATA / NVMe (OEM + Windows Update)")
    lines.append("  3) Network (LAN/Wi-Fi/Bluetooth)")
    lines.append("  4) Audio")
    lines.append("  5) GPU (NVIDIA/AMD/Intel official package)")
    lines.append("  6) Peripheral drivers (printer, headset, capture devices)")

    lines.append("")
    lines.append("Official source hints:")
    if any(k in mfg_l for k in ("dell",)):
        lines.append("  - Dell: use Dell Support (Service Tag / model) to install chipset/network/audio first.")
    elif any(k in mfg_l for k in ("hp", "hewlett")):
        lines.append("  - HP: use HP Support Assistant or HP driver page for your exact model.")
    elif "lenovo" in mfg_l:
        lines.append("  - Lenovo: use Lenovo Vantage / support page for your model.")
    elif any(k in mfg_l for k in ("asus",)):
        lines.append("  - ASUS: use ASUS support page for your exact model/motherboard.")
    elif any(k in mfg_l for k in ("acer",)):
        lines.append("  - Acer: use Acer support page for your model.")
    elif any(k in mfg_l for k in ("msi",)):
        lines.append("  - MSI: use MSI support page for your motherboard/laptop model.")
    elif any(k in mfg_l for k in ("gigabyte",)):
        lines.append("  - GIGABYTE: use GIGABYTE support page for your motherboard (chipset/LAN/audio) and GPU vendor for graphics.")
    else:
        lines.append("  - Use your OEM or motherboard vendor support page for chipset/LAN/audio.")
    lines.append("  - GPU: NVIDIA/AMD/Intel official drivers, matching your GPU model and Windows 10.")
    lines.append("  - Microsoft Update: run Windows Update after chipset/network.")

    lines.append("")
    lines.append("If Device Manager shows Unknown devices:")
    lines.append("  - Use Hardware IDs to identify (Properties → Details → Hardware Ids).")
    lines.append("  - Prefer OEM packages over random driver sites.")
    return lines


def capture_oem_driver_checklist(ctx: RunContext, step: StepReport, fp: Dict[str, Any]) -> None:
    out_dir = ctx.bundle_dir / "drivers" / "checklist"
    ensure_dir(out_dir)
    out = out_dir / "oem_driver_checklist.txt"
    lines = generate_oem_driver_checklist_from_fp(fp)
    safe_write_text(out, "\n".join(lines) + "\n")
    step.items.append(StepItem("drv_oem_checklist", "OEM driver checklist", True, message=str(out)))


def verify_device_readiness(ctx: RunContext, step: StepReport, stream_cb=None) -> List[str]:
    suggestions: List[str] = []

    if not (is_windows() and which("powershell")):
        step.items.append(StepItem("ps_missing", "Device readiness checks", False, message="PowerShell not found."))
        return ["Install chipset driver (manual)", "Install GPU driver (manual)", "Install LAN/Wi-Fi driver (manual)"]

    run_cmd(
        ctx,
        step,
        "dev_display",
        "List display adapters (Get-PnpDevice -Class Display)",
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-PnpDevice -Class Display -ErrorAction SilentlyContinue | Select-Object FriendlyName,Status,InstanceId | Format-Table -AutoSize | Out-String -Width 4096",
        ],
        stream_cb=stream_cb,
        allow_fail=True,
    )

    run_cmd(
        ctx,
        step,
        "dev_net",
        "List network adapters (Get-NetAdapter)",
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-NetAdapter -ErrorAction SilentlyContinue | Select-Object Name,Status,LinkSpeed,MacAddress,PnPDeviceID | Format-Table -AutoSize | Out-String -Width 4096",
        ],
        stream_cb=stream_cb,
        allow_fail=True,
    )

    it = run_cmd(
        ctx,
        step,
        "dev_not_ok",
        "List devices not OK (Get-PnpDevice | where Status -ne 'OK')",
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object { $_.Status -ne 'OK' } | Select-Object Class,FriendlyName,Status,InstanceId | Format-Table -AutoSize | Out-String -Width 4096",
        ],
        stream_cb=stream_cb,
        allow_fail=True,
    )

    suggestions.append("Install chipset driver (OEM/motherboard support page)")
    suggestions.append("Install GPU driver (NVIDIA/AMD/Intel OEM package)")
    suggestions.append("Install LAN/Wi-Fi driver (OEM network driver)")

    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            txt = Path(it.stdout_path).read_text(encoding="utf-8", errors="replace")
            if any(k in txt.lower() for k in ("error", "unknown", "problem", "disabled", "failed")):
                suggestions.append("Resolve devices with error/unknown status (Device Manager / OEM drivers)")
    except Exception:
        pass

    return suggestions


# -----------------------------
# Browsers (bookmarks + extensions only)
# -----------------------------


def _list_extensions_dir(ext_dir: Path) -> List[str]:
    if not ext_dir.exists():
        return []
    ids: List[str] = []
    for p in sorted(ext_dir.iterdir()):
        if p.is_dir():
            ids.append(p.name)
    return ids


def capture_chromium_profile(ctx: RunContext, step: StepReport, name: str, profile_dir: Path, stream_cb=None) -> None:
    out_dir = ctx.bundle_dir / "browsers" / name
    ensure_dir(out_dir)

    bookmarks = profile_dir / "Bookmarks"
    if bookmarks.exists():
        try:
            shutil.copy2(bookmarks, out_dir / "Bookmarks")
            step.items.append(StepItem(f"{name}_bookmarks", f"{name} bookmarks", True, message=str(out_dir / "Bookmarks")))
        except Exception as e:
            step.items.append(StepItem(f"{name}_bookmarks_err", f"{name} bookmarks", False, message=str(e)))
    else:
        step.items.append(StepItem(f"{name}_bookmarks_missing", f"{name} bookmarks", False, message=f"Not found: {bookmarks}"))

    ext_dir = profile_dir / "Extensions"
    ids = _list_extensions_dir(ext_dir)
    safe_write_text(out_dir / "extensions_list.txt", "\n".join(ids) + "\n")
    step.items.append(StepItem(f"{name}_ext_list", f"{name} extensions list", True, message=str(out_dir / "extensions_list.txt")))

    # Best-effort: copy Extensions folder (may be large; still optional)
    if ext_dir.exists():
        ok, msg = copy_tree_best_effort(ext_dir, out_dir / "Extensions")
        step.items.append(StepItem(f"{name}_ext_copy", f"{name} extensions folder copy", ok, message=msg))
    else:
        step.items.append(StepItem(f"{name}_ext_missing", f"{name} extensions folder", False, message=f"Not found: {ext_dir}"))


def apply_chromium_profile(ctx: RunContext, step: StepReport, name: str, profile_dir: Path, stream_cb=None) -> None:
    in_dir = ctx.bundle_dir / "browsers" / name
    if not in_dir.exists():
        step.items.append(StepItem(f"{name}_bundle_missing", f"{name} restore", False, message=f"Missing in bundle: {in_dir}"))
        return

    bookmarks_src = in_dir / "Bookmarks"
    bookmarks_dst = profile_dir / "Bookmarks"
    if bookmarks_src.exists():
        if ctx.dry_run:
            step.items.append(StepItem(f"{name}_bookmarks_dryrun", f"{name} bookmarks restore (dry-run)", True, message=f"Would restore to: {bookmarks_dst}"))
        else:
            try:
                ensure_dir(bookmarks_dst.parent)
                backup_if_exists(bookmarks_dst)
                shutil.copy2(bookmarks_src, bookmarks_dst)
                step.items.append(StepItem(f"{name}_bookmarks_restore", f"{name} bookmarks restore", True, message=str(bookmarks_dst)))
            except Exception as e:
                step.items.append(StepItem(f"{name}_bookmarks_restore_err", f"{name} bookmarks restore", False, message=str(e)))
    else:
        step.items.append(StepItem(f"{name}_bookmarks_src_missing", f"{name} bookmarks restore", False, message=f"Missing in bundle: {bookmarks_src}"))

    ext_src = in_dir / "Extensions"
    ext_dst = profile_dir / "Extensions"
    if ext_src.exists():
        if ctx.dry_run:
            step.items.append(StepItem(f"{name}_ext_dryrun", f"{name} extensions restore (dry-run)", True, message=f"Would restore to: {ext_dst}"))
        else:
            ok, msg = copy_tree_best_effort(ext_src, ext_dst)
            step.items.append(StepItem(f"{name}_ext_restore", f"{name} extensions restore", ok, message=msg))
    else:
        step.items.append(StepItem(f"{name}_ext_src_missing", f"{name} extensions restore", False, message=f"Missing in bundle: {ext_src}"))


def capture_firefox(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    out_root = ctx.bundle_dir / "browsers" / "firefox"
    ensure_dir(out_root)
    appdata = Path(os.environ.get("APPDATA", ""))
    profiles_root = appdata / "Mozilla" / "Firefox"
    profiles_ini = profiles_root / "profiles.ini"

    if profiles_ini.exists():
        try:
            shutil.copy2(profiles_ini, out_root / "profiles.ini")
            step.items.append(StepItem("ff_profiles_ini", "Firefox profiles.ini", True, message=str(out_root / "profiles.ini")))
        except Exception as e:
            step.items.append(StepItem("ff_profiles_ini_err", "Firefox profiles.ini", False, message=str(e)))
    else:
        step.items.append(StepItem("ff_profiles_ini_missing", "Firefox profiles.ini", False, message=f"Not found: {profiles_ini}"))

    profiles_dir = profiles_root / "Profiles"
    if not profiles_dir.exists():
        step.items.append(StepItem("ff_profiles_missing", "Firefox Profiles dir", False, message=f"Not found: {profiles_dir}"))
        return

    for prof in sorted([p for p in profiles_dir.iterdir() if p.is_dir()])[:10]:
        prof_out = out_root / "Profiles" / prof.name
        ensure_dir(prof_out)

        # Bookmarks backups (JSONLZ4)
        bb_dir = prof / "bookmarkbackups"
        if bb_dir.exists():
            backups = sorted([p for p in bb_dir.iterdir() if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
            if backups:
                try:
                    shutil.copy2(backups[0], prof_out / "bookmarkbackup_latest.jsonlz4")
                    step.items.append(StepItem(f"ff_bb_{prof.name}", f"Firefox bookmark backup ({prof.name})", True, message=str(prof_out / "bookmarkbackup_latest.jsonlz4")))
                except Exception as e:
                    step.items.append(StepItem(f"ff_bb_err_{prof.name}", f"Firefox bookmark backup ({prof.name})", False, message=str(e)))
        else:
            step.items.append(StepItem(f"ff_bb_missing_{prof.name}", f"Firefox bookmark backups ({prof.name})", False, message=f"Not found: {bb_dir}"))

        # Extensions manifest
        ext_json = prof / "extensions.json"
        if ext_json.exists():
            try:
                shutil.copy2(ext_json, prof_out / "extensions.json")
                step.items.append(StepItem(f"ff_extjson_{prof.name}", f"Firefox extensions.json ({prof.name})", True, message=str(prof_out / "extensions.json")))
            except Exception as e:
                step.items.append(StepItem(f"ff_extjson_err_{prof.name}", f"Firefox extensions.json ({prof.name})", False, message=str(e)))
        else:
            step.items.append(StepItem(f"ff_extjson_missing_{prof.name}", f"Firefox extensions.json ({prof.name})", False, message=f"Not found: {ext_json}"))

        # Optional: copy extensions dir (contains installed add-ons)
        ext_dir = prof / "extensions"
        if ext_dir.exists():
            ok, msg = copy_tree_best_effort(ext_dir, prof_out / "extensions")
            step.items.append(StepItem(f"ff_extdir_{prof.name}", f"Firefox extensions dir ({prof.name})", ok, message=msg))
        else:
            step.items.append(StepItem(f"ff_extdir_missing_{prof.name}", f"Firefox extensions dir ({prof.name})", False, message=f"Not found: {ext_dir}"))


def apply_firefox(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    # Best-effort only: restore into existing profile folders if they exist.
    in_root = ctx.bundle_dir / "browsers" / "firefox" / "Profiles"
    if not in_root.exists():
        step.items.append(StepItem("ff_bundle_missing", "Firefox restore", False, message=f"Missing in bundle: {in_root}"))
        return

    appdata = Path(os.environ.get("APPDATA", ""))
    profiles_dir = appdata / "Mozilla" / "Firefox" / "Profiles"
    if not profiles_dir.exists():
        step.items.append(StepItem("ff_profiles_missing", "Firefox restore", False, message=f"Profiles dir not found: {profiles_dir}"))
        return

    restored_any = False
    for prof_in in sorted([p for p in in_root.iterdir() if p.is_dir()])[:10]:
        prof_dst = profiles_dir / prof_in.name
        if not prof_dst.exists():
            continue

        # restore extensions folder + extensions.json (best-effort)
        if ctx.dry_run:
            step.items.append(StepItem(f"ff_restore_dryrun_{prof_in.name}", f"Firefox restore ({prof_in.name}) (dry-run)", True, message=f"Would restore to: {prof_dst}"))
            restored_any = True
            continue

        try:
            ext_json_src = prof_in / "extensions.json"
            if ext_json_src.exists():
                backup_if_exists(prof_dst / "extensions.json")
                shutil.copy2(ext_json_src, prof_dst / "extensions.json")

            ext_dir_src = prof_in / "extensions"
            if ext_dir_src.exists():
                ok, msg = copy_tree_best_effort(ext_dir_src, prof_dst / "extensions")
                step.items.append(StepItem(f"ff_ext_restore_{prof_in.name}", f"Firefox extensions restore ({prof_in.name})", ok, message=msg))
            else:
                step.items.append(StepItem(f"ff_ext_src_missing_{prof_in.name}", f"Firefox extensions restore ({prof_in.name})", False, message=f"Missing in bundle: {ext_dir_src}"))

            restored_any = True
        except Exception as e:
            step.items.append(StepItem(f"ff_restore_err_{prof_in.name}", f"Firefox restore ({prof_in.name})", False, message=str(e)))

    if not restored_any:
        step.items.append(StepItem("ff_restore_none", "Firefox restore", False, message="No matching Firefox profiles found to restore into (best-effort)."))


# -----------------------------
# Tools captures
# -----------------------------


def capture_powertoys(ctx: RunContext, step: StepReport) -> None:
    src = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "PowerToys"
    dst = ctx.bundle_dir / "tools" / "powertoys"
    ok, msg = copy_tree_best_effort(src, dst)
    step.items.append(StepItem("powertoys_copy", "PowerToys settings backup", ok, message=msg))


def apply_powertoys(ctx: RunContext, step: StepReport) -> None:
    src = ctx.bundle_dir / "tools" / "powertoys"
    dst = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "PowerToys"
    if not src.exists():
        step.items.append(StepItem("powertoys_missing", "PowerToys settings restore", False, message=f"Missing in bundle: {src}"))
        return
    if ctx.dry_run:
        step.items.append(StepItem("powertoys_dryrun", "PowerToys settings restore (dry-run)", True, message=f"Would restore to: {dst}"))
        return
    ok, msg = copy_tree_best_effort(src, dst)
    step.items.append(StepItem("powertoys_restore", "PowerToys settings restore", ok, message=msg))


def capture_wsl(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    out_dir = ctx.bundle_dir / "tools" / "wsl"
    ensure_dir(out_dir)

    if which("wsl") is not None:
        it = run_cmd(ctx, step, "wsl_list", "WSL distro list (wsl -l -v)", ["wsl", "-l", "-v"], stream_cb=stream_cb, allow_fail=True)
        try:
            if it.stdout_path and Path(it.stdout_path).exists():
                shutil.copy2(it.stdout_path, out_dir / "wsl_list.txt")
                step.items.append(StepItem("wsl_list_saved", "Saved WSL list", True, message=str(out_dir / "wsl_list.txt")))
        except Exception:
            pass
    else:
        step.items.append(StepItem("wsl_missing", "WSL distro list", False, message="wsl.exe not found."))

    wslconfig = Path(os.environ.get("USERPROFILE", "")) / ".wslconfig"
    if wslconfig.exists():
        try:
            shutil.copy2(wslconfig, out_dir / ".wslconfig")
            step.items.append(StepItem("wslconfig_copy", "Copy .wslconfig", True, message=str(out_dir / ".wslconfig")))
        except Exception as e:
            step.items.append(StepItem("wslconfig_copy_err", "Copy .wslconfig", False, message=str(e)))
    else:
        step.items.append(StepItem("wslconfig_missing", "Copy .wslconfig", False, message=f"Not found: {wslconfig}"))


def apply_wsl(ctx: RunContext, step: StepReport) -> None:
    in_dir = ctx.bundle_dir / "tools" / "wsl"
    wslconfig_src = in_dir / ".wslconfig"
    wslconfig_dst = Path(os.environ.get("USERPROFILE", "")) / ".wslconfig"
    if not wslconfig_src.exists():
        step.items.append(StepItem("wslconfig_missing", "Restore .wslconfig", False, message=f"Missing in bundle: {wslconfig_src}"))
        return
    if ctx.dry_run:
        step.items.append(StepItem("wslconfig_dryrun", "Restore .wslconfig (dry-run)", True, message=f"Would restore to: {wslconfig_dst}"))
        return
    try:
        backup_if_exists(wslconfig_dst)
        shutil.copy2(wslconfig_src, wslconfig_dst)
        step.items.append(StepItem("wslconfig_restore", "Restore .wslconfig", True, message=str(wslconfig_dst)))
    except Exception as e:
        step.items.append(StepItem("wslconfig_restore_err", "Restore .wslconfig", False, message=str(e)))


def capture_onedrive_known_folders(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    out_dir = ctx.bundle_dir / "tools" / "onedrive_known_folders"
    ensure_dir(out_dir)

    env_keys = ["OneDrive", "OneDriveConsumer", "OneDriveCommercial", "OneDriveTenantName"]
    env_out = {k: os.environ.get(k, "") for k in env_keys}
    safe_write_json(out_dir / "onedrive_env.json", env_out)
    step.items.append(StepItem("onedrive_env", "OneDrive env paths (capture)", True, message=str(out_dir / "onedrive_env.json")))

    if not (is_windows() and which("powershell")):
        step.items.append(StepItem("kf_status", "Known folders (capture)", False, message="PowerShell not found."))
        return

    ps = r"""
$paths = @(
'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders',
'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
)
$out = @{}
foreach($p in $paths){
  try { $out[$p] = Get-ItemProperty $p -ErrorAction SilentlyContinue } catch {}
}
$out | ConvertTo-Json -Depth 4 -Compress
""".strip()

    it = run_cmd(
        ctx,
        step,
        "knownfolders",
        "Capture Known Folder paths (registry inventory only)",
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        stream_cb=stream_cb,
        allow_fail=True,
    )
    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            txt = Path(it.stdout_path).read_text(encoding="utf-8", errors="replace").strip()
            if txt:
                safe_write_text(out_dir / "known_folders.json", txt + "\n")
                step.items.append(StepItem("kf_saved", "Saved Known Folder paths", True, message=str(out_dir / "known_folders.json")))
    except Exception:
        pass


def capture_startup_inventory(ctx: RunContext, step: StepReport, stream_cb=None) -> None:
    out_dir = ctx.bundle_dir / "tools" / "startup_inventory"
    ensure_dir(out_dir)

    if not (is_windows() and which("powershell")):
        step.items.append(StepItem("startup_status", "Startup inventory", False, message="PowerShell not found."))
        return

    ps = r"""
$items = @()

# Startup folder (current user)
$sf = [Environment]::GetFolderPath('Startup')
if(Test-Path $sf){
  Get-ChildItem $sf -ErrorAction SilentlyContinue | ForEach-Object {
    $items += [PSCustomObject]@{ Source='StartupFolder'; Name=$_.Name; Path=$_.FullName }
  }
}

# Run keys (inventory only)
$runPaths = @(
'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run',
'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run',
'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'
)
foreach($rp in $runPaths){
  if(Test-Path $rp){
    $p = Get-ItemProperty $rp -ErrorAction SilentlyContinue
    $p.PSObject.Properties | Where-Object { $_.Name -notlike 'PS*' } | ForEach-Object {
      $items += [PSCustomObject]@{ Source=$rp; Name=$_.Name; Path=$_.Value }
    }
  }
}

$items | Sort-Object Source,Name | Format-Table -AutoSize | Out-String -Width 4096
""".strip()

    it = run_cmd(
        ctx,
        step,
        "startup_items",
        "Capture startup inventory (safe: inventory only)",
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        stream_cb=stream_cb,
        allow_fail=True,
    )
    try:
        if it.stdout_path and Path(it.stdout_path).exists():
            shutil.copy2(it.stdout_path, out_dir / "startup_items.txt")
            step.items.append(StepItem("startup_saved", "Saved startup inventory", True, message=str(out_dir / "startup_items.txt")))
    except Exception:
        pass


# -----------------------------
# Operations (Capture / Apply / Verify)
# -----------------------------


def op_capture(bundle_dir: Path, mode: str, dry_run: bool, toggles: Toggles, stream_cb=None) -> Tuple[RunContext, Dict[str, Any]]:
    started = datetime.now().isoformat(timespec="seconds")
    ctx = make_run_context(bundle_dir, mode, dry_run)
    steps: List[StepReport] = []

    ctx.hardware_match = "UNKNOWN"
    enforced = enforce_gates(ctx, toggles)
    ctx.disabled_features = compute_disabled_features(mode, ctx.hardware_match, toggles)

    s = StepReport(name="CAPTURE", started=started)
    steps.append(s)

    src_fp = capture_fingerprint(ctx, "source", stream_cb=stream_cb)
    safe_write_json(ctx.bundle_dir / "fingerprints" / "source_fingerprint.json", src_fp)

    if enforced.use_winget:
        capture_winget(ctx, s, stream_cb=stream_cb)
    if enforced.use_choco:
        capture_choco(ctx, s, stream_cb=stream_cb)
    if enforced.use_scoop:
        capture_scoop(ctx, s, stream_cb=stream_cb)

    capture_installed_apps_inventory(ctx, s, stream_cb=stream_cb)

    if enforced.cfg_git:
        capture_git(ctx, s, include_gitconfig=enforced.cfg_gitconfig_file, stream_cb=stream_cb)
    if enforced.cfg_ssh:
        capture_ssh(ctx, s, stream_cb=stream_cb)
    if enforced.cfg_vscode:
        capture_vscode(ctx, s, stream_cb=stream_cb)
    if enforced.cfg_windows_terminal:
        capture_windows_terminal(ctx, s, stream_cb=stream_cb)

    capture_timezone(ctx, s, stream_cb=stream_cb)
    capture_power_plan(ctx, s, stream_cb=stream_cb)

    if enforced.drv_inventory:
        capture_driver_inventory(ctx, s, stream_cb=stream_cb)
    if enforced.drv_oem_checklist:
        capture_oem_driver_checklist(ctx, s, src_fp)
    if enforced.drv_export_driverstore:
        capture_driverstore_export(ctx, s, stream_cb=stream_cb)

    # Browsers
    localapp = Path(os.environ.get("LOCALAPPDATA", ""))
    if enforced.br_chrome:
        capture_chromium_profile(ctx, s, "chrome", localapp / "Google" / "Chrome" / "User Data" / "Default", stream_cb=stream_cb)
    if enforced.br_edge:
        capture_chromium_profile(ctx, s, "edge", localapp / "Microsoft" / "Edge" / "User Data" / "Default", stream_cb=stream_cb)
    if enforced.br_firefox:
        capture_firefox(ctx, s, stream_cb=stream_cb)

    # Tools
    if enforced.tool_powertoys:
        capture_powertoys(ctx, s)
    if enforced.tool_wsl:
        capture_wsl(ctx, s, stream_cb=stream_cb)
    if enforced.tool_onedrive_known_folders:
        capture_onedrive_known_folders(ctx, s, stream_cb=stream_cb)
    if enforced.tool_startup_inventory:
        capture_startup_inventory(ctx, s, stream_cb=stream_cb)

    ended = datetime.now().isoformat(timespec="seconds")
    s.ended = ended
    report = write_report(ctx, steps, started, ended)
    write_summary(ctx, report, checklist=None)
    return ctx, report


def op_apply(bundle_dir: Path, mode: str, dry_run: bool, toggles: Toggles, stream_cb=None) -> Tuple[RunContext, Dict[str, Any]]:
    started = datetime.now().isoformat(timespec="seconds")
    ctx = make_run_context(bundle_dir, mode, dry_run)
    steps: List[StepReport] = []

    s0 = StepReport(name="APPLY", started=started)
    steps.append(s0)

    tgt_fp = capture_fingerprint(ctx, "target", stream_cb=stream_cb)
    safe_write_json(ctx.bundle_dir / "fingerprints" / "target_fingerprint.json", tgt_fp)

    src_fp = load_fingerprint(ctx.bundle_dir / "fingerprints" / "source_fingerprint.json")
    if src_fp:
        match, details = classify_hardware_match(src_fp, tgt_fp)
        ctx.hardware_match = match
        ctx.hardware_match_details = details
        append_log(ctx, f"[match] hardware_match={match} details={json.dumps(details)}", stream_cb=stream_cb)
    else:
        ctx.hardware_match = "UNKNOWN"
        ctx.hardware_match_details = {"notes": ["No source_fingerprint.json found; cannot classify match."]}

    ctx.disabled_features = compute_disabled_features(mode, ctx.hardware_match, toggles)
    enforced = enforce_gates(ctx, toggles)

    if enforced.use_winget:
        apply_winget(ctx, s0, stream_cb=stream_cb)
    if enforced.use_choco:
        apply_choco(ctx, s0, stream_cb=stream_cb)
    if enforced.use_scoop:
        apply_scoop(ctx, s0, stream_cb=stream_cb)

    if enforced.cfg_git:
        apply_git(ctx, s0, restore_gitconfig=enforced.cfg_gitconfig_file, stream_cb=stream_cb)
    if enforced.cfg_ssh:
        apply_ssh(ctx, s0, stream_cb=stream_cb)
    if enforced.cfg_vscode:
        apply_vscode(ctx, s0, stream_cb=stream_cb)
    if enforced.cfg_windows_terminal:
        apply_windows_terminal(ctx, s0, stream_cb=stream_cb)

    if enforced.win_tz_region:
        apply_timezone_region(ctx, s0, stream_cb=stream_cb)
    else:
        s0.items.append(StepItem("tz_region_skipped", "Timezone/Region apply", True, message="Skipped (disabled by policy or not selected)."))

    if enforced.win_power_plan:
        apply_power_plan(ctx, s0, stream_cb=stream_cb)
    else:
        s0.items.append(StepItem("powerplan_skipped", "Power plan apply", True, message="Skipped (disabled by policy or not selected)."))

    # DriverStore restore (HIGH RISK; gated)
    if enforced.drv_restore_driverstore:
        s0.items.append(StepItem("drvstore_warning", "DriverStore restore warning", True, message="HIGH RISK: restoring drivers can destabilize Windows. Only for SAME hardware with PASS match."))
        apply_driverstore_restore(ctx, s0, stream_cb=stream_cb)
    else:
        s0.items.append(StepItem("drvstore_restore_skipped", "DriverStore restore", True, message="Skipped (disabled by policy/gates or not selected)."))

    # Browsers restore (bookmarks + extensions only)
    localapp = Path(os.environ.get("LOCALAPPDATA", ""))
    if enforced.br_chrome:
        apply_chromium_profile(ctx, s0, "chrome", localapp / "Google" / "Chrome" / "User Data" / "Default", stream_cb=stream_cb)
    if enforced.br_edge:
        apply_chromium_profile(ctx, s0, "edge", localapp / "Microsoft" / "Edge" / "User Data" / "Default", stream_cb=stream_cb)
    if enforced.br_firefox:
        apply_firefox(ctx, s0, stream_cb=stream_cb)

    # Tools restore (safe)
    if enforced.tool_powertoys:
        apply_powertoys(ctx, s0)
    if enforced.tool_wsl:
        apply_wsl(ctx, s0)

    # Capture-only tools (explicitly not restored)
    if enforced.tool_onedrive_known_folders:
        s0.items.append(StepItem("onedrive_restore_skipped", "OneDrive / Known Folder restore", True, message="Capture-only (inventory). No changes applied."))
    if enforced.tool_startup_inventory:
        s0.items.append(StepItem("startup_restore_skipped", "Startup restore", True, message="Capture-only (inventory). No changes applied."))

    ended = datetime.now().isoformat(timespec="seconds")
    s0.ended = ended
    report = write_report(ctx, steps, started, ended)
    write_summary(ctx, report, checklist=None)
    return ctx, report


def op_verify(bundle_dir: Path, mode: str, dry_run: bool, toggles: Toggles, stream_cb=None) -> Tuple[RunContext, Dict[str, Any], List[str]]:
    started = datetime.now().isoformat(timespec="seconds")
    ctx = make_run_context(bundle_dir, mode, dry_run)
    steps: List[StepReport] = []

    s = StepReport(name="VERIFY", started=started)
    steps.append(s)

    tgt_fp = capture_fingerprint(ctx, "target", stream_cb=stream_cb)
    safe_write_json(ctx.bundle_dir / "fingerprints" / "target_fingerprint.json", tgt_fp)

    src_fp = load_fingerprint(ctx.bundle_dir / "fingerprints" / "source_fingerprint.json")
    if src_fp:
        match, details = classify_hardware_match(src_fp, tgt_fp)
        ctx.hardware_match = match
        ctx.hardware_match_details = details
        append_log(ctx, f"[match] hardware_match={match} details={json.dumps(details)}", stream_cb=stream_cb)
    else:
        ctx.hardware_match = "UNKNOWN"
        ctx.hardware_match_details = {"notes": ["No source_fingerprint.json found; cannot classify match."]}

    ctx.disabled_features = compute_disabled_features(mode, ctx.hardware_match, toggles)
    enforced = enforce_gates(ctx, toggles)

    run_cmd(ctx, s, "python_ver", "python --version", [sys.executable, "--version"], stream_cb=stream_cb, allow_fail=True)

    if enforced.use_winget:
        if which("winget") is not None:
            run_cmd(ctx, s, "winget_ver", "winget --version", ["winget", "--version"], stream_cb=stream_cb, allow_fail=True)
        else:
            s.items.append(StepItem("winget_missing", "winget --version", False, message="winget not found."))

    if enforced.cfg_git:
        if which("git") is not None:
            run_cmd(ctx, s, "git_ver", "git --version", ["git", "--version"], stream_cb=stream_cb, allow_fail=True)
        else:
            s.items.append(StepItem("git_missing", "git --version", False, message="git not found."))

    if enforced.cfg_vscode:
        if which("code") is not None:
            run_cmd(ctx, s, "code_ver", "code --version", ["code", "--version"], stream_cb=stream_cb, allow_fail=True)
        else:
            s.items.append(StepItem("code_missing", "code --version", False, message="code CLI not found."))

    checklist: List[str] = []
    if enforced.drv_checklist:
        checklist = verify_device_readiness(ctx, s, stream_cb=stream_cb)
    else:
        s.items.append(StepItem("drv_checklist_skipped", "Driver readiness checklist", True, message="Skipped (not selected)."))

    ended = datetime.now().isoformat(timespec="seconds")
    s.ended = ended
    report = write_report(ctx, steps, started, ended)
    write_summary(ctx, report, checklist=checklist)
    return ctx, report, checklist
