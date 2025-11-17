# Tailscale Remote Access for OK Monitor Fleet

This guide covers Tailscale-specific features for secure remote SSH and VNC access to your OK Monitor devices.

> **For installation instructions:** See [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md) or [DEPLOYMENT_V2.md](DEPLOYMENT_V2.md)

## What is Tailscale?

Tailscale creates a secure, private network (called a "tailnet") that connects your devices no matter where they are. Benefits for OK Monitor fleet:

- ✅ **Secure** - Uses WireGuard encryption
- ✅ **Zero-config** - No port forwarding or firewall rules
- ✅ **Easy access** - SSH/VNC from anywhere (home, office, mobile)
- ✅ **Fleet management** - See all devices in one dashboard
- ✅ **Unique names** - Each device gets a memorable hostname
- ✅ **No public exposure** - Devices not accessible from internet

---

## Quick Start

### One-Time Setup (Tailscale Account)

1. Create free Tailscale account: https://tailscale.com/
2. Generate an auth key:
   - Go to https://login.tailscale.com/admin/settings/keys
   - Click "Generate auth key"
   - Enable "Reusable" for fleet deployment
   - Enable "Ephemeral" if you want device to disappear when offline
   - Copy the key (starts with `tskey-auth-...`)

### Install Tailscale on Devices

**During OK Monitor installation, use the `--tailscale-key` flag:**

```bash
sudo deployment/install_device.sh --tailscale-key tskey-auth-xxxxx
```

**For detailed installation options and standalone Tailscale setup, see:**
- [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md#quick-installation) - Installation flags and options
- [DEPLOYMENT_V2.md](DEPLOYMENT_V2.md#installation) - v2.0 specific setup

### Install Tailscale on Your Computer

**Mac/Windows:**
- Download from: https://tailscale.com/download
- Install and sign in with same account

**Linux:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

---

## Device Naming Convention

Devices are automatically named: `okmonitor-{DEVICE_ID}`

Examples:
- `DEVICE_ID=okmonitor1` → Hostname: `okmonitor-okmonitor1`
- `DEVICE_ID=floor-01-cam` → Hostname: `okmonitor-floor-01-cam`
- `DEVICE_ID=warehouse-entrance` → Hostname: `okmonitor-warehouse-entrance`

This makes it easy to identify and access devices in your fleet.

---

## Accessing Devices

### SSH Access

From any device on your tailnet:

```bash
# By hostname
ssh mok@okmonitor-okmonitor1

# By Tailscale IP
ssh mok@100.101.102.103

# List all devices
tailscale status
```

### VNC Access

Raspberry Pi OS includes RealVNC Server (enabled by default).

**Using RealVNC Viewer:**
1. Download RealVNC Viewer: https://www.realvnc.com/en/connect/download/viewer/
2. Connect to: `okmonitor-okmonitor1` or Tailscale IP
3. Enter Raspberry Pi credentials

**Using built-in VNC clients:**
```bash
# macOS (Screen Sharing)
open vnc://okmonitor-okmonitor1

# Linux
vncviewer okmonitor-okmonitor1:5900
```

---

## Fleet Deployment Workflow

1. **Generate reusable auth key** at https://login.tailscale.com/admin/settings/keys (enable "Reusable", set 90-day expiry)

2. **Install on each device:**
   ```bash
   sudo deployment/install_device.sh --tailscale-key tskey-auth-xxxxx
   ```

3. **Manage fleet:**
   - Web: https://login.tailscale.com/admin/machines
   - CLI: `tailscale status`

**Batch deployment script:**
```bash
#!/bin/bash
AUTH_KEY="tskey-auth-xxxxx"
for device in okmonitor1 okmonitor2 okmonitor3; do
    ssh mok@${device}.local "cd /opt/okmonitor && sudo deployment/install_device.sh --tailscale-key $AUTH_KEY"
done
```

---

## Common Use Cases

### Remote Troubleshooting

```bash
# Check if device is online
tailscale status | grep okmonitor-okmonitor1

# SSH to device
ssh mok@okmonitor-okmonitor1

# Check device logs
ssh mok@okmonitor-okmonitor1 'sudo journalctl -u okmonitor-device -n 50'

# View live logs
ssh mok@okmonitor-okmonitor1 -t 'sudo journalctl -u okmonitor-device -f'
```

### Remote Configuration Updates

```bash
# Update .env.device
ssh mok@okmonitor-okmonitor1 'sudo nano /opt/okmonitor/.env.device'

# Restart service
ssh mok@okmonitor-okmonitor1 'sudo systemctl restart okmonitor-device'
```

### Batch Operations

```bash
# Check status of all devices
for host in okmonitor-okmonitor1 okmonitor-okmonitor2; do
    echo "=== $host ==="
    ssh mok@$host 'systemctl status okmonitor-device --no-pager | grep Active'
done

# Update all devices
for host in okmonitor-okmonitor1 okmonitor-okmonitor2; do
    echo "=== Updating $host ==="
    ssh mok@$host 'cd /opt/okmonitor && git pull && sudo systemctl restart okmonitor-device'
done
```

---

## Security Best Practices

1. **Enable MFA**: https://login.tailscale.com/admin/settings/mfa - Protects your entire fleet
2. **Use ACLs**: Control who can access which devices at https://login.tailscale.com/admin/acls
3. **Set Key Expiration**: Use 30-90 day expiration for auth keys
4. **Review Devices**: Regularly check https://login.tailscale.com/admin/machines and remove unused devices
5. **Ephemeral Keys**: Enable "Ephemeral" for temporary access deployments

---

## Troubleshooting

### Device Not Showing Up in Tailnet

```bash
# Check Tailscale status
sudo tailscale status

# Check if service is running
sudo systemctl status tailscaled

# Restart Tailscale
sudo tailscale down
sudo tailscale up
```

### Can't Connect to Device via Tailscale

```bash
# On the Raspberry Pi, check connectivity
sudo tailscale ping okmonitor-okmonitor2

# Verify SSH is running
sudo systemctl status ssh
```

### Hostname Not Resolving

Use Tailscale IP instead:
```bash
# Get device IP
tailscale ip -4

# Connect via IP
ssh mok@100.101.102.103
```

### Connection Drops Frequently

```bash
# Enable longer timeout
sudo tailscale up --timeout=0

# Check network stability
ping -c 10 8.8.8.8
```

### VNC Not Working

```bash
# Check if VNC is enabled (on Raspberry Pi)
sudo raspi-config
# → Interface Options → VNC → Enable

# Or via command line
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl start vncserver-x11-serviced.service

# Check VNC status
sudo systemctl status vncserver-x11-serviced.service
```

> **For general device troubleshooting:** See [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md#troubleshooting) or [DEPLOYMENT_V2.md](DEPLOYMENT_V2.md#troubleshooting)

---

## Advanced Features

### Subnet Routing
Access other devices on the Pi's local network through Tailscale:
```bash
sudo tailscale up --advertise-routes=192.168.1.0/24
# Then approve at https://login.tailscale.com/admin/machines
```

### Exit Node
Use Raspberry Pi as VPN exit node:
```bash
sudo tailscale up --advertise-exit-node
# Then on other devices: tailscale up --exit-node=okmonitor-okmonitor1
```

### SSH Key Authentication
```bash
ssh-keygen -t ed25519 -C "okmonitor-fleet"
ssh-copy-id mok@okmonitor-okmonitor1
```

---

## Monitoring & Maintenance

**Check status:**
```bash
sudo tailscale status      # Connection status
sudo tailscale ip -4       # Get current IP
sudo tailscale netcheck    # Network info
```

**Update Tailscale:**
```bash
sudo apt update && sudo apt upgrade tailscale
```

**Remove device:**
```bash
sudo tailscale logout  # Or delete from https://login.tailscale.com/admin/machines
```

---

## Cost & Limits

**Free Tier (Personal):**
- Up to 100 devices
- Up to 3 users
- Perfect for small OK Monitor fleets

**Paid Plans:**
- More devices
- Team collaboration features
- Advanced ACLs
- Priority support

See: https://tailscale.com/pricing

---

## Useful Resources

- Tailscale Docs: https://tailscale.com/kb/
- Admin Console: https://login.tailscale.com/admin/
- Status Page: https://status.tailscale.com/
- Community: https://forum.tailscale.com/

---

## Example: Complete Fleet Setup

```bash
# 1. Generate auth key at https://login.tailscale.com/admin/settings/keys
# 2. Install on devices
sudo deployment/install_device.sh --tailscale-key tskey-auth-xxxxx

# 3. Access from your laptop (after installing Tailscale)
tailscale status  # View all devices
ssh mok@okmonitor-okmonitor1  # Connect to any device
```

---

## Support

For issues with:
- **Tailscale installation**: Check https://tailscale.com/kb/
- **OK Monitor device**: See [DEPLOYMENT_V1.md](DEPLOYMENT_V1.md) or [DEPLOYMENT_V2.md](DEPLOYMENT_V2.md)
- **General troubleshooting**: Review deployment guides for device-specific issues
