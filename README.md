# LAB 11: Autonomous Smart Vehicle with AI & Emergency Override
**AGU EE 304 — Embedded Systems**
Instructor: Dr. Khaled Hejja

---

## Overview

This project implements the Lab 11 smart vehicle state machine in Python. Because a physical Raspberry Pi 5 was unavailable, the hardware layer has been substituted with a software simulation while preserving the full software architecture described in the lab: threading model, Flask web server, state machine logic, and smartphone control interface.

---

## Hardware Substitutions

| Lab Component | Substitution | Notes |
|---|---|---|
| Raspberry Pi 5 | Desktop Linux machine (Arch) | Runs the same Python code |
| `RPi.GPIO` library | `SimulatedGPIO` class | Identical API; LED state printed to terminal in color |
| HC-SR04 Ultrasonic Sensor | `/sensor?dist=X` HTTP endpoint | Injects a distance reading to trigger obstacle logic |
| Green LED (GPIO 14) | Terminal output `[GREEN LED] ON/OFF` | Color-coded green in terminal |
| Red LED (GPIO 15) | Terminal output `[RED LED] ON/OFF` | Color-coded red in terminal |

Everything else — the threading architecture, Flask routes, state machine, and smartphone control — is unchanged from the lab specification.

---

## Project Structure

```
Embedded_Lab_11/
├── smart_car.py      # Main application (state machine + Flask server)
├── requirements.txt  # Python dependencies
├── LAB-11.pdf        # Original lab document
└── README.md
```

---

## Setup

**1. Create and activate the virtual environment**

On Arch Linux, Python packages cannot be installed globally. A virtual environment is required.

```bash
python3 -m venv venv
source venv/bin/activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Generate a self-signed SSL certificate**

HTTPS is required for the browser's Web Speech API (microphone access). A self-signed certificate is generated once using `openssl`:

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes \
  -subj "/CN/<your-local-ip>" \
  -addext "subjectAltName=IP:<your-local-ip>"
```

Replace `<your-local-ip>` with your machine's local IP (find it with `ip addr show`).

The `-addext subjectAltName` flag is required because modern mobile browsers reject certificates that do not include a Subject Alternative Name — they will refuse the connection entirely without showing a warning if this is missing.

**4. Find your machine's local IP**
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**5. Start the server**
```bash
python3 smart_car.py
```

The server starts on port `5000` over HTTPS. On a real Raspberry Pi this would be plain HTTP on port `80`; HTTPS on port `5000` is used here because desktop Linux does not require root for ports above 1024, and HTTPS is needed for microphone access.

---

## Interacting via Smartphone

Ensure your phone is on the **same WiFi network** as your machine, then open the phone's browser and navigate to:

```
https://<your-local-ip>:5000
```

The browser will show a security warning about the self-signed certificate. Tap **Advanced → Proceed** to continue. This is expected and safe on a local network.

### Dashboard UI

The root route `/` serves a mobile-friendly control panel with:

| Element | Function |
|---|---|
| State badge | Shows current vehicle state: IDLE / FORWARD / AVOIDING |
| Green / Red LED indicators | Live visual feedback matching the physical LED behavior |
| Distance slider | Simulates the HC-SR04 sensor reading |
| FORWARD / STOP buttons | Send commands directly |
| HOLD & SPEAK button | Voice control via the phone's built-in speech recognition |

### Voice Control

Tapping **HOLD & SPEAK** activates the browser's Web Speech API. The phone listens for one utterance, displays what it heard, then maps the result to a command:

| You say | Command sent |
|---|---|
| "Forward" | `/control?cmd=forward` |
| "Stop" | `/control?cmd=stop` |

This is the voice-to-text mechanism described in Phase 3 of the lab instructions, implemented entirely using the phone's built-in speech engine — no external AI model is involved.

### Manual URL control (as described in the lab)

| Action | URL |
|---|---|
| Move forward | `https://<your-ip>:5000/control?cmd=forward` |
| Stop | `https://<your-ip>:5000/control?cmd=stop` |

---

## Simulating the HC-SR04 Sensor

The distance slider on the dashboard updates the simulated sensor reading in real time. It can also be set via URL from any browser tab:

**Simulate a clear path:**
```
https://<your-ip>:5000/sensor?dist=100
```

**Simulate an obstacle at 15 cm (triggers autonomous override):**
```
https://<your-ip>:5000/sensor?dist=15
```

This replicates the "Autonomous Event" from Phase 3 of the lab: while the vehicle is in the `forward` state, dropping the distance below 25 cm causes the watchdog thread to instantly override the state to `avoiding` and switch the LED — without waiting for any phone input.

---

## Expected Behavior

| Event | Vehicle State | Green LED | Red LED |
|---|---|---|---|
| Startup | `idle` | OFF | OFF |
| `cmd=forward` (path clear > 30 cm) | `forward` | ON | OFF |
| `cmd=forward` (path blocked ≤ 30 cm) | unchanged | — | — |
| Distance drops below 25 cm while moving | `avoiding` | OFF | ON |
| `cmd=stop` | `idle` | OFF | OFF |

---

## Note on "AI"

The lab title references AI to describe two things:

1. **Voice-to-text input** — the phone's built-in speech recognition converts spoken words into URL parameters. No model runs on the server.
2. **The sensor watchdog** — the `monitor_obstacles` thread continuously reads distance and overrides the vehicle state if an obstacle is detected. This is rule-based logic (`if distance < 25`) rather than a machine learning model.

The "intelligence" of the system is the autonomous decision loop that fuses a high-level user command (voice/button) with low-level sensor data to determine whether motion is safe — which is the core learning objective of the lab.
