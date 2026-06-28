**WinGOES - GUI User Manual**

**Windows 10 Pro Rebuild & Migration Assistant**

**1\. What WinGOES Is (and What It Is Not)**

**WinGOES** is a guided assistant that helps you **safely rebuild or re-set up Windows 10 Pro** without dragging along old problems.

It is designed around one core idea:

**A clean Windows install is usually best - but your useful setup should not be lost.**

WinGOES lets you:

- Capture a snapshot of your current system
- Reinstall Windows cleanly
- Re-apply _only the safe, intentional parts_ of your setup

**WinGOES is NOT:**

- A full disk imaging or cloning tool
- A "restore everything exactly as it was" utility
- A risky driver-migration or registry-copying tool

This is intentional. WinGOES prioritizes **stability, clarity, and control** over convenience shortcuts.

**2\. Core Concepts (Plain English)**

Before using the GUI, it helps to understand three simple ideas.

**2.1 Capture → Apply → Verify**

WinGOES works in **three stages**:

- **CAPTURE**  
    Records what _can_ be safely re-applied later
- **APPLY**  
    Re-applies selected items to a fresh Windows install
- **VERIFY**  
    Confirms that your new system is healthy and ready

You can run these stages on different days and even different machines.

**2.2 Migration Modes (Very Important)**

WinGOES always operates in **one of three modes**.  
The mode determines what the tool will _allow_ and what it will _refuse_ to do.

**CLEAN REBUILD (Default - Recommended)**

Use when:

- You are reinstalling Windows fresh
- You want to eliminate old Windows issues
- You are moving to new hardware

What it does:

- Re-installs apps where possible
- Restores selected user tools and preferences
- **Blocks risky actions** (driver copying, system tweaks)

This is the safest and most common mode.

**SAME-HARDWARE TRANSFER (Advanced)**

Use only when:

- You are reinstalling Windows on **the same physical machine**
- You understand the risks

What it does:

- Allows more system-level restoration
- Still blocks known dangerous operations
- Requires hardware fingerprint matching

If the hardware does not match, WinGOES will automatically downgrade behavior.

**CUSTOM (Expert Use)**

Use when:

- You want full manual control
- You accept responsibility for advanced choices

Even in Custom mode, **WinGOES will still block actions known to cause system instability**.

**2.3 Hardware Fingerprints (Automatic Safety Check)**

WinGOES automatically creates a **hardware fingerprint**:

- CPU
- Motherboard
- Storage identity

This fingerprint is used to:

- Detect whether APPLY is happening on the same hardware
- Prevent unsafe driver or system transfers

You do **not** need to configure this. It is automatic.

**3\. The Main GUI Layout**

The WinGOES GUI is intentionally simple and linear.

You will typically see:

- **Mode Selection**
- **Feature Toggles**
- **Action Buttons** (CAPTURE / APPLY / VERIFY)
- **Live Log Panel**

**4\. Mode Selection (Top Section)**

**What This Does**

This determines the **rules** WinGOES will follow.

**How to Use It**

- Choose **CLEAN REBUILD** unless you have a very specific reason not to
- SAME-HARDWARE TRANSFER should only be selected if:
  - You are reinstalling Windows on the same PC
  - You understand that some system risks increase

**Example**

"I'm building a new PC and want my dev tools back, but none of the old Windows weirdness."

→ **CLEAN REBUILD**

**5\. Feature Toggles (What Gets Captured / Applied)**

Each toggle represents a **category of information**.

If a toggle is disabled by your selected mode, the GUI will show it as unavailable.

**5.1 Applications (Package Managers)**

**Winget**

Captures:

- Apps installed via Windows Package Manager
- App versions where available

Applies:

- Re-installs those apps automatically where possible

Important:

- Some apps cannot be reinstalled automatically (games, vendor installers, Microsoft Store apps)
- WinGOES records these safely but does not force reinstallation

**Example**

"I want my dev tools, browsers, and utilities back automatically."

Enable **Winget**

**Chocolatey / Scoop**

Same concept as Winget, for users who use these ecosystems.

Enable only if you actually use them.

**5.2 Developer & Power-User Tools**

**Git Configuration**

Captures:

- Global Git settings
- Optional .gitconfig file

Applies:

- Restores your Git identity and preferences

Example:

"I don't want to reconfigure Git name/email on a new install."

Enable **Git**

**SSH Keys**

Captures:

- ~/.ssh folder (keys, known hosts)

Applies:

- Restores SSH access for Git, servers, automation

Example:

"I need my SSH keys for GitHub and servers."

Enable **SSH**

**VS Code**

Captures:

- Extensions list
- Settings and keybindings

Applies:

- Re-installs extensions
- Restores preferences

Example:

"I want VS Code to feel exactly the same on the new install."

Enable **VS Code**

**Windows Terminal**

Captures:

- Terminal profiles
- Appearance and behavior settings

Applies:

- Restores terminal configuration

**5.3 Windows Settings (Safe Allowlist)**

These are **safe, reversible settings**.

**Timezone**

Captures and restores your timezone

**Power Plan**

Restores your preferred power profile (Balanced, High Performance, etc.)

In **CLEAN REBUILD**, these are often disabled by default to avoid unintended side effects.

**5.4 Drivers (Handled Carefully)**

WinGOES does **not** blindly copy drivers.

What it can do:

- Capture a **driver inventory**
- Produce a **post-install checklist**

What it will not do (by default):

- Copy drivers between machines
- Force old drivers onto new hardware

Example:

"I want to know what drivers I had, not copy them blindly."

Enable **Driver Inventory**

**6\. Action Buttons (The Workflow)**

**6.1 CAPTURE**

**When to use:**  
Before reinstalling Windows.

What happens:

- System snapshot is taken
- Selected data is saved into a **bundle folder**
- Nothing is changed on your system

Example workflow:

- Launch WinGOES
- Select CLEAN REBUILD
- Enable desired toggles
- Click **CAPTURE**
- Copy the bundle folder to external storage

**6.2 APPLY**

**When to use:**  
After installing fresh Windows.

What happens:

- Hardware fingerprint is checked
- Safe items are restored
- Apps are reinstalled where possible
- Risky actions are blocked automatically

You can use **Dry Run** mode to see what _would_ happen without changing anything.

Example:

"I want to see what WinGOES will do before it does it."

Enable **Dry Run**, then click **APPLY**

**6.3 VERIFY**

**When to use:**  
After APPLY is finished.

What happens:

- Confirms system health
- Checks key tools are present
- Generates a readiness checklist (especially for drivers)

Example:

"Did everything install correctly? What do I still need to do manually?"

Click **VERIFY**

**7\. The Live Log Panel (What You're Seeing Scroll)**

The log shows:

- What WinGOES is doing
- What it skips (and why)
- What succeeds
- What requires manual attention

**Important: Warnings vs Errors**

Many messages look scary but are **informational**, not failures.

Example:

"Installed package is not available from any source"

This means:

- Winget detected the app
- Winget cannot reinstall it automatically
- **Nothing is broken**

WinGOES records this so _you_ know what needs manual reinstall.

**8\. Common Real-World Scenarios**

**Scenario 1: New PC Build**

- Mode: CLEAN REBUILD
- Enable: Winget, Git, SSH, VS Code
- CAPTURE on old PC
- APPLY on new PC
- VERIFY

Result:

- Clean Windows
- Dev environment restored
- No legacy issues

**Scenario 2: Same PC, Fresh Windows**

- Mode: SAME-HARDWARE TRANSFER
- Enable extra options if needed
- Hardware fingerprint ensures safety

**Scenario 3: "I Just Want a Checklist"**

- Enable minimal toggles
- CAPTURE only
- Use inventory files as a reference

**9\. Final Notes & Best Practices**

- **CLEAN REBUILD is the safest choice**
- WinGOES intentionally refuses dangerous actions
- Logs are your friend, not a sign of failure
- Use Dry Run when unsure

**Windows 10 Pro Rebuild & Migration Assistant**

**1\. What WinGOES Is (and What It Is Not)**

**WinGOES** is a guided assistant that helps you **safely rebuild or re-set up Windows 10 Pro** without dragging along old problems.

It is designed around one core idea:

**A clean Windows install is usually best - but your useful setup should not be lost.**

WinGOES lets you:

- Capture a snapshot of your current system
- Reinstall Windows cleanly
- Re-apply _only the safe, intentional parts_ of your setup

**WinGOES is NOT:**

- A full disk imaging or cloning tool
- A "restore everything exactly as it was" utility
- A risky driver-migration or registry-copying tool

This is intentional. WinGOES prioritizes **stability, clarity, and control** over convenience shortcuts.

**2\. Core Concepts (Plain English)**

Before using the GUI, it helps to understand three simple ideas.

**2.1 Capture → Apply → Verify**

WinGOES works in **three stages**:

- **CAPTURE**  
    Records what _can_ be safely re-applied later
- **APPLY**  
    Re-applies selected items to a fresh Windows install
- **VERIFY**  
    Confirms that your new system is healthy and ready

You can run these stages on different days and even different machines.

**2.2 Migration Modes (Very Important)**

WinGOES always operates in **one of three modes**.  
The mode determines what the tool will _allow_ and what it will _refuse_ to do.

**CLEAN REBUILD (Default - Recommended)**

Use when:

- You are reinstalling Windows fresh
- You want to eliminate old Windows issues
- You are moving to new hardware

What it does:

- Re-installs apps where possible
- Restores selected user tools and preferences
- **Blocks risky actions** (driver copying, system tweaks)

This is the safest and most common mode.

**SAME-HARDWARE TRANSFER (Advanced)**

Use only when:

- You are reinstalling Windows on **the same physical machine**
- You understand the risks

What it does:

- Allows more system-level restoration
- Still blocks known dangerous operations
- Requires hardware fingerprint matching

If the hardware does not match, WinGOES will automatically downgrade behavior.

**CUSTOM (Expert Use)**

Use when:

- You want full manual control
- You accept responsibility for advanced choices

Even in Custom mode, **WinGOES will still block actions known to cause system instability**.

**2.3 Hardware Fingerprints (Automatic Safety Check)**

WinGOES automatically creates a **hardware fingerprint**:

- CPU
- Motherboard
- Storage identity

This fingerprint is used to:

- Detect whether APPLY is happening on the same hardware
- Prevent unsafe driver or system transfers

You do **not** need to configure this. It is automatic.

**3\. The Main GUI Layout**

The WinGOES GUI is intentionally simple and linear.

You will typically see:

- **Mode Selection**
- **Feature Toggles**
- **Action Buttons** (CAPTURE / APPLY / VERIFY)
- **Live Log Panel**

**4\. Mode Selection (Top Section)**

**What This Does**

This determines the **rules** WinGOES will follow.

**How to Use It**

- Choose **CLEAN REBUILD** unless you have a very specific reason not to
- SAME-HARDWARE TRANSFER should only be selected if:
  - You are reinstalling Windows on the same PC
  - You understand that some system risks increase

**Example**

"I'm building a new PC and want my dev tools back, but none of the old Windows weirdness."

→ **CLEAN REBUILD**

**5\. Feature Toggles (What Gets Captured / Applied)**

Each toggle represents a **category of information**.

If a toggle is disabled by your selected mode, the GUI will show it as unavailable.

**5.1 Applications (Package Managers)**

**Winget**

Captures:

- Apps installed via Windows Package Manager
- App versions where available

Applies:

- Re-installs those apps automatically where possible

Important:

- Some apps cannot be reinstalled automatically (games, vendor installers, Microsoft Store apps)
- WinGOES records these safely but does not force reinstallation

**Example**

"I want my dev tools, browsers, and utilities back automatically."

Enable **Winget**

**Chocolatey / Scoop**

Same concept as Winget, for users who use these ecosystems.

Enable only if you actually use them.

**5.2 Developer & Power-User Tools**

**Git Configuration**

Captures:

- Global Git settings
- Optional .gitconfig file

Applies:

- Restores your Git identity and preferences

Example:

"I don't want to reconfigure Git name/email on a new install."

Enable **Git**

**SSH Keys**

Captures:

- ~/.ssh folder (keys, known hosts)

Applies:

- Restores SSH access for Git, servers, automation

Example:

"I need my SSH keys for GitHub and servers."

Enable **SSH**

**VS Code**

Captures:

- Extensions list
- Settings and keybindings

Applies:

- Re-installs extensions
- Restores preferences

Example:

"I want VS Code to feel exactly the same on the new install."

Enable **VS Code**

**Windows Terminal**

Captures:

- Terminal profiles
- Appearance and behavior settings

Applies:

- Restores terminal configuration

**5.3 Windows Settings (Safe Allowlist)**

These are **safe, reversible settings**.

**Timezone**

Captures and restores your timezone

**Power Plan**

Restores your preferred power profile (Balanced, High Performance, etc.)

In **CLEAN REBUILD**, these are often disabled by default to avoid unintended side effects.

**5.4 Drivers (Handled Carefully)**

WinGOES does **not** blindly copy drivers.

What it can do:

- Capture a **driver inventory**
- Produce a **post-install checklist**

What it will not do (by default):

- Copy drivers between machines
- Force old drivers onto new hardware

Example:

"I want to know what drivers I had, not copy them blindly."

Enable **Driver Inventory**

**6\. Action Buttons (The Workflow)**

**6.1 CAPTURE**

**When to use:**  
Before reinstalling Windows.

What happens:

- System snapshot is taken
- Selected data is saved into a **bundle folder**
- Nothing is changed on your system

Example workflow:

- Launch WinGOES
- Select CLEAN REBUILD
- Enable desired toggles
- Click **CAPTURE**
- Copy the bundle folder to external storage

**6.2 APPLY**

**When to use:**  
After installing fresh Windows.

What happens:

- Hardware fingerprint is checked
- Safe items are restored
- Apps are reinstalled where possible
- Risky actions are blocked automatically

You can use **Dry Run** mode to see what _would_ happen without changing anything.

Example:

"I want to see what WinGOES will do before it does it."

Enable **Dry Run**, then click **APPLY**

**6.3 VERIFY**

**When to use:**  
After APPLY is finished.

What happens:

- Confirms system health
- Checks key tools are present
- Generates a readiness checklist (especially for drivers)

Example:

"Did everything install correctly? What do I still need to do manually?"

Click **VERIFY**

**7\. The Live Log Panel (What You're Seeing Scroll)**

The log shows:

- What WinGOES is doing
- What it skips (and why)
- What succeeds
- What requires manual attention

**Important: Warnings vs Errors**

Many messages look scary but are **informational**, not failures.

Example:

"Installed package is not available from any source"

This means:

- Winget detected the app
- Winget cannot reinstall it automatically
- **Nothing is broken**

WinGOES records this so _you_ know what needs manual reinstall.

**8\. Common Real-World Scenarios**

**Scenario 1: New PC Build**

- Mode: CLEAN REBUILD
- Enable: Winget, Git, SSH, VS Code
- CAPTURE on old PC
- APPLY on new PC
- VERIFY

Result:

- Clean Windows
- Dev environment restored
- No legacy issues

**Scenario 2: Same PC, Fresh Windows**

- Mode: SAME-HARDWARE TRANSFER
- Enable extra options if needed
- Hardware fingerprint ensures safety

**Scenario 3: "I Just Want a Checklist"**

- Enable minimal toggles
- CAPTURE only
- Use inventory files as a reference

**9\. Final Notes & Best Practices**

- **CLEAN REBUILD is the safest choice**
- WinGOES intentionally refuses dangerous actions
- Logs are your friend, not a sign of failure
- Use Dry Run when unsure