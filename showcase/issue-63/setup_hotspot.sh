#!/usr/bin/env bash
# Configure Zero 2 W as a WiFi access point (OBD-Dash network)
# Run once on fresh Raspberry Pi OS Lite

set -e

echo "Installing hostapd + dnsmasq…"
sudo apt-get update -qq
sudo apt-get install -y hostapd dnsmasq

sudo systemctl stop hostapd dnsmasq

# Static IP for wlan0
sudo tee /etc/network/interfaces.d/wlan0-static <<'EOF'
auto wlan0
iface wlan0 inet static
    address 192.168.42.1
    netmask 255.255.255.0
EOF

# DHCP for clients
sudo tee /etc/dnsmasq.conf <<'EOF'
interface=wlan0
dhcp-range=192.168.42.10,192.168.42.50,24h
EOF

# AP config
sudo tee /etc/hostapd/hostapd.conf <<'EOF'
interface=wlan0
driver=nl80211
ssid=OBD-Dash
hw_mode=g
channel=6
auth_algs=1
wpa=2
wpa_passphrase=obdzerow
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

sudo sed -i 's|#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

sudo systemctl unmask hostapd
sudo systemctl enable hostapd dnsmasq
sudo systemctl start  hostapd dnsmasq

echo "Done — connect to SSID: OBD-Dash | pass: obdzerow"
echo "Dashboard: http://192.168.42.1:5000"
