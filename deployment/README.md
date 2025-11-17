# Visant Device Deployment Guide

This directory contains documentation for deploying Visant camera devices to Raspberry Pi hardware.

---

## Quick Navigation

### Getting Started
- **[QUICK-START.md](QUICK-START.md)** - Condensed reference card for field deployment

### Full Deployment Guides
- **[DEPLOYMENT_V1.md](DEPLOYMENT_V1.md)** - Route 1: Fresh installation (v1.0 polling architecture)
- **[DEPLOYMENT_V2.md](DEPLOYMENT_V2.md)** - v2.0 cloud-triggered SSE architecture
- **[CLONING.md](CLONING.md)** - Route 2: Golden image cloning for fleet deployment

### Component Setup
- **[NETWORK-SETUP.md](NETWORK-SETUP.md)** - WiFi configuration (Comitup web interface, addwifi.sh script)
- **[TAILSCALE.md](TAILSCALE.md)** - Remote access VPN for fleet management
- **[UNINSTALL.md](UNINSTALL.md)** - Safe uninstallation procedure

---

## Which Guide Should I Use?

### Step 1: Choose Your Architecture

**v1.0 (Polling Architecture)** - Original version
- Device polls cloud server every N seconds
- Simpler setup, good for testing
- Use: [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md)

**v2.0 (Cloud-Triggered Architecture)** - Recommended
- Cloud server pushes commands via Server-Sent Events (SSE)
- More efficient, near-instant response
- Use: [DEPLOYMENT_V2.md](DEPLOYMENT_V2.md)

### Step 2: Choose Your Deployment Method

**Route 1: Fresh Installation** (1-5 devices)
- Install from scratch on each device
- More flexible, easier to customize
- Takes 15-20 minutes per device
- Use: [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md) or [DEPLOYMENT_V2.md](DEPLOYMENT_V2.md)

**Route 2: Golden Image Cloning** (5+ devices)
- Create one master image, clone to all devices
- Faster for fleet deployment (5 minutes per device after initial setup)
- Requires SD card reader/writer
- Use: [CLONING.md](CLONING.md)

---

## Typical Workflows

### First-Time Deployment (1 device)

```
1. Read QUICK-START.md (5 min)
2. Follow DEPLOYMENT_V2.md (20 min)
3. Setup WiFi using NETWORK-SETUP.md (5 min)
4. Optional: Setup Tailscale using TAILSCALE.md (10 min)
```

**Total Time:** 40 minutes

### Fleet Deployment (10+ devices)

```
1. Create golden image using CLONING.md Part 1 (30 min one-time)
2. Clone to each device using CLONING.md Part 2 (5 min per device)
3. Customize WiFi/device ID using customize_clone.sh (2 min per device)
4. Verify using verify_deployment.sh (1 min per device)
```

**Total Time:** 30 min setup + 8 min per device

### On-Site Installation (Non-Technical)

```
1. Print QUICK-START.md as reference card
2. Boot device (pre-configured golden image)
3. Connect to "visant-XXXXXX" WiFi hotspot (auto-created by Comitup)
4. Visit http://10.41.0.1 in browser
5. Select site WiFi network and enter password
6. Device connects and auto-activates
```

**Total Time:** 3 minutes

---

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4 (4GB+ RAM recommended) or Raspberry Pi 5
- USB webcam (UVC compatible)
- MicroSD card (32GB+ recommended)
- Power supply (official Raspberry Pi USB-C 5V/3A)

### Software Requirements
- Raspberry Pi OS Lite (64-bit) - Bookworm or later
- Internet connection (WiFi or Ethernet)
- Cloud server running Visant (https://app.visant.ai)

### Access Requirements
- Activation code from Visant cloud admin
- WiFi credentials for site network
- SSH access (for fresh installation)

---

## Network Setup Options

Three methods available (see [NETWORK-SETUP.md](NETWORK-SETUP.md)):

**1. Comitup Web Interface** (Recommended for field deployment)
- Device creates WiFi hotspot automatically
- Configure via web browser (no SSH needed)
- Best for: Non-technical installers, on-site deployment

**2. addwifi.sh Script** (For technical users)
- Command-line WiFi configuration
- Supports multiple networks, priority management
- Best for: Remote SSH access, batch configuration

**3. Manual wpa_supplicant** (Advanced)
- Direct configuration file editing
- Full control over WiFi settings
- Best for: Advanced users, special network requirements

---

## Remote Access

Tailscale VPN provides secure remote access to devices:
- SSH from anywhere without port forwarding
- VNC desktop access
- Fleet-wide management
- See: [TAILSCALE.md](TAILSCALE.md)

---

## Troubleshooting

### Quick Fixes

**Device not connecting to WiFi**
```bash
sudo systemctl status wpa_supplicant
sudo journalctl -u wpa_supplicant -n 50
```

**Service not starting**
```bash
sudo systemctl status visant-device-v2
sudo journalctl -u visant-device-v2 -n 50
```

**Camera not found**
```bash
v4l2-ctl --list-devices
```

**Full diagnostics**
```bash
./verify_deployment.sh
```

### Detailed Troubleshooting
- See troubleshooting sections in each guide
- [NETWORK-SETUP.md](NETWORK-SETUP.md) - WiFi issues
- [TAILSCALE.md](TAILSCALE.md) - Remote access issues
- [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md) or [DEPLOYMENT_V2.md](DEPLOYMENT_V2.md) - Service issues

---

## File Reference

### Documentation
- `README.md` - This file (overview)
- `QUICK-START.md` - Condensed reference card
- `DEPLOYMENT_V1.md` - Fresh install guide (v1.0)
- `DEPLOYMENT_V2.md` - Fresh install guide (v2.0)
- `CLONING.md` - Golden image cloning
- `NETWORK-SETUP.md` - WiFi configuration
- `TAILSCALE.md` - Remote access setup
- `UNINSTALL.md` - Removal procedure

### Scripts
- `install_device.sh` - Main installation script
- `addwifi.sh` - WiFi configuration tool
- `customize_clone.sh` - Post-clone customization
- `prepare_for_clone.sh` - Prepare device for imaging
- `verify_deployment.sh` - Installation verification
- `update_device.sh` - Manual update trigger
- `uninstall.sh` - Uninstallation script
- `install_comitup.sh` - Comitup installer
- `install_tailscale.sh` - Tailscale installer

### Service Files
- `visant-device-v2.service` - Main v2.0 device service
- `visant-update.service` - Scheduled update service
- `visant-update.timer` - Update timer (daily)

---

## Support & Resources

- **Cloud Dashboard:** https://app.visant.ai
- **GitHub Issues:** Report bugs and feature requests
- **Documentation Updates:** Check for latest version

---

## Version History

See [CHANGELOG.md](../../docs/CHANGELOG.md) for version information.

**Current Documentation Version:** 2025-11-17

---

## Quick Command Reference

```bash
# Service management
sudo systemctl status visant-device-v2
sudo systemctl restart visant-device-v2
sudo journalctl -u visant-device-v2 -f

# Updates
sudo systemctl start visant-update.service

# WiFi
sudo ./addwifi.sh "NetworkName" "password"

# Verification
./verify_deployment.sh

# Uninstall
sudo ./uninstall.sh
```

---

**Need help?** Start with [QUICK-START.md](QUICK-START.md) for a condensed overview, then refer to the detailed guides as needed.
