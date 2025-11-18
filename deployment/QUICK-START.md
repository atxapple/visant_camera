# Quick Start Guide: Device Deployment

**Print and laminate this guide for field technicians**

---

## Purpose

This guide provides two deployment methods for OK Monitor devices. Choose the route that best fits your deployment scenario.

**Who should use this:**
- Field technicians deploying devices
- System administrators setting up monitoring infrastructure
- Anyone installing OK Monitor on Raspberry Pi 5 devices

---

## Choosing Your Deployment Method

| Factor | Route 1: Fresh Installation | Route 2: Golden Image Cloning |
|--------|----------------------------|-------------------------------|
| **Best for** | Single devices, testing, custom configs | Multiple devices, standardized deployments |
| **Time per device** | ~30 minutes | ~5 minutes (after image created) |
| **Requires** | Internet connection on device | SD card reader, golden image file |
| **Flexibility** | High - customize everything | Medium - customize ID and network |
| **Network setup** | Can configure WiFi during install | Configure WiFi after cloning |
| **Updates** | Gets latest code from GitHub | Uses snapshot from image creation |

**Decision Guide:**
- **Deploying 1-2 devices?** → Use Route 1
- **Deploying 3+ identical devices?** → Use Route 2
- **Testing or development?** → Use Route 1
- **Production rollout?** → Use Route 2
- **No internet at deployment site?** → Use Route 2

---

## Route 1: Fresh Installation

**Time required:** ~30 minutes per device

### Before You Start

**What you need:**
- ☐ Raspberry Pi 5 with Raspberry Pi OS Bookworm installed
- ☐ SSH enabled (via raspi-config or Imager settings)
- ☐ Internet connection (Ethernet or WiFi)
- ☐ USB webcam connected
- ☐ Cloud API URL (e.g., `https://okmonitor-production.up.railway.app`)
- ☐ Device ID chosen (e.g., `okmonitor1`, `floor-01-cam`)

---

### Step-by-Step Installation

#### 1. Connect to Device
```bash
# Find device IP (if using DHCP) or use hostname
ssh mok@okmonitor.local
# Enter password when prompted
```
☐ Connected via SSH

---

#### 2. Clone Repository
```bash
cd ~
git clone https://github.com/atxapple/okmonitor.git
cd okmonitor
```
☐ Repository cloned

---

#### 3. Configure Device Settings
```bash
# Create configuration directory
sudo mkdir -p /opt/okmonitor
sudo nano /opt/okmonitor/.env.device
```

**Enter these values:**
```bash
API_URL=https://okmonitor-production.up.railway.app
DEVICE_ID=okmonitor1                    # ← Change this! (used for Tailscale name)
CAMERA_SOURCE=0                         # Usually 0
```

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

☐ Configuration created

---

#### 4. Run Installer
```bash
sudo chmod +x deployment/install_device.sh

# Fresh install with Tailscale (recommended) - replace floor-01 with your device ID
sudo deployment/install_device.sh --device-id floor-01 --tailscale-key tskey-auth-xxxxx

# Fresh install without Tailscale
sudo deployment/install_device.sh --device-id floor-01

# Reinstall (skip Tailscale - safe for remote work)
sudo deployment/install_device.sh --device-id floor-01 --skip-tailscale
```

**What this does:**
- Installs system dependencies
- Sets up Python environment
- Installs OK Monitor software
- Creates systemd services
- Installs Comitup (WiFi hotspot for easy on-site setup)
- Installs addwifi.sh (backup WiFi configuration tool)
- Configures Tailscale (detects existing connections, asks before changes)

**Note:** Use `--skip-tailscale` when reinstalling remotely to avoid disconnection.

**Time:** ~15 minutes

☐ Installer completed

---

#### 5. Configure WiFi (if needed)

**Method A: Comitup Web Interface** (Recommended - no SSH needed!)
```bash
# 1. Reboot device: sudo reboot
# 2. Connect phone/laptop to 'okmonitor-XXXX' WiFi (no password)
# 3. Open browser to: http://10.41.0.1
# 4. Select customer WiFi and enter password
# Device automatically connects and starts monitoring!
```
📖 **Full guide:** [COMITUP.md](COMITUP.md)

**Method B: addwifi.sh Script** (Backup method with SSH)
```bash
# Add WiFi network:
~/addwifi.sh "Network-Name" "wifi-password" 100

# Verify connection:
ping -c 3 8.8.8.8
```
📖 **Full guide:** [WIFI.md](WIFI.md)

☐ WiFi configured (if needed)

---

#### 6. Start Service
```bash
# Start the service
sudo systemctl start okmonitor-device

# Watch logs (Ctrl+C to exit)
sudo journalctl -u okmonitor-device -f
```

**You should see:**
```
[device] Entering scheduled capture mode...
[device] Received new config: {...}
[device] Camera opened successfully
```

☐ Service started and running

---

#### 7. Verify Installation
```bash
sudo deployment/verify_deployment.sh
```

**Expected:** All checks pass or only warnings

☐ Verification passed

---

#### 8. Connect Tailscale (if not done in step 4)
```bash
# If you didn't use --tailscale-key during installation:
sudo deployment/install_tailscale.sh --auth-key tskey-auth-xxxxx

# Check status
tailscale status
```
☐ Tailscale connected

**Note:** Tailscale is already installed - this step only connects if you skipped it earlier

---

#### 9. Final Checks
```bash
# Check service status
sudo systemctl status okmonitor-device

# Check update timer
sudo systemctl list-timers okmonitor-update

# Reboot test
sudo reboot
```

**After reboot:**
```bash
# Wait 1 minute, then check
ssh mok@okmonitor.local
sudo systemctl status okmonitor-device
```
☐ Auto-start verified

---

## Route 2: Golden Image Cloning

**Time per device:** ~5 minutes (after golden image created)

This route clones a pre-configured SD card image to quickly deploy multiple devices.

---

### Part A: Create Golden Image (One-Time Setup)

**Do this ONCE to create the master image**

#### Before You Start
- ☐ One Raspberry Pi 5 set up as master device
- ☐ Master device tested and working perfectly
- ☐ Computer with SD card reader
- ☐ Imaging software installed (Win32DiskImager, dd, or Balena Etcher)

---

#### 1. Prepare Master Device
```bash
# SSH into master device
ssh mok@okmonitor.local

# Stop service
sudo systemctl stop okmonitor-device

# Prepare for cloning
sudo deployment/prepare_for_clone.sh

# Shutdown
sudo shutdown -h now
```
☐ Master device prepared

---

#### 2. Create SD Card Image

**On Windows:**
1. Download Win32 Disk Imager
2. Insert master SD card
3. Click "Read"
4. Save as: `okmonitor-golden-v1.0.img`

**On macOS:**
```bash
diskutil list
diskutil unmountDisk /dev/disk2
sudo dd if=/dev/rdisk2 of=~/okmonitor-golden-v1.0.img bs=4m status=progress
```

**On Linux:**
```bash
lsblk
sudo dd if=/dev/sdb of=~/okmonitor-golden-v1.0.img bs=4M status=progress
```

☐ Image created

---

#### 3. (Optional) Shrink Image
```bash
# Download PiShrink
wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh
chmod +x pishrink.sh

# Shrink image
sudo ./pishrink.sh okmonitor-golden-v1.0.img
```
☐ Image optimized

---

### Part B: Deploy to New Devices

**Do this for EACH device**

#### Before You Start
- ☐ Golden image file ready
- ☐ Blank SD card (32GB+)
- ☐ Unique device ID chosen for this device
- ☐ WiFi credentials (if needed)
- ☐ Tailscale auth key (if needed)

---

#### 1. Write Image to SD Card

**Using Balena Etcher (Easiest):**
1. Download: https://etcher.balena.io/
2. Select golden image file
3. Select SD card
4. Click "Flash"

**Using dd (Linux/macOS):**
```bash
sudo dd if=okmonitor-golden-v1.0.img of=/dev/sdX bs=4M status=progress
sync
```

**Using Win32DiskImager (Windows):**
1. Select golden image file
2. Select SD card drive
3. Click "Write"

☐ Image written to SD card

---

#### 2. Boot Device
1. Insert SD card into Raspberry Pi
2. Connect power
3. Wait ~60 seconds for boot
4. Connect via SSH

```bash
ssh mok@okmonitor.local
# Default password from golden image
```

☐ Device booted and accessible

---

#### 3. Customize Device ID

```bash
# Run customization script
sudo deployment/customize_clone.sh
```

**When prompted:**
- Enter unique DEVICE_ID: `okmonitor1` (or `floor-01-cam`, etc.)
- Confirm: `y`
- **Connect to Tailscale?** `y` (recommended)
  - Enter Tailscale auth key when prompted
  - Or press `n` to skip (can connect later)

**Script will:**
- Update device configuration
- Clear cached data
- Reset Tailscale identity
- Prompt to connect Tailscale
- Restart service

☐ Device customized with unique ID
☐ Tailscale connected (if accepted prompt)

---

#### 4. Configure WiFi (if needed)

**Method A: Comitup Web Interface** (Recommended - no SSH needed!)
```bash
# 1. Reboot device: sudo reboot
# 2. Connect phone/laptop to 'okmonitor-XXXX' WiFi (no password)
# 3. Open browser to: http://10.41.0.1
# 4. Select customer WiFi and enter password
# Device automatically connects and starts monitoring!
```
📖 **Full guide:** [COMITUP.md](COMITUP.md) or [ONSITE-SETUP.md](ONSITE-SETUP.md)

**Method B: addwifi.sh Script** (Backup method with SSH)
```bash
# Add WiFi network:
~/addwifi.sh "Network-Name" "wifi-password" 100

# Verify connection:
ping -c 3 8.8.8.8
```
📖 **Full guide:** [WIFI.md](WIFI.md)

☐ WiFi configured (if needed)

---

#### 5. Connect Tailscale (if skipped in step 3)

```bash
# If you skipped Tailscale during customization:
sudo deployment/install_tailscale.sh --auth-key tskey-auth-xxxxx

# Verify
tailscale status
```

☐ Tailscale connected (if skipped earlier)

**Note:** Tailscale is pre-installed in golden image - this step only connects if you skipped the prompt

---

#### 6. Verify Deployment

```bash
# Run verification
sudo deployment/verify_deployment.sh
```

**Expected:** All checks pass

**Check logs:**
```bash
sudo journalctl -u okmonitor-device -f
```

**You should see:**
```
[device] Entering scheduled capture mode...
[device] Received new config: {...}
[device] Camera opened successfully
```

☐ Verification passed

---

#### 7. Final Checks

```bash
# Test reboot
sudo reboot
```

**After reboot:**
```bash
# Wait 1 minute, reconnect
ssh mok@okmonitor.local
sudo systemctl status okmonitor-device
```

☐ Auto-start verified

---

### Batch Deployment Workflow

**For deploying 10+ devices efficiently:**

#### Step 1: Write All SD Cards
```
1. Write golden image to first SD card
2. Label SD card with device ID
3. Repeat for all devices
4. Stack labeled cards
```

#### Step 2: Boot and Customize
```
For each device:
  1. Insert SD card
  2. Boot device
  3. SSH in
  4. Run: sudo deployment/customize_clone.sh
  5. Enter device ID from label
  6. Configure WiFi (if needed)
  7. Move to next device
```

#### Step 3: Bulk Tailscale Setup
```bash
# After all devices customized, from management PC:
DEVICES=("okmonitor1" "okmonitor2" "okmonitor3")
AUTH_KEY="tskey-auth-xxxxx"

for device in "${DEVICES[@]}"; do
    ssh mok@okmonitor-$device.local \
        "sudo deployment/install_tailscale.sh --auth-key $AUTH_KEY"
done
```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| View logs | `sudo journalctl -u okmonitor-device -f` |
| Restart service | `sudo systemctl restart okmonitor-device` |
| Edit config | `sudo nano /opt/okmonitor/.env.device` |
| Check device ID | `grep DEVICE_ID /opt/okmonitor/.env.device` |
| Add WiFi | `~/addwifi.sh "SSID" "password"` |
| List cameras | `v4l2-ctl --list-devices` |
| Check API | `curl -I https://okmonitor-production.up.railway.app/health` |
| Manual update | `sudo /opt/okmonitor/deployment/update_device.sh` |
| Verify deployment | `sudo deployment/verify_deployment.sh` |
| Customize clone | `sudo deployment/customize_clone.sh` |
| Uninstall | `sudo deployment/uninstall.sh --keep-packages` |
| Reinstall (remote) | `sudo deployment/install_device.sh --device-id YOUR_ID --skip-tailscale` |

---

## Common Troubleshooting

### Service Won't Start
```bash
sudo journalctl -u okmonitor-device -n 50
sudo systemctl status okmonitor-device
```
**Common fixes:**
- Camera not connected → Check USB
- Wrong/placeholder DEVICE_ID → Edit `.env.device` or run customize script
- No internet → Configure WiFi or Ethernet

### Camera Not Found
```bash
v4l2-ctl --list-devices
ls -l /dev/video*
```
**Fix:** Update `CAMERA_SOURCE` in `/opt/okmonitor/.env.device`

### Network Issues
```bash
curl -I https://okmonitor-production.up.railway.app/health
ping -c 4 8.8.8.8
```
**Fix:** Add WiFi with `~/addwifi.sh` or connect Ethernet

### Tailscale Conflict (Route 2)
```bash
# If "node already registered" error:
sudo tailscale logout
sudo deployment/install_tailscale.sh --auth-key YOUR_KEY
```

### Multiple Devices Same ID (Route 2)
```bash
# On duplicate device:
sudo deployment/customize_clone.sh
# Enter NEW unique device ID
```

---

## Completion Checklist

Before leaving the site:

- ☐ Service running (`sudo systemctl status okmonitor-device`)
- ☐ Camera working (`v4l2-ctl --list-devices`)
- ☐ Cloud connected (`curl -I $API_URL/health`)
- ☐ WiFi configured (if applicable)
- ☐ Tailscale connected (if needed)
- ☐ Auto-start verified (reboot test passed)
- ☐ Device ID is unique and descriptive
- ☐ Device ID label applied to hardware
- ☐ Device ID recorded in tracking sheet
- ☐ Verification script passed
- ☐ Customer notified

---

## Device Naming Best Practices

**Good examples:**
- `floor-01-cam` - Clear location
- `warehouse-entrance` - Clear purpose
- `lab-02-bench-01` - Specific location

**Bad examples:**
- `cam1` - Too generic
- `test` - Not descriptive
- `device-ABC123` - Not readable

---

## Additional Resources

**Detailed Guides:**
- [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md) - Complete v1.0 deployment documentation
- [CLONING.md](CLONING.md) - Golden image creation and management
- [COMITUP.md](COMITUP.md) - WiFi setup via web interface
- [ONSITE-SETUP.md](ONSITE-SETUP.md) - Field deployment procedures
- [WIFI.md](WIFI.md) - Manual WiFi configuration

**Troubleshooting:**
- [DEPLOYMENT_V1.md#troubleshooting](DEPLOYMENT_V1.md#troubleshooting)
- [CLONING.md#troubleshooting](CLONING.md#troubleshooting)

**Issue?**
1. Run: `sudo deployment/verify_deployment.sh`
2. Check logs: `sudo journalctl -u okmonitor-device -f`
3. Review detailed guides above

---

## Deployment Record

**Deployment Date:** _______________
**Deployment Route:** ☐ Route 1 (Fresh) ☐ Route 2 (Clone)
**Device ID:** _______________
**Golden Image Version (Route 2):** _______________
**WiFi Network:** _______________
**Tailscale Hostname:** _______________
**Technician:** _______________
**Site Location:** _____________________________________
**Notes:** _____________________________________
_____________________________________
