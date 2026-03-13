# Level Sense Local for Home Assistant

A custom component to completely sever the Level Sense Pro from its proprietary cloud and achieve 100% local, two-way control inside Home Assistant.

By using local DNS spoofing and a reverse proxy, this integration intercepts the device's hardcoded outbound telemetry and seamlessly takes over as the command server, allowing you to configure thresholds, toggle sirens, and read sensors without ever touching the internet.

## ✨ Features

* **100% Cloud-Free:** Traffic never leaves your local network.
* **Real-Time Telemetry:** Monitors Temperature, Humidity, Leak Sensor (Input 1), Float Switch (Input 2), Battery Voltage, and internal device states.
* **Two-Way Configuration:** Change alarm thresholds, polling intervals, and siren/relay bitmasks directly from the Home Assistant UI.
* **Persistent Storage:** Saves your custom device configuration to a local `.storage` file so your settings survive Home Assistant reboots.
* **Corrected Physics & Math:** Automatically corrects the manufacturer's raw telemetry data (e.g., handling the internal 3.61°C / 6.5°F thermal offset) to reflect true ambient conditions.

## ⚠️ Architecture & Prerequisites

The Level Sense Pro is a "dumb client" that only initiates outbound HTTP GET requests to `cloud.level-sense.com` on Port `80`. It wakes up, posts data to `/_device/data`, and if flagged, pulls new settings from `/_device/config`.

Because Home Assistant runs on Port `8123` and the device refuses to append ports to its requests, you cannot point the device directly to Home Assistant. You must intercept the traffic.

**You will need:**
* **A Local DNS Server** (e.g., Pi-hole, AdGuard Home, or your router) to redirect `cloud.level-sense.com` to a local Reverse Proxy.
* **A Reverse Proxy** (e.g., Nginx, SWAG, HAProxy) listening on Port `80` to catch the intercepted traffic and forward it to Home Assistant.

## 🛠️ Setup Instructions

### 1. Network Interception (DNS & Proxy)

First, configure your local DNS server to assign `cloud.level-sense.com` to the IP address of your Reverse Proxy.

Next, configure your Reverse Proxy to catch that domain and forward the specific endpoints to Home Assistant. Here is an example configuration for Nginx:

```nginx
server {
    listen 80;
    server_name cloud.level-sense.com;

    # Forward telemetry data to Home Assistant
    location /_device/data {
        proxy_pass http://<HOME_ASSISTANT_IP>:8123/_device/data;
    }

    # Forward configuration requests to Home Assistant
    location /_device/config {
        proxy_pass http://<HOME_ASSISTANT_IP>:8123/_device/config;
    }
}
```

### 2. Install the Custom Component

1. Download or clone this repository.
2. Copy the `level_sense` folder into your Home Assistant `/config/custom_components/` directory.
3. Restart Home Assistant.

### 3. Home Assistant Configuration

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **Level Sense** and select it.
4. The integration will automatically create the required HTTP endpoints and generate the default `.storage` configuration file.

### 4. Force the Initial Sync

To get your device talking to Home Assistant immediately without waiting for its next deep-sleep cycle to end:

1. Walk over to your physical Level Sense unit.
2. Press the **Check-in / Calibrate** button on the front panel.
3. The device will wake up, hit your proxy, push its data to Home Assistant, and immediately download the local configuration payload.

*Your sensors will populate in Home Assistant instantly!*

## 🧠 Technical Notes

* **Strict C-Parsers:** The ESP32 firmware on the Level Sense uses a highly rigid JSON parser. The `/_device/config` endpoint in this integration is intentionally designed to return tightly packed JSON (no spaces) with specific sequential key ordering and a `text/html` header. Altering the JSON structure in `__init__.py` may cause the device to silently reject the payload.


