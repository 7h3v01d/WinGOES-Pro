# models_and_utils.py
from __future__ import annotations

import ctypes
import getpass
import json
import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Constants / Policy
# -----------------------------

APP_TITLE = "WinGOES Pro 2.0"

MODE_CLEAN = "CLEAN_REBUILD"
MODE_SAME = "SAME_HARDWARE_TRANSFER"
MODE_CUSTOM = "CUSTOM"
ALL_MODES = [MODE_CLEAN, MODE_SAME, MODE_CUSTOM]

MATCH_PASS = "PASS"
MATCH_PARTIAL = "PARTIAL"
MATCH_FAIL = "FAIL"

INTENTIONALLY_NOT_MIGRATED = [
    "Arbitrary registry blobs (.reg import/export)",
    "Shell/context-menu handlers (HKCR/HKLM shell extensions)",
    "Scheduled tasks migration",
    "Services migration",
    "Browser cookies/passwords",
]

# -----------------------------
# Utility
# -----------------------------


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def is_windows() -> bool:
    return os.name == "nt"


def is_admin() -> bool:
    if not is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    """Relaunch current script as admin via UAC. Returns True if ShellExecute was invoked."""
    if not is_windows():
        return False
    try:
        params = " ".join([f'"{a}"' if " " in a else a for a in sys.argv])
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        return rc > 32
    except Exception:
        return False


def safe_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding=encoding, errors="replace")


def safe_write_json(path: Path, obj: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8", errors="replace")


def backup_if_exists(path: Path) -> Optional[Path]:
    """If file exists, create a timestamped backup next to it and return backup path."""
    if path.exists() and path.is_file():
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        bak = path.with_name(f"{path.name}.bak_{stamp}")
        shutil.copy2(path, bak)
        return bak
    return None


def copy_tree_best_effort(src: Path, dst: Path) -> Tuple[bool, str]:
    """Copy directory tree best-effort. Returns (ok, message)."""
    try:
        if not src.exists():
            return False, f"Source not found: {src}"
        ensure_dir(dst)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return True, "Copied"
    except Exception as e:
        return False, f"Copy failed: {e}"


def which(exe: str) -> Optional[str]:
    return shutil.which(exe)


def _decode_stream_line(b: bytes) -> str:
    for enc in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            return b.decode(enc, errors="replace")
        except Exception:
            continue
    return b.decode("latin-1", errors="replace")


# -----------------------------
# Reporting
# -----------------------------


@dataclass
class StepItem:
    id: str
    description: str
    ok: bool
    rc: Optional[int] = None
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    message: str = ""


@dataclass
class StepReport:
    name: str
    started: str
    ended: str = ""
    ok: bool = True
    items: List[StepItem] = field(default_factory=list)


@dataclass
class RunContext:
    bundle_dir: Path
    run_id: str
    migration_mode: str
    dry_run: bool
    admin: bool
    run_dir: Path
    log_path: Path
    report_path: Path
    summary_path: Path
    hardware_match: str = "UNKNOWN"
    hardware_match_details: Dict[str, Any] = field(default_factory=dict)
    disabled_features: List[str] = field(default_factory=list)

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "start": self.run_id,
            "end": "",
            "hostname": platform.node(),
            "username": getpass.getuser(),
            "admin": self.admin,
            "os_build": get_os_build_best_effort(),
            "dry_run": self.dry_run,
            "migration_mode": self.migration_mode,
        }


# -----------------------------
# Logging + Command execution
# -----------------------------


def append_log(ctx: RunContext, line: str, stream_cb=None) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    text = f"{ts} {line}\n"
    ensure_dir(ctx.log_path.parent)
    with ctx.log_path.open("a", encoding="utf-8", errors="replace") as f:
        f.write(text)
    if stream_cb:
        stream_cb(text.rstrip("\n"))


def run_cmd(
    ctx: RunContext,
    step: StepReport,
    item_id: str,
    desc: str,
    cmd: List[str],
    cwd: Optional[Path] = None,
    shell: bool = False,
    env: Optional[Dict[str, str]] = None,
    stream_cb=None,
    allow_fail: bool = True,
    timeout_s: int = 180,
) -> StepItem:
    """
    Runs a command deterministically:
      - Captures stdout/stderr to files
      - Streams log lines in real-time
      - Enforces a hard timeout to prevent hangs
    """
    started = time.time()
    stdout_file = ctx.run_dir / "stdout" / f"{step.name}_{item_id}_stdout.txt"
    stderr_file = ctx.run_dir / "stderr" / f"{step.name}_{item_id}_stderr.txt"
    ensure_dir(stdout_file.parent)
    ensure_dir(stderr_file.parent)

    header = f"[cmd] {desc}\n  exec: {' '.join(cmd) if isinstance(cmd, list) else str(cmd)}\n  timeout_s={timeout_s}\n"
    append_log(ctx, header, stream_cb=stream_cb)

    q: "queue.Queue[Tuple[str, str]]" = queue.Queue()
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    def reader_thread(pipe, tag: str):
        try:
            for raw in iter(pipe.readline, b""):
                if not raw:
                    break
                line = _decode_stream_line(raw).rstrip("\r\n")
                q.put((tag, line))
        except Exception as e:
            q.put((tag, f"[reader_error] {e}"))
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    try:
        p = subprocess.Popen(
            cmd if not shell else " ".join(cmd),
            cwd=str(cwd) if cwd else None,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            bufsize=1,
        )

        t_out = threading.Thread(target=reader_thread, args=(p.stdout, "stdout"), daemon=True)
        t_err = threading.Thread(target=reader_thread, args=(p.stderr, "stderr"), daemon=True)
        t_out.start()
        t_err.start()

        timed_out = False
        deadline = time.time() + max(5, int(timeout_s))

        while True:
            drained_any = False
            while True:
                try:
                    tag, line = q.get_nowait()
                except queue.Empty:
                    break
                drained_any = True
                if tag == "stdout":
                    stdout_lines.append(line)
                    append_log(ctx, line, stream_cb=stream_cb)
                else:
                    stderr_lines.append(line)
                    append_log(ctx, f"[stderr] {line}", stream_cb=stream_cb)

            rc = p.poll()
            if rc is not None:
                flush_until = time.time() + 1.0
                while time.time() < flush_until:
                    try:
                        tag, line = q.get_nowait()
                    except queue.Empty:
                        break
                    if tag == "stdout":
                        stdout_lines.append(line)
                        append_log(ctx, line, stream_cb=stream_cb)
                    else:
                        stderr_lines.append(line)
                        append_log(ctx, f"[stderr] {line}", stream_cb=stream_cb)
                break

            if time.time() > deadline:
                timed_out = True
                try:
                    append_log(ctx, f"[timeout] Killing process after {timeout_s}s: {desc}", stream_cb=stream_cb)
                    p.kill()
                except Exception:
                    pass
                break

            if not drained_any:
                time.sleep(0.05)

        try:
            rc = p.wait(timeout=5)
        except Exception:
            rc = p.returncode if p.returncode is not None else -1

        duration = time.time() - started

        safe_write_text(stdout_file, "\n".join(stdout_lines) + "\n")
        safe_write_text(stderr_file, "\n".join(stderr_lines) + "\n")

        ok = (rc == 0) and not timed_out
        msg = f"rc={rc} duration={duration:.2f}s"
        if timed_out:
            msg = f"TIMEOUT after {timeout_s}s (rc={rc}) duration={duration:.2f}s"

        append_log(ctx, f"[done] {desc} -> {msg}", stream_cb=stream_cb)

        it = StepItem(
            id=item_id,
            description=desc,
            ok=ok,
            rc=rc,
            stdout_path=str(stdout_file),
            stderr_path=str(stderr_file),
            message=msg,
        )
        step.items.append(it)

        if timed_out and not allow_fail:
            step.ok = False
        return it

    except FileNotFoundError as e:
        safe_write_text(stdout_file, "")
        safe_write_text(stderr_file, str(e))
        exe = ""
        try:
            exe = cmd[0] if isinstance(cmd, list) and cmd else ""
        except Exception:
            exe = ""
        msg = f"Not found: {exe or 'command'} (not on PATH or not installed)"
        append_log(ctx, f"[notfound] {desc} -> {msg}", stream_cb=stream_cb)

        it = StepItem(
            id=item_id,
            description=desc,
            ok=False,
            rc=127,
            stdout_path=str(stdout_file),
            stderr_path=str(stderr_file),
            message=msg,
        )
        step.items.append(it)

        if not allow_fail:
            step.ok = False
        return it

    except Exception as e:
        safe_write_text(stdout_file, "")
        safe_write_text(stderr_file, str(e))
        msg = f"Exception: {e}"
        append_log(ctx, f"[error] {desc} -> {msg}", stream_cb=stream_cb)

        it = StepItem(
            id=item_id,
            description=desc,
            ok=False,
            rc=-1,
            stdout_path=str(stdout_file),
            stderr_path=str(stderr_file),
            message=msg,
        )
        step.items.append(it)

        if not allow_fail:
            step.ok = False
        return it


# -----------------------------
# OS / Fingerprints / Matching
# -----------------------------


def get_os_build_best_effort() -> Dict[str, Any]:
    """Best-effort Windows edition/version/build. Avoids fragile registry parsing."""
    info = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "win32_ver": platform.win32_ver(),
    }
    if is_windows() and which("powershell"):
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-ComputerInfo | Select-Object WindowsProductName,WindowsVersion,OsBuildNumber,OsHardwareAbstractionLayer | ConvertTo-Json -Compress",
            ]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            if p.returncode == 0 and p.stdout.strip():
                info["computer_info"] = json.loads(p.stdout)
            else:
                info["computer_info_error"] = p.stderr.strip()
        except Exception as e:
            info["computer_info_error"] = str(e)
    return info


def powershell_json(command: str, timeout_s: int = 30) -> Tuple[Optional[Any], str]:
    """Execute a PowerShell command that outputs JSON (ConvertTo-Json). Best-effort. Returns (obj, error_text)."""
    if not (is_windows() and which("powershell")):
        return None, "PowerShell not found"
    try:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        if p.returncode != 0:
            return None, p.stderr.strip() or f"rc={p.returncode}"
        out = p.stdout.strip()
        if not out:
            return None, "Empty output"
        return json.loads(out), ""
    except Exception as e:
        return None, str(e)


def capture_fingerprint(ctx: RunContext, which_fp: str, stream_cb=None) -> Dict[str, Any]:
    """
    Capture hardware fingerprint to bundle/fingerprints/<which_fp>_fingerprint.json
    Best-effort; handles missing cmdlets gracefully.
    """
    fp: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "hostname": platform.node(),
        "windows": get_os_build_best_effort(),
        "manufacturer_model": {},
        "bios": {},
        "baseboard": {},
        "cpu": {},
        "gpus": [],
        "nics": [],
    }

    append_log(ctx, f"[fingerprint] Capturing {which_fp} fingerprint (best-effort)", stream_cb=stream_cb)

    obj, err = powershell_json(
        "(Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model) | ConvertTo-Json -Compress",
        timeout_s=20,
    )
    if obj is not None:
        fp["manufacturer_model"] = obj
    elif err:
        fp["manufacturer_model_error"] = err

    obj, err = powershell_json(
        "(Get-CimInstance Win32_BIOS | Select-Object SerialNumber) | ConvertTo-Json -Compress",
        timeout_s=20,
    )
    if obj is not None:
        fp["bios"]["serial"] = obj.get("SerialNumber")
    elif err:
        fp["bios_serial_error"] = err

    obj, err = powershell_json(
        "(Get-CimInstance Win32_ComputerSystemProduct | Select-Object UUID) | ConvertTo-Json -Compress",
        timeout_s=20,
    )
    if obj is not None:
        fp["bios"]["uuid"] = obj.get("UUID")
    elif err:
        fp["bios_uuid_error"] = err

    obj, err = powershell_json(
        "(Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer,Product,SerialNumber) | ConvertTo-Json -Compress",
        timeout_s=20,
    )
    if obj is not None:
        fp["baseboard"] = obj
    elif err:
        fp["baseboard_error"] = err

    obj, err = powershell_json(
        "(Get-CimInstance Win32_Processor | Select-Object Name) | ConvertTo-Json -Compress",
        timeout_s=20,
    )
    if obj is not None:
        fp["cpu"]["name"] = obj.get("Name")
    elif err:
        fp["cpu_error"] = err

    gpus, err = powershell_json(
        "(@(Get-PnpDevice -Class Display -ErrorAction SilentlyContinue | Select-Object FriendlyName,InstanceId) ) | ConvertTo-Json -Compress",
        timeout_s=25,
    )
    gpu_list: List[Dict[str, Any]] = []
    if isinstance(gpus, dict):
        gpu_list = [gpus]
    elif isinstance(gpus, list):
        gpu_list = gpus
    if gpu_list:
        fp["gpus"] = [{"name": g.get("FriendlyName"), "pnp_device_id": g.get("InstanceId")} for g in gpu_list]
    elif err:
        fp["gpus_error"] = err

    nics, err = powershell_json(
        "(@(Get-NetAdapter -ErrorAction SilentlyContinue | Select-Object Name,InterfaceDescription,PnPDeviceID) ) | ConvertTo-Json -Compress",
        timeout_s=25,
    )
    nic_list: List[Dict[str, Any]] = []
    if isinstance(nics, dict):
        nic_list = [nics]
    elif isinstance(nics, list):
        nic_list = nics
    if nic_list:
        fp["nics"] = [
            {"name": n.get("Name") or n.get("InterfaceDescription"), "pnp_device_id": n.get("PnPDeviceID")}
            for n in nic_list
        ]
    elif err:
        fp["nics_error"] = err

    out_path = ctx.bundle_dir / "fingerprints" / f"{which_fp}_fingerprint.json"
    safe_write_json(out_path, fp)
    append_log(ctx, f"[fingerprint] Wrote {out_path}", stream_cb=stream_cb)
    return fp


def load_fingerprint(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def classify_hardware_match(source_fp: Dict[str, Any], target_fp: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Rules:
    - If BIOS UUID or serial matches -> PASS
    - Else if baseboard + CPU + at least one NIC PNPDeviceID matches -> PASS
    - Else if only CPU matches -> PARTIAL
    - Else -> FAIL
    """
    details: Dict[str, Any] = {
        "matched_fields": [],
        "notes": [],
    }

    def norm(s: Any) -> str:
        return (str(s).strip().lower() if s is not None else "")

    s_uuid = norm(source_fp.get("bios", {}).get("uuid"))
    t_uuid = norm(target_fp.get("bios", {}).get("uuid"))
    s_serial = norm(source_fp.get("bios", {}).get("serial"))
    t_serial = norm(target_fp.get("bios", {}).get("serial"))

    if s_uuid and t_uuid and s_uuid == t_uuid:
        details["matched_fields"].append("bios.uuid")
        return MATCH_PASS, details
    if s_serial and t_serial and s_serial == t_serial:
        details["matched_fields"].append("bios.serial")
        return MATCH_PASS, details

    s_bb = source_fp.get("baseboard", {}) or {}
    t_bb = target_fp.get("baseboard", {}) or {}
    s_bb_key = (norm(s_bb.get("Manufacturer")), norm(s_bb.get("Product")))
    t_bb_key = (norm(t_bb.get("Manufacturer")), norm(t_bb.get("Product")))

    s_cpu = norm((source_fp.get("cpu", {}) or {}).get("name"))
    t_cpu = norm((target_fp.get("cpu", {}) or {}).get("name"))

    cpu_match = bool(s_cpu and t_cpu and s_cpu == t_cpu)
    bb_match = bool(s_bb_key[0] and s_bb_key[1] and s_bb_key == t_bb_key)

    s_nics = source_fp.get("nics", []) or []
    t_nics = target_fp.get("nics", []) or []
    s_nic_ids = {norm(n.get("pnp_device_id")) for n in s_nics if norm(n.get("pnp_device_id"))}
    t_nic_ids = {norm(n.get("pnp_device_id")) for n in t_nics if norm(n.get("pnp_device_id"))}
    nic_overlap = sorted(list(s_nic_ids.intersection(t_nic_ids)))

    if bb_match:
        details["matched_fields"].append("baseboard.manufacturer+product")
    if cpu_match:
        details["matched_fields"].append("cpu.name")
    if nic_overlap:
        details["matched_fields"].append("nics.pnp_device_id(overlap)")
        details["nic_overlap"] = nic_overlap[:10]

    if bb_match and cpu_match and bool(nic_overlap):
        return MATCH_PASS, details
    if cpu_match:
        details["notes"].append("CPU matched but insufficient stable identifiers for PASS.")
        return MATCH_PARTIAL, details
    return MATCH_FAIL, details


# -----------------------------
# Policy / Gating
# -----------------------------


@dataclass
class Toggles:
    # Packages
    use_winget: bool = True
    use_choco: bool = False
    use_scoop: bool = False

    # Portable configs
    cfg_git: bool = True
    cfg_gitconfig_file: bool = True
    cfg_ssh: bool = True
    cfg_vscode: bool = True
    cfg_windows_terminal: bool = True

    # Windows settings allowlist
    win_tz_region: bool = False
    win_power_plan: bool = False

    # Drivers
    drv_inventory: bool = True
    drv_checklist: bool = True
    drv_oem_checklist: bool = True
    drv_export_driverstore: bool = False  # CAPTURE only (pnputil /export-driver)
    drv_restore_driverstore: bool = False  # APPLY only (pnputil /add-driver ... /install) (HIGH RISK)

    # Browsers (bookmarks + extensions only; never passwords by default)
    br_chrome: bool = False
    br_edge: bool = False
    br_firefox: bool = False
    br_passwords: bool = False  # must remain False by default (not implemented in v1)

    # Tools / additional captures
    tool_powertoys: bool = False
    tool_wsl: bool = False
    tool_onedrive_known_folders: bool = False  # capture-only (no restore)
    tool_startup_inventory: bool = True  # inventory-only (safe)

    # Expert high-risk (must remain off by default)
    risky_shell_context_menu: bool = False  # still off by default even in CUSTOM


def compute_disabled_features(mode: str, match: str, toggles: Toggles) -> List[str]:
    disabled: List[str] = []

    if mode == MODE_CLEAN:
        if toggles.win_tz_region or toggles.win_power_plan:
            disabled.append("Windows settings allowlist toggles are disabled in CLEAN_REBUILD (policy).")
        if toggles.drv_restore_driverstore or toggles.drv_export_driverstore:
            disabled.append("DriverStore backup/restore is disabled in CLEAN_REBUILD (policy).")

    # DriverStore restore is only allowed when hardware match PASS (and practically same-hardware)
    if (mode in (MODE_SAME, MODE_CUSTOM)) and match != MATCH_PASS:
        if toggles.drv_restore_driverstore:
            disabled.append(f"DriverStore restore disabled because hardware match is {match} (requires PASS).")
        if toggles.win_tz_region or toggles.win_power_plan:
            disabled.append(f"Windows settings transfer disabled because hardware match is {match} (requires PASS).")

    if toggles.br_passwords:
        disabled.append("Browser passwords/cookies are intentionally not supported in v1 (must remain OFF by default).")

    if toggles.risky_shell_context_menu:
        disabled.append(
            "Shell/context-menu migration is high risk and intentionally not implemented in v1 (remains OFF by default)."
        )

    return disabled


def enforce_gates(ctx: RunContext, toggles: Toggles) -> Toggles:
    """Engine enforcement of gates regardless of UI state. Returns a sanitized Toggles copy."""
    t = Toggles(**toggles.__dict__)

    # CLEAN policy
    if ctx.migration_mode == MODE_CLEAN:
        t.win_tz_region = False
        t.win_power_plan = False
        t.drv_export_driverstore = False
        t.drv_restore_driverstore = False
        t.risky_shell_context_menu = False

    # SAME/CUSTOM: restore gated by hardware PASS
    if ctx.migration_mode in (MODE_SAME, MODE_CUSTOM) and ctx.hardware_match != MATCH_PASS:
        t.win_tz_region = False
        t.win_power_plan = False
        t.drv_restore_driverstore = False

    # Never in v1
    t.br_passwords = False
    t.risky_shell_context_menu = False
    return t


def make_run_context(bundle_dir: Path, mode: str, dry_run: bool) -> RunContext:
    run_id = now_stamp()
    run_dir = bundle_dir / "runs" / run_id
    ensure_dir(run_dir)
    ctx = RunContext(
        bundle_dir=bundle_dir,
        run_id=run_id,
        migration_mode=mode,
        dry_run=dry_run,
        admin=is_admin(),
        run_dir=run_dir,
        log_path=run_dir / "run.log",
        report_path=run_dir / "report.json",
        summary_path=run_dir / "summary.txt",
    )
    safe_write_text(ctx.log_path, f"{APP_TITLE} run_id={run_id}\n")
    return ctx


def write_report(ctx: RunContext, steps: List[StepReport], started_iso: str, ended_iso: str) -> Dict[str, Any]:
    src_fp = load_fingerprint(ctx.bundle_dir / "fingerprints" / "source_fingerprint.json")
    tgt_fp = load_fingerprint(ctx.bundle_dir / "fingerprints" / "target_fingerprint.json")

    report = {
        "metadata": ctx.to_metadata(),
        "fingerprints": {
            "source_fingerprint": src_fp,
            "target_fingerprint": tgt_fp,
            "hardware_match": ctx.hardware_match,
            "hardware_match_details": ctx.hardware_match_details,
        },
        "steps": [
            {
                "name": s.name,
                "started": s.started,
                "ended": s.ended,
                "ok": s.ok,
                "items": [it.__dict__ for it in s.items],
            }
            for s in steps
        ],
        "policy_decisions": {
            "disabled_features_due_to_mode_or_hardware": ctx.disabled_features,
            "intentionally_not_migrated": INTENTIONALLY_NOT_MIGRATED,
        },
    }
    report["metadata"]["start"] = started_iso
    report["metadata"]["end"] = ended_iso
    safe_write_json(ctx.report_path, report)
    return report


def write_summary(ctx: RunContext, report: Dict[str, Any], checklist: Optional[List[str]] = None) -> None:
    lines: List[str] = []
    lines.append(APP_TITLE)
    lines.append(f"Run ID: {ctx.run_id}")
    lines.append(f"Bundle: {ctx.bundle_dir}")
    lines.append(f"Mode: {ctx.migration_mode}")
    lines.append(f"Dry-Run: {ctx.dry_run}")
    lines.append(f"Admin: {ctx.admin}")
    lines.append(f"Hardware match: {ctx.hardware_match}")
    if ctx.hardware_match_details:
        lines.append(f"Match details: {json.dumps(ctx.hardware_match_details, indent=2)}")
    if ctx.disabled_features:
        lines.append("Disabled features (policy/gates):")
        for d in ctx.disabled_features:
            lines.append(f"  - {d}")
    lines.append("")
    lines.append("Steps:")
    for s in report.get("steps", []):
        lines.append(f"  - {s.get('name')}: {'OK' if s.get('ok') else 'NOT OK'}")
        for it in s.get("items", []):
            status = "OK" if it.get("ok") else "NOT OK"
            lines.append(f"      * {it.get('id')}: {status} - {it.get('description')} :: {it.get('message')}")
    lines.append("")
    lines.append("Intentionally not migrated (by design):")
    for x in INTENTIONALLY_NOT_MIGRATED:
        lines.append(f"  - {x}")
    if checklist:
        lines.append("")
        lines.append("Verification checklist:")
        for c in checklist:
            lines.append(f"  - {c}")
    safe_write_text(ctx.summary_path, "\n".join(lines) + "\n")
