# WinGOES – Mode Selection Flowchart
### Which Mode Should I Use?
```text
┌──────────────────────────────────────────────┐
│ Are you reinstalling Windows 10 Pro?         │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│ Do you want to remove old Windows problems?  │
│ (context menu bugs, weird settings, issues) │
└──────────────────────────────────────────────┘
           │ YES                                │ NO / NOT SURE
           ▼                                    ▼
┌──────────────────────────────────────────────┐
│ Are you changing hardware (new PC, new MB)? │
└──────────────────────────────────────────────┘
           │ YES                                │ NO / SAME PC
           ▼                                    ▼
┌───────────────────────────────┐      ┌───────────────────────────────┐
│   ✅ CLEAN REBUILD             │      │ Do you need system-level       │
│   (RECOMMENDED)               │      │ settings or driver carry-over? │
└───────────────────────────────┘      └───────────────────────────────┘
                                                   │ NO
                                                   ▼
                                      ┌───────────────────────────────┐
                                      │   ✅ CLEAN REBUILD             │
                                      │   (Still Recommended)         │
                                      └───────────────────────────────┘
                                                   │ YES
                                                   ▼
┌──────────────────────────────────────────────┐
│ Are you reinstalling on the EXACT same PC?   │
│ (same motherboard, CPU, system identity)    │
└──────────────────────────────────────────────┘
                     │ YES
                     ▼
┌──────────────────────────────────────────────┐
│ Are you comfortable with advanced options    │
│ and understand driver/system risks?          │
└──────────────────────────────────────────────┘
           │ YES                                │ NO
           ▼                                    ▼
┌───────────────────────────────┐      ┌───────────────────────────────┐
│ ⚠️ SAME-HARDWARE TRANSFER      │      │   ✅ CLEAN REBUILD             │
│ (ADVANCED)                    │      │   (SAFER CHOICE)              │
└───────────────────────────────┘      └───────────────────────────────┘
```
---

## Mode Summary (Quick Reference)
##✅ CLEAN REBUILD (Default – Recommended)

Use when:

- New PC or upgraded hardware
- Fresh Windows install
- You want to eliminate old Windows issues
- You are unsure which mode to choose

What it does:

- Reinstalls apps where possible
- Restores safe, portable configs
- Blocks risky system migrations

---

⚠️ SAME-HARDWARE TRANSFER (Advanced)

Use only when:

- Reinstalling Windows on the same physical machine
- Hardware fingerprint matches
- You understand the risks

What it allows:

- Limited system settings restoration
- Advanced options (still gated and safety-checked)

If hardware does not match:

- WinGOES automatically disables risky features

---

## 🧪 CUSTOM (Expert Use Only)

Use when:

- You want full manual control
- You accept responsibility for advanced decisions

Even in CUSTOM mode:

- Known dangerous actions remain blocked
- Safety gates still apply

---

## Golden Rule

If you ever hesitate, choose CLEAN REBUILD.
It is always safe, always supported, and always reversible.
