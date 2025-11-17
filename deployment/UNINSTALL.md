# Visant Uninstall Guide

This guide explains how to completely uninstall Visant from your Raspberry Pi device.

## Overview

The uninstall script removes all Visant components **except Tailscale**, which is preserved to maintain remote access to the device.

## What Gets Removed

The uninstall process removes:

- ✗ **Visant Application** - Complete removal of `/opt/visant` directory
  - Source code and virtual environment
  - Configuration files (`.env.device`)
  - All captured images and debug data
  - Logs and temporary files

- ✗ **Systemd Services** - All Visant services
  - `visant-device-v2.service` - Main monitoring service
  - `visant-update.service` - Update service
  - `visant-update.timer` - Scheduled update timer

- ✗ **Comitup WiFi Hotspot** - Complete removal
  - Comitup service and package
  - Configuration files (`/etc/comitup.conf`)
  - Callback scripts
  - APT repository

- ✗ **Helper Scripts**
  - `addwifi.sh` - WiFi configuration tool
  - Update logs (`/var/log/visant-update.log`)

- ✗ **System Packages** (Optional)
  - Python libraries (OpenCV, NumPy, etc.)
  - Video utilities (v4l-utils, ffmpeg)
  - Development libraries

## What Gets Preserved

- ✓ **Tailscale** - Remote access maintained
  - Tailscale service continues running
  - Existing connections remain active
  - Device stays accessible remotely

## Usage

### Basic Uninstall

Remove Visant but keep system packages:

```bash
sudo ./deployment/uninstall.sh --keep-packages
```

### Complete Uninstall

Remove everything including system packages:

```bash
sudo ./deployment/uninstall.sh
```

### Non-Interactive Mode

Skip all confirmation prompts:

```bash
sudo ./deployment/uninstall.sh --yes
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--keep-packages` | Keep system packages (python3, opencv, ffmpeg, etc.) |
| `--yes` | Skip all confirmation prompts (auto-yes) |
| `--help` | Show help message and exit |

## Step-by-Step Process

The uninstall script performs the following steps:

1. **Stop Services** - Gracefully stops all Visant services
2. **Disable Services** - Removes services from auto-start
3. **Remove Service Files** - Deletes systemd service definitions
4. **Remove Application** - Deletes entire `/opt/visant` directory
5. **Remove Helper Scripts** - Deletes addwifi.sh and logs
6. **Uninstall Comitup** - Removes WiFi hotspot system
7. **Remove Packages** (Optional) - Uninstalls system dependencies

## Examples

### Recommended: Keep System Packages

Most users should keep system packages as they may be used by other applications:

```bash
sudo ./deployment/uninstall.sh --keep-packages
```

### Clean Slate: Remove Everything

For a complete system cleanup:

```bash
sudo ./deployment/uninstall.sh
```

The script will prompt you to confirm before removing system packages.

### Automated Uninstall

For scripted/automated uninstalls:

```bash
sudo ./deployment/uninstall.sh --keep-packages --yes
```

## Reinstallation

After uninstalling, you can reinstall Visant at any time.

### Safe Remote Reinstall (Recommended)

If you kept Tailscale running and are connected remotely, use the `--skip-tailscale` flag to prevent disconnection:

```bash
sudo ./deployment/install_device.sh --skip-tailscale
```

This preserves your existing Tailscale connection and prevents losing remote access during installation.

### Fresh Install

For a complete fresh installation including Tailscale reconfiguration:

```bash
sudo ./deployment/install_device.sh
```

The installer will detect existing Tailscale and prompt you whether to keep or reconfigure it.

### Installation Options

| Option | Description |
|--------|-------------|
| `--skip-tailscale` | Skip Tailscale (recommended for remote reinstalls) |
| `--install-tailscale` | Force Tailscale reconfiguration |
| `--tailscale-key KEY` | Reconfigure Tailscale with new auth key |

## Important Notes

### Data Loss Warning

⚠️ **All data will be permanently deleted**, including:
- Captured images in `debug_captures/`
- Configuration in `.env.device`
- Analysis results and logs

**There is no backup created automatically.** If you need to preserve any data, back it up manually before uninstalling.

### Manual Backup (Optional)

To backup your configuration before uninstalling:

```bash
# Backup configuration
sudo cp /opt/visant/.env.device ~/env.device.backup

# Backup captured images (if needed)
sudo cp -r /opt/visant/debug_captures ~/debug_captures_backup
```

After reinstalling, you can restore your configuration:

```bash
sudo cp ~/env.device.backup /opt/visant/.env.device
```

### Tailscale Preservation

The uninstall script explicitly **does not touch Tailscale**:
- Tailscale service remains running
- Tailscale configuration is unchanged
- Remote access via Tailscale continues working

This ensures you can reinstall Visant remotely without losing access to the device.

### System Packages

When deciding whether to remove system packages (`--keep-packages`), consider:

**Keep packages if:**
- You're not sure if other applications use them
- You plan to reinstall Visant soon
- You want faster reinstallation (no package download)

**Remove packages if:**
- You want a completely clean system
- You're repurposing the device for something else
- Disk space is limited

## Troubleshooting

### Permission Denied

Make sure to run with `sudo`:

```bash
sudo ./deployment/uninstall.sh
```

### Service Won't Stop

If a service fails to stop, force kill it:

```bash
sudo systemctl kill visant-device-v2.service
sudo systemctl kill visant-update.service
```

Then run the uninstall script again.

### Directory Won't Delete

If `/opt/visant` won't delete due to permissions:

```bash
sudo chmod -R 777 /opt/visant
sudo rm -rf /opt/visant
```

### Verify Complete Removal

To verify everything was removed:

```bash
# Check services
systemctl list-units | grep visant

# Check directories
ls -la /opt/visant

# Check processes
ps aux | grep visant

# Verify Tailscale still running
sudo tailscale status
```

## Getting Help

If you encounter issues:

1. Check the script output for error messages
2. Review system logs: `sudo journalctl -xe`
3. Consult the main README: `deployment/README.md`
4. Report issues on GitHub

## See Also

- [Installation Guide](README.md) - How to install Visant
- [Quick Start Guide](QUICK-START-ROUTE1.md) - Initial setup
- [WiFi Configuration](WIFI.md) - Network setup
- [Comitup Guide](COMITUP.md) - WiFi hotspot setup
