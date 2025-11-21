# Network Setup Guide - OK Monitor Devices

Comprehensive WiFi configuration guide for Raspberry Pi devices running OK Monitor.

---

## Overview

This guide covers three methods for configuring WiFi on OK Monitor devices:

1. **Comitup Web Interface** - Web-based configuration via device hotspot
2. **addwifi.sh Script** - Command-line network management via SSH
3. **Manual wpa_supplicant** - Direct configuration for advanced users

---

## Method Comparison

| Feature | Comitup | addwifi.sh | Manual |
|---------|---------|------------|--------|
| **Access Required** | WiFi + Browser | SSH | SSH + Root |
| **Best For** | Field deployment | Remote management | Advanced troubleshooting |
| **Ease of Use** | Very Easy | Medium | Difficult |
| **Physical Access** | None needed | None needed | None needed |
| **Network Knowledge** | Minimal | Basic | Advanced |
| **Priority Management** | Auto | Yes (0-999) | Manual |
| **Multiple Networks** | Yes | Yes | Yes |
| **Hidden Networks** | CLI required | Supported | Supported |
| **Setup Time** | 3 minutes | 1 minute | 5+ minutes |

### When to Use Each Method

**Use Comitup when:**
- Deploying at customer sites without SSH access
- Technicians are non-technical
- No monitor/keyboard available
- Need quick, foolproof setup

**Use addwifi.sh when:**
- Managing devices remotely via Tailscale/SSH
- Bulk fleet configuration
- Need priority-based network failover
- Configuring hidden networks

**Use manual configuration when:**
- Troubleshooting network issues
- Enterprise WiFi (WPA2-Enterprise)
- Custom network configurations
- Learning how WiFi works on Linux

---

## Method 1: Comitup Web Interface

### What is Comitup?

Comitup automatically creates a WiFi hotspot when your Raspberry Pi has no network connection, allowing you to configure WiFi through a simple web interface from your phone or laptop.

**Key Features:**
- Zero-touch deployment (no keyboard/monitor needed)
- Phone-friendly web interface
- Open access point (no password required for setup)
- Automatic fallback to hotspot if WiFi fails
- Remembers multiple networks
- Auto-reconnect to known networks

---

### Quick Start - Field Deployment

**Time: 3 minutes**

#### Step 1: Power On Device
1. Connect USB camera and power supply
2. Wait 60 seconds for boot
3. Device creates hotspot: `okmonitor-XXXX`

#### Step 2: Connect to Hotspot
1. Open WiFi settings on phone/laptop
2. Connect to: `okmonitor-XXXX` (e.g., `okmonitor-1a2b`)
3. Password: None (open network)

#### Step 3: Open Configuration Page
1. Open web browser
2. Navigate to: `http://10.41.0.1`
3. Comitup web interface appears

#### Step 4: Configure Customer WiFi
1. Click on customer's WiFi network
2. Enter WiFi password
3. Click "Connect"
4. Wait 30-60 seconds

#### Step 5: Verify Connection
- Check OK Monitor dashboard
- Device should appear online
- Captures should start uploading

**Done!** Device will remember this network and auto-connect.

---

### Comitup Installation

#### Automatic Installation (Recommended)

```bash
# Clone repository
cd ~
git clone https://github.com/atxapple/okmonitor.git
cd okmonitor

# Run Comitup installer
sudo chmod +x deployment/install_comitup.sh
sudo deployment/install_comitup.sh

# Reboot to activate
sudo reboot
```

#### Manual Installation

```bash
# Download repository package
cd /tmp
wget https://davesteele.github.io/comitup/deb/davesteele-comitup-apt-source_1.3_all.deb

# Install repository
sudo dpkg -i davesteele-comitup-apt-source*.deb

# Update and install Comitup
sudo apt-get update
sudo apt-get install comitup

# Configure (see Configuration section)
sudo nano /etc/comitup.conf
```

---

### Comitup Configuration

Edit `/etc/comitup.conf`:

```ini
# Access Point name when no WiFi is configured
ap_name: okmonitor

# Access Point password (empty = open/no password)
ap_password:

# Callback script for state changes
external_callback: /usr/local/bin/comitup-callback.sh

# Enable verbose logging
verbose: false
```

#### Custom Device Name

```bash
sudo nano /etc/comitup.conf
```

Change:
```ini
ap_name: okmonitor-floor1
```

Restart:
```bash
sudo systemctl restart comitup
```

#### Enable Password Protection (Optional)

```bash
sudo nano /etc/comitup.conf
```

Add password (minimum 8 characters):
```ini
ap_password: your_secure_password
```

Restart:
```bash
sudo systemctl restart comitup
```

---

### Comitup Command Line Interface

#### Check Status

```bash
# Service status
systemctl status comitup

# Current state
comitup-cli

# View logs
journalctl -u comitup -f
```

#### List Saved Networks

```bash
# Using NetworkManager
nmcli connection show

# Show only WiFi connections
nmcli connection show | grep wifi
```

#### Delete a Network

```bash
# List connections
nmcli connection show

# Delete specific network
sudo nmcli connection delete "NetworkName"
```

#### Force Hotspot Mode

```bash
# Delete all WiFi connections
sudo nmcli connection show | grep wifi | awk '{print $1}' | \
    xargs -I {} sudo nmcli connection delete "{}"

# Reboot
sudo reboot
```

#### Manual Network Configuration

```bash
# Add network manually
sudo nmcli device wifi connect "SSID" password "password"

# Verify connection
nmcli device status
```

---

### Integration with OK Monitor

#### Automatic Service Restart

The callback script at `/usr/local/bin/comitup-callback.sh` automatically restarts OK Monitor when WiFi connects:

```bash
#!/bin/bash
STATE=$1

case "$STATE" in
    CONNECTED)
        systemctl restart okmonitor-device
        logger "OK Monitor: WiFi connected"
        ;;
    FAILED)
        logger "OK Monitor: WiFi connection failed"
        ;;
esac
```

**States:**
- `HOTSPOT` - No WiFi configured, running as AP
- `CONNECTING` - Attempting to connect to WiFi
- `CONNECTED` - Successfully connected to WiFi
- `FAILED` - Connection attempt failed

#### Deployment Workflow

For fleet deployments:
1. Create golden image with Comitup pre-installed
2. Clone image to SD cards
3. Boot devices at customer sites
4. Use Comitup to configure local WiFi
5. OK Monitor automatically starts after WiFi connects

---

## Method 2: addwifi.sh Script

### Quick Start

The `addwifi.sh` script is automatically installed to your home directory during device setup.

#### Basic Usage

```bash
# Add a WiFi network
~/addwifi.sh "Network-Name" "password123"

# List all saved networks
~/addwifi.sh --list

# Show help
~/addwifi.sh --help
```

---

### Common Scenarios

#### Scenario 1: New Installation Site

Connect device to customer WiFi:

```bash
# Connect to customer WiFi
~/addwifi.sh "CustomerWiFi" "their-password"

# Verify connection
ip addr show wlan0
ping -c 3 8.8.8.8
```

#### Scenario 2: Multiple Network Locations

Device moves between office, warehouse, and backup:

```bash
# Office network (highest priority)
~/addwifi.sh "Office-WiFi" "office-pass" 200

# Warehouse network (medium priority)
~/addwifi.sh "Warehouse-WiFi" "warehouse-pass" 150

# Backup hotspot (lowest priority)
~/addwifi.sh "Mobile-Hotspot" "hotspot-pass" 50

# Check all configured networks
~/addwifi.sh --list
```

Device automatically connects to the highest-priority available network.

#### Scenario 3: Hidden Network

```bash
# Add hidden network
~/addwifi.sh "Hidden-Secure-Net" "secret-password" 100 --hidden
```

#### Scenario 4: Temporary Access Point

```bash
# Connect to temporary phone hotspot
~/addwifi.sh "iPhone-Hotspot" "temp-pass" 10
```

---

### Priority Management

Priority values range from 0-999. Higher numbers connect first when multiple networks are in range.

#### Recommended Priority Scheme

| Location Type | Priority | Use Case |
|--------------|----------|----------|
| Primary Site | 200 | Main production location |
| Secondary Site | 150 | Backup or alternate location |
| Office/Admin | 100 | Administrative access |
| Mobile Hotspot | 50 | Emergency connectivity |
| Guest/Temp | 10 | Temporary access |

#### Example: Multi-Site Deployment

```bash
# Factory floor (primary)
~/addwifi.sh "Factory-Production" "prod-pass" 200

# Office area (secondary)
~/addwifi.sh "Factory-Office" "office-pass" 150

# Manager's mobile hotspot (emergency)
~/addwifi.sh "Manager-Phone" "hotspot-pass" 50
```

When the device is on the factory floor, it connects to "Factory-Production". If that network goes down, it automatically fails over to "Factory-Office", then to the mobile hotspot if needed.

---

### Network Management

#### List All Saved Networks

```bash
~/addwifi.sh --list
```

Output example:
```
===== Saved WiFi Profiles =====

Office-WiFi                    Priority: 200   Auto-connect: yes
Warehouse-WiFi                 Priority: 150   Auto-connect: yes
Mobile-Hotspot                 Priority: 50    Auto-connect: yes

Active connection:
  Office-WiFi (on wlan0)
```

#### Update Existing Network

```bash
# Change password
~/addwifi.sh "Office-WiFi" "new-password-2024" 200

# Change priority
~/addwifi.sh "Office-WiFi" "same-password" 250
```

#### Remove a Network

```bash
# List connections
nmcli connection show

# Delete a connection
sudo nmcli connection delete "Network-Name"
```

#### Check Current Connection

```bash
# Show active WiFi connection
nmcli connection show --active | grep wifi

# Show signal strength and details
nmcli device wifi list
```

---

### Advanced Usage

#### Static IP Configuration

```bash
# First, add the network normally
~/addwifi.sh "Static-Network" "password" 200

# Then configure static IP
sudo nmcli connection modify "Static-Network" \
    ipv4.method manual \
    ipv4.addresses 192.168.1.100/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns "8.8.8.8 8.8.4.4"

# Bring connection up
sudo nmcli connection up "Static-Network"
```

#### Enterprise WiFi (WPA2-Enterprise)

```bash
# Create connection
sudo nmcli connection add type wifi ifname wlan0 con-name "Enterprise-WiFi" ssid "Enterprise-WiFi"

# Configure WPA2-Enterprise
sudo nmcli connection modify "Enterprise-WiFi" \
    wifi-sec.key-mgmt wpa-eap \
    802-1x.eap peap \
    802-1x.phase2-auth mschapv2 \
    802-1x.identity "username" \
    802-1x.password "password"

# Activate
sudo nmcli connection up "Enterprise-WiFi"
```

#### Custom MAC Address

```bash
~/addwifi.sh "Network-Name" "password"

# Then set custom MAC
sudo nmcli connection modify "Network-Name" \
    802-11-wireless.cloned-mac-address "AA:BB:CC:DD:EE:FF"

sudo nmcli connection up "Network-Name"
```

#### Remote WiFi Configuration via Tailscale

```bash
# From your laptop (connected to Tailscale)
ssh mok@okmonitor-okmonitor1

# On the device
~/addwifi.sh "New-Site-WiFi" "new-password" 200
```

#### Bulk Fleet WiFi Configuration

```bash
#!/bin/bash
# deploy_wifi_to_fleet.sh

NETWORK="Factory-WiFi"
PASSWORD="factory-pass-2024"
DEVICES=("okmonitor-okmonitor1" "okmonitor-okmonitor2" "okmonitor-okmonitor3")

for device in "${DEVICES[@]}"; do
    echo "Configuring WiFi on $device..."
    ssh mok@$device "~/addwifi.sh '$NETWORK' '$PASSWORD' 200"
done
```

Run from your management machine:
```bash
chmod +x deploy_wifi_to_fleet.sh
./deploy_wifi_to_fleet.sh
```

---

## Method 3: Manual wpa_supplicant Configuration

For advanced users who need direct control over network configuration.

### Basic Configuration

Edit network configuration:

```bash
# Backup existing configuration
sudo cp /etc/NetworkManager/system-connections/MyNetwork /tmp/backup

# Edit connection file
sudo nano /etc/NetworkManager/system-connections/MyNetwork
```

### Example Configuration

```ini
[connection]
id=MyNetwork
type=wifi
autoconnect=true
autoconnect-priority=200

[wifi]
ssid=MyNetwork
mode=infrastructure

[wifi-security]
key-mgmt=wpa-psk
psk=your-password-here

[ipv4]
method=auto
```

### Reload NetworkManager

```bash
sudo systemctl reload NetworkManager
sudo nmcli connection up MyNetwork
```

---

## Troubleshooting

### Comitup Issues

#### Hotspot Not Appearing

Check Comitup service:
```bash
sudo systemctl status comitup
```

If not running:
```bash
sudo systemctl start comitup
```

Check WiFi interface:
```bash
nmcli device status
```

Restart Comitup:
```bash
sudo systemctl restart comitup
```

#### Can't Access Web Interface

Verify IP address and try these URLs:
- http://10.41.0.1
- http://10.41.0.1:80
- http://comitup.local

Clear browser cache or try incognito/private browsing mode.

Check firewall:
```bash
sudo ufw status
```

#### WiFi Connection Fails via Comitup

Check password (case-sensitive, special characters).

View connection logs:
```bash
sudo journalctl -u comitup -n 50
```

Try manual connection:
```bash
sudo nmcli device wifi connect "SSID" password "password"
```

#### Device Stuck in Hotspot Mode

Check saved connections:
```bash
nmcli connection show
```

Try to activate manually:
```bash
sudo nmcli connection up "NetworkName"

# Check why it failed
sudo journalctl -u NetworkManager -n 50
```

Signal too weak:
- Move device closer to router
- Check antenna connections (if using USB WiFi)
- Consider WiFi extender

---

### WiFi Script Issues

#### WiFi Not Connecting

Check if WiFi hardware is enabled:
```bash
nmcli radio wifi on
nmcli device status
```

Check network is in range:
```bash
sudo nmcli device wifi list
```

Test connection manually:
```bash
sudo nmcli connection up "Network-Name"
```

Check logs:
```bash
sudo journalctl -u NetworkManager -n 50
```

#### Wrong Password

Re-run with the correct password:
```bash
~/addwifi.sh "Network-Name" "correct-password"
```

#### Auto-Connect Not Working After Reboot

Verify auto-connect is enabled:
```bash
nmcli connection show "Network-Name" | grep autoconnect
```

If disabled, enable it:
```bash
sudo nmcli connection modify "Network-Name" connection.autoconnect yes
```

Check boot order:
```bash
systemctl list-dependencies okmonitor-device.service
```

#### Multiple Devices Connecting to Wrong Network

Differentiate priorities:
```bash
~/addwifi.sh "Preferred-Network" "pass1" 200
~/addwifi.sh "Backup-Network" "pass2" 100
```

#### Hidden Network Not Found

Verify SSID is typed exactly (case-sensitive):
```bash
# "MyNetwork" != "mynetwork" != "MYNETWORK"
```

Check network is actually hidden:
```bash
# If you see it in this list, don't use --hidden flag
sudo nmcli device wifi list
```

---

### Network Connectivity Issues

#### Network Keeps Disconnecting

Check signal strength:
```bash
nmcli device wifi list
# Signal column shows strength (0-100)
# Aim for >50 for stable connection
```

If signal is weak:
- Reposition device closer to access point
- Check for physical obstructions (metal cabinets, thick walls)
- Add WiFi USB adapter with external antenna
- Add network extender/repeater

Check for interference:
```bash
sudo iwlist wlan0 scan | grep -E "ESSID|Channel|Quality"
```

#### Can't Find WiFi Interface

Check WiFi hardware:
```bash
# List all network devices
nmcli device status

# Check for WiFi driver
lsusb  # For USB WiFi adapters
dmesg | grep -i wifi
```

If no interface found:
- Check physical connection (USB WiFi adapter)
- Verify driver is installed
- Check if WiFi is disabled in BIOS/firmware

#### Hotspot Keeps Disconnecting (Comitup)

Check for WiFi interference:
```bash
sudo iwlist wlan0 scan | grep -E "Channel|ESSID|Quality"
```

Change hotspot channel:
```bash
sudo nano /etc/comitup.conf
# Add: ap_channel: 6
sudo systemctl restart comitup
```

Check power supply:
- Ensure adequate power (5V 3A for Pi 5)
- Poor power can cause WiFi instability

---

## Security Best Practices

### Password Management

1. **Use strong passwords:**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Avoid common words or patterns

2. **Don't store passwords in plain text:**
   - Never commit passwords to git
   - Use password managers for organization

3. **Rotate passwords regularly:**
   - Update network passwords every 90 days
   - Use update command to change credentials:
     ```bash
     ~/addwifi.sh "Network-Name" "new-password-2024" 200
     ```

### Network Security

1. **Prefer WPA2/WPA3:**
   - Avoid WEP or open networks
   - Both methods use WPA2-PSK by default

2. **Use hidden networks when possible:**
   - Adds a layer of obscurity
   - Remember to use `--hidden` flag with addwifi.sh

3. **Separate device networks:**
   - Consider IoT-specific network segment
   - Isolate monitoring devices from corporate network

### Comitup Access Point Security

**Default configuration uses open (no password) access point.**

Risks:
- Anyone can connect to the hotspot
- Anyone can configure WiFi settings
- Limited attack window (only active when no WiFi configured)

Mitigations:
1. **Physical security** - Keep devices in secure areas during setup
2. **Limited exposure** - Hotspot only active briefly during deployment
3. **Monitor access** - Check logs for unexpected connections
4. **Add password** - For high-security environments:

```bash
sudo nano /etc/comitup.conf
```

Set:
```ini
ap_password: SecurePass123!
```

### Physical Security

1. **Protect device access:**
   - Keep Raspberry Pi in locked enclosure
   - Limit physical access to trusted personnel

2. **Secure credentials:**
   - Don't leave passwords written near devices
   - Train technicians on secure password handling

### Network Isolation

Comitup hotspot is isolated from your main network:
- Hotspot is its own network (10.41.0.0/24)
- No access to your configured WiFi
- Only provides web interface for configuration

---

## Monitoring & Maintenance

### Check Connection Status

```bash
# Check if connected
nmcli -t -f DEVICE,STATE device | grep wlan0

# Get signal strength
nmcli -t -f IN-USE,SIGNAL,SSID device wifi | grep "^*"

# Get IP address
ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
```

### Log WiFi Events

```bash
# Watch for connection changes
sudo journalctl -u NetworkManager -f

# Filter for specific network
sudo journalctl -u NetworkManager | grep "Network-Name"
```

### Alert on Disconnection

Create a simple monitor script:

```bash
#!/bin/bash
# wifi_monitor.sh

while true; do
    if ! nmcli -t -f DEVICE,STATE device | grep -q "wlan0:connected"; then
        echo "WiFi disconnected at $(date)"
        # Send alert (customize as needed)
        curl -X POST "YOUR_ALERT_ENDPOINT" -d "device=$HOSTNAME&status=disconnected"
    fi
    sleep 60
done
```

### Check Comitup Health

```bash
#!/bin/bash
# comitup-health.sh

STATUS=$(comitup-cli 2>/dev/null)

if [[ $STATUS == *"CONNECTED"* ]]; then
    echo "OK: Device connected to WiFi"
    exit 0
elif [[ $STATUS == *"HOTSPOT"* ]]; then
    echo "WARN: Device in hotspot mode (no WiFi configured)"
    exit 1
else
    echo "ERROR: Comitup not responding"
    exit 2
fi
```

### Automatic Fallback

Comitup automatically falls back to hotspot mode if:
- Configured WiFi network not in range
- WiFi password changed
- Network authentication fails
- Connection drops repeatedly

This provides automatic recovery without manual intervention.

---

## Quick Reference Commands

### Comitup Commands

```bash
systemctl status comitup              # Service status
comitup-cli                           # Current state
journalctl -u comitup -f              # View logs
sudo systemctl restart comitup        # Restart service
```

### WiFi Script Commands

```bash
~/addwifi.sh "SSID" "password" [priority] [--hidden]
~/addwifi.sh --list
~/addwifi.sh --help
```

### NetworkManager Commands

```bash
nmcli device status                   # Show all network devices
nmcli device wifi list                # Scan for WiFi networks
nmcli connection show                 # List saved connections
nmcli connection show --active        # Show active connections
nmcli connection up "Name"            # Connect to network
nmcli connection down "Name"          # Disconnect from network
nmcli connection delete "Name"        # Remove saved network
```

### Diagnostics

```bash
ip addr show wlan0                    # Show WiFi interface details
ping -c 3 8.8.8.8                     # Test internet connectivity
iwconfig wlan0                        # Show wireless configuration
sudo journalctl -u NetworkManager     # View NetworkManager logs
```

---

## Common Questions

**Q: Can I use Ethernet and WiFi at the same time?**

A: Yes! NetworkManager handles both. Ethernet typically takes precedence automatically.

**Q: Does this work with WiFi 6 (802.11ax)?**

A: Yes, if your Raspberry Pi hardware and driver support it. The Raspberry Pi 5 built-in WiFi supports WiFi 5 (802.11ac).

**Q: Can I configure multiple WiFi networks?**

A: Yes! Both Comitup and addwifi.sh support multiple networks. The device auto-connects to whichever is in range (based on priority with addwifi.sh).

**Q: What if I need to configure WiFi before SSH access?**

A: Use Comitup (no SSH needed) or connect via Ethernet first.

**Q: Can I access the Comitup web interface after WiFi is configured?**

A: No, the hotspot and web interface are only active when the device isn't connected to WiFi. Use SSH or Tailscale for remote management.

**Q: How do I change the hotspot name?**

A: Edit `/etc/comitup.conf`, change `ap_name`, and restart comitup service.

**Q: Can both Comitup and addwifi.sh be installed on the same device?**

A: Yes! Use Comitup for on-site WiFi setup, and addwifi.sh for remote WiFi changes via SSH/Tailscale.

---

## Tips & Tricks

### Quick Connection Test

```bash
# Test internet connectivity
ping -c 3 8.8.8.8

# Test DNS resolution
ping -c 3 google.com

# Test cloud API
curl -I https://okmonitor-production.up.railway.app/health
```

### Forget All WiFi Networks

```bash
# List all WiFi connections
nmcli -t -f NAME,TYPE connection show | grep 802-11-wireless | cut -d: -f1

# Delete each one
nmcli -t -f NAME,TYPE connection show | grep 802-11-wireless | cut -d: -f1 | \
    while read name; do sudo nmcli connection delete "$name"; done
```

### Export WiFi Configuration

```bash
# Backup all NetworkManager configs
sudo tar -czf wifi-backup.tar.gz /etc/NetworkManager/system-connections/

# Restore on another device
sudo tar -xzf wifi-backup.tar.gz -C /
sudo systemctl restart NetworkManager
```

### Auto-Connect to Best Network

NetworkManager automatically handles this based on:
1. Priority (higher = preferred)
2. Signal strength (if priorities equal)
3. Last connected time (if all else equal)

Configure priorities correctly and the system handles the rest!

---

## Support

For issues with:
- **Comitup**: https://davesteele.github.io/comitup/
- **NetworkManager**: https://networkmanager.dev/
- **Visant device deployment**: See main DEPLOYMENT_V1.md or DEPLOYMENT_V2.md
- **Raspberry Pi WiFi**: https://www.raspberrypi.com/documentation/

---

## File Locations

### Comitup
- Configuration: `/etc/comitup.conf`
- Callback script: `/usr/local/bin/comitup-callback.sh`
- Service: `/lib/systemd/system/comitup.service`
- Logs: `journalctl -u comitup`

### addwifi.sh
- Script source: `deployment/addwifi.sh`
- Installed to: `/home/{user}/addwifi.sh`
- Repository: https://github.com/atxapple/okmonitor

### NetworkManager
- Connection profiles: `/etc/NetworkManager/system-connections/`
- Configuration: `/etc/NetworkManager/NetworkManager.conf`
- Logs: `journalctl -u NetworkManager`

---

Happy connecting!
