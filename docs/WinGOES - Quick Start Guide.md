**WinGOES - Quick Start Guide**

**Windows 10 Pro Rebuild & Migration Assistant**

**What WinGOES Does**

WinGOES helps you **reinstall Windows cleanly** while safely restoring your **apps and personal setup** - without bringing old Windows problems with you.

It works in three steps:  
**CAPTURE → APPLY → VERIFY**

**Step 1 - Choose the Right Mode**

☑ **CLEAN REBUILD (Recommended)**  
Use for:

- New PC
- Fresh Windows install
- Eliminating old Windows issues

✔ Safest option  
✔ Blocks risky system transfers

☐ SAME-HARDWARE TRANSFER (Advanced)  
Use **only** if reinstalling Windows on the **same PC**  
Requires hardware match

☐ CUSTOM (Expert)  
Manual control, still enforces safety limits

**If unsure: choose CLEAN REBUILD**

**Step 2 - Select What You Want to Keep**

Enable only what you actually use:

☐ **Applications**

- Winget (recommended)
- Chocolatey / Scoop (if used)

☐ **Developer & Power Tools**

- Git config
- SSH keys
- VS Code (extensions + settings)
- Windows Terminal

☐ **Windows Settings (Safe Only)**

- Timezone
- Power plan

☐ **Drivers**

- Inventory & checklist only  
    (Drivers are NOT copied automatically)

**Step 3 - CAPTURE (Before Reinstalling Windows)**

- Open WinGOES on your **current Windows install**
- Select your mode and toggles
- Click **CAPTURE**
- Wait for completion
- Copy the **bundle folder** to:
  - USB drive, or
  - External disk, or
  - Network location

✔ Nothing is changed on your system  
✔ This step is safe and repeatable

**Step 4 - Install Windows Cleanly**

- Perform a normal **Windows 10 Pro clean install**
- Complete initial Windows setup
- Log into your account

Do **not** copy old system folders or drivers.

**Step 5 - APPLY (After Windows Is Installed)**

- Copy the saved **bundle folder** to the new system
- Open WinGOES
- Select the **same mode** used during CAPTURE
- (Optional) Enable **Dry Run** to preview actions
- Click **APPLY**

✔ Apps are reinstalled where possible  
✔ Settings are restored safely  
✔ Risky actions are blocked automatically

**Step 6 - VERIFY (Final Check)**

Click **VERIFY** to:

- Confirm key tools are installed
- Check system readiness
- Generate a driver/setup checklist

Use the checklist to finish any **manual installs** (GPU driver, chipset, etc.).

**Reading the Log (Important)**

Messages like:

"Installed package is not available from any source"

**Are normal.**  
They mean:

- The app was detected
- It cannot be auto-installed
- You may reinstall it manually later

Only messages marked **fatal** indicate real problems.

**Best Practices**

✔ Use **CLEAN REBUILD** unless you are certain  
✔ Keep your bundle backed up  
✔ Use **Dry Run** if unsure  
✔ Read the VERIFY checklist  
✔ Do not force driver transfers

**In One Sentence**

**WinGOES gives you a clean Windows install - with your useful setup restored and your old problems left behind.**