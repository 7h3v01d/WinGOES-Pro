# license_manager.py
# WinGOES Pro - License Management Module
# Handles license key validation, activation, and enforcement.
#
# License Key Format:  WGPRO-XXXXX-XXXXX-XXXXX-XXXXX
# Where X = alphanumeric (Base32 alphabet, uppercase)
#
# Key encoding:
#   Segment 1: Edition code + checksum seed
#   Segments 2-4: Encoded payload (machine-agnostic by design)
#   Segment 5: HMAC checksum (last 5 chars of HMAC-SHA256 keyed hash)
#
# This is a LOCAL validation model (no call-home required).
# Keys are cryptographically signed; forged keys will fail checksum.

from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

# ── Retail Config ─────────────────────────────────────────────────────────────

APP_NAME     = "WinGOES Pro"
APP_VERSION  = "2.0"
EDITION_NAME = "Professional"
LICENSE_FILE_NAME = "wingoes_pro.lic"

# HMAC signing secret (embedded). In a real product, obfuscate or
# store as a compiled constant. For a solo/indie product this is sufficient.
_SIGNING_SECRET = b"WinGOES-Pro-2025-RetailKey-DO-NOT-DISTRIBUTE"

# Edition codes encoded into key segment 1
EDITION_CODES = {
    "PRO":  "PR",
    "HOME": "HM",
    "TEAM": "TM",
}

# Base32 alphabet used for key generation
_B32_ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

# ── License Data ──────────────────────────────────────────────────────────────


@dataclass
class LicenseInfo:
    valid: bool
    key: str = ""
    edition: str = ""
    activated_date: str = ""
    machine_id: str = ""
    seat_name: str = ""
    error: str = ""
    trial: bool = False
    trial_days_remaining: int = 0

    def is_pro(self) -> bool:
        return self.valid and not self.trial

    def display_status(self) -> str:
        if self.trial:
            return f"Trial — {self.trial_days_remaining} day(s) remaining"
        if self.valid:
            return f"Licensed  •  {EDITION_NAME}"
        return f"Unlicensed  •  {self.error or 'No valid license found'}"


# ── Key Validation ─────────────────────────────────────────────────────────────


def _normalize_key(raw: str) -> str:
    """Strip whitespace and dashes, uppercase."""
    return raw.strip().upper().replace("-", "").replace(" ", "")


def _format_key(clean: str) -> str:
    """Format 25-char clean key as WGPRO-XXXXX-XXXXX-XXXXX-XXXXX."""
    if len(clean) != 25:
        return clean
    return f"WGPRO-{clean[0:5]}-{clean[5:10]}-{clean[10:15]}-{clean[15:20]}-{clean[20:25]}"


def _key_segments(raw: str) -> Optional[Tuple[str, str, str, str, str]]:
    """Parse key into 5 segments. Returns None if format is wrong."""
    # Accept with or without 'WGPRO-' prefix
    clean = _normalize_key(raw)
    if clean.startswith("WGPRO"):
        clean = clean[5:]  # strip prefix if present
    if len(clean) != 25:
        return None
    if not all(c in _B32_ALPHA for c in clean):
        return None
    return clean[0:5], clean[5:10], clean[10:15], clean[15:20], clean[20:25]


def _compute_checksum(segments: Tuple[str, str, str, str]) -> str:
    """Compute 5-char checksum from first 4 segments using HMAC-SHA256."""
    payload = "-".join(segments).encode("ascii")
    digest = hmac.new(_SIGNING_SECRET, payload, hashlib.sha256).hexdigest().upper()
    # Map hex chars into Base32 alphabet for uniformity
    mapped = ""
    for ch in digest[:10]:
        idx = int(ch, 16) % len(_B32_ALPHA)
        mapped += _B32_ALPHA[idx]
    return mapped[:5]


def validate_key(raw_key: str) -> Tuple[bool, str, str]:
    """
    Validate a license key.
    Returns (is_valid, edition_code, error_message).
    """
    if not raw_key or not raw_key.strip():
        return False, "", "No license key provided."

    segs = _key_segments(raw_key)
    if segs is None:
        return False, "", "Invalid key format. Expected: WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"

    s1, s2, s3, s4, s5 = segs

    # Verify checksum
    expected = _compute_checksum((s1, s2, s3, s4))
    if not hmac.compare_digest(expected, s5):
        return False, "", "Invalid license key — checksum mismatch. Please check the key and try again."

    # Decode edition from segment 1 prefix
    edition = "UNKNOWN"
    for ed_name, code in EDITION_CODES.items():
        if s1.startswith(code):
            edition = ed_name
            break

    return True, edition, ""


# ── Machine ID ────────────────────────────────────────────────────────────────


def get_machine_id() -> str:
    """
    Generate a stable machine identifier.
    Uses a combination of hostname + platform info, hashed.
    Not hardware-locked — allows reinstall on same machine.
    """
    parts = [
        platform.node(),
        platform.machine(),
        platform.processor(),
        os.environ.get("COMPUTERNAME", ""),
    ]
    raw = "|".join(p for p in parts if p).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16].upper()


# ── License File Persistence ───────────────────────────────────────────────────


def _get_license_path() -> Path:
    """Return the path to the stored license file."""
    # Store in %APPDATA%\WinGOES Pro\ on Windows, or ~/.wingoes_pro/ elsewhere
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home()
    lic_dir = base / "WinGOES Pro"
    lic_dir.mkdir(parents=True, exist_ok=True)
    return lic_dir / LICENSE_FILE_NAME


def _sign_stored_license(data: dict) -> str:
    """Create an integrity signature for the stored license."""
    payload = json.dumps({k: v for k, v in sorted(data.items()) if k != "sig"},
                         separators=(",", ":")).encode("utf-8")
    return hmac.new(_SIGNING_SECRET, payload, hashlib.sha256).hexdigest()


def save_license(key: str, edition: str, seat_name: str = "") -> bool:
    """Persist a validated license to disk. Returns True on success."""
    try:
        machine_id = get_machine_id()
        data = {
            "key": key.strip().upper(),
            "edition": edition,
            "activated_date": datetime.now(timezone.utc).isoformat(),
            "machine_id": machine_id,
            "seat_name": seat_name.strip(),
            "app_version": APP_VERSION,
        }
        data["sig"] = _sign_stored_license(data)
        path = _get_license_path()
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_stored_license() -> LicenseInfo:
    """
    Load and verify the stored license.
    Returns a LicenseInfo with valid=True if the license passes all checks.
    """
    path = _get_license_path()
    if not path.exists():
        return LicenseInfo(valid=False, error="No license file found.")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return LicenseInfo(valid=False, error="License file is corrupt or unreadable.")

    # Verify stored signature
    stored_sig = data.get("sig", "")
    expected_sig = _sign_stored_license(data)
    if not hmac.compare_digest(stored_sig, expected_sig):
        return LicenseInfo(valid=False, error="License file has been tampered with.")

    # Re-validate the key itself
    raw_key = data.get("key", "")
    ok, edition, err = validate_key(raw_key)
    if not ok:
        return LicenseInfo(valid=False, error=f"Stored key invalid: {err}")

    return LicenseInfo(
        valid=True,
        key=raw_key,
        edition=edition,
        activated_date=data.get("activated_date", ""),
        machine_id=data.get("machine_id", ""),
        seat_name=data.get("seat_name", ""),
    )


def deactivate_license() -> bool:
    """Remove the stored license file."""
    try:
        path = _get_license_path()
        if path.exists():
            path.unlink()
        return True
    except Exception:
        return False


# ── Trial Mode ────────────────────────────────────────────────────────────────

TRIAL_DAYS = 14
_TRIAL_FILE_NAME = "wingoes_trial.json"


def _get_trial_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home()
    return base / "WinGOES Pro" / _TRIAL_FILE_NAME


def get_or_create_trial() -> LicenseInfo:
    """
    Manage a 14-day trial. Returns LicenseInfo with trial=True if active.
    """
    path = _get_trial_path()
    now_ts = time.time()

    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            start_ts = float(data.get("start_ts", 0))
            elapsed_days = (now_ts - start_ts) / 86400
            remaining = max(0, TRIAL_DAYS - int(elapsed_days))
            if remaining > 0:
                return LicenseInfo(
                    valid=True,
                    trial=True,
                    trial_days_remaining=remaining,
                    activated_date=datetime.fromtimestamp(start_ts).isoformat(),
                )
            else:
                return LicenseInfo(
                    valid=False,
                    trial=True,
                    trial_days_remaining=0,
                    error="Trial period has expired. Please purchase a license.",
                )
        except Exception:
            pass

    # First run — start trial
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"start_ts": now_ts}), encoding="utf-8")
    except Exception:
        pass

    return LicenseInfo(
        valid=True,
        trial=True,
        trial_days_remaining=TRIAL_DAYS,
        activated_date=datetime.fromtimestamp(now_ts).isoformat(),
    )


# ── Primary Entry Point ────────────────────────────────────────────────────────


def check_license() -> LicenseInfo:
    """
    Master license check. Returns the best available license state:
      1. Valid stored license → return it.
      2. Active trial → return trial info.
      3. Expired trial / no license → return invalid with error.
    """
    stored = load_stored_license()
    if stored.valid:
        return stored

    # Fall back to trial
    trial = get_or_create_trial()
    return trial


# ── Key Generator (for offline key issuance / dev use) ────────────────────────


def generate_key(edition: str = "PRO") -> str:
    """
    Generate a valid signed license key.
    For use by the developer/publisher to issue keys to customers.
    NOT exposed in the end-user UI.
    """
    import secrets

    code = EDITION_CODES.get(edition.upper(), "PR")

    def rand_seg(prefix: str = "") -> str:
        chars = [_B32_ALPHA[secrets.randbelow(len(_B32_ALPHA))] for _ in range(5 - len(prefix))]
        return prefix + "".join(chars)

    s1 = rand_seg(code)
    s2 = rand_seg()
    s3 = rand_seg()
    s4 = rand_seg()
    s5 = _compute_checksum((s1, s2, s3, s4))

    clean = s1 + s2 + s3 + s4 + s5
    return f"WGPRO-{clean[0:5]}-{clean[5:10]}-{clean[10:15]}-{clean[15:20]}-{clean[20:25]}"


# ── CLI helper (python license_manager.py genkey) ─────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "genkey":
        edition = sys.argv[2].upper() if len(sys.argv) >= 3 else "PRO"
        key = generate_key(edition)
        print(f"Generated {edition} key: {key}")
        ok, ed, err = validate_key(key)
        print(f"Self-validation: valid={ok} edition={ed} err={err!r}")
    elif len(sys.argv) >= 2 and sys.argv[1] == "validate":
        key = sys.argv[2] if len(sys.argv) >= 3 else ""
        ok, ed, err = validate_key(key)
        print(f"valid={ok} edition={ed} err={err!r}")
    else:
        print("Usage:")
        print("  python license_manager.py genkey [PRO|HOME|TEAM]")
        print("  python license_manager.py validate <KEY>")
