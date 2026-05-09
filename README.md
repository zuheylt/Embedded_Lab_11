# LAB 11: Autonomous Smart Vehicle with AI & Emergency Override
**AGU EE 304 — Embedded Systems**
Instructor: Dr. Khaled Hejja

---

## Overview

This project implements the Lab 11 smart vehicle state machine in Python. Because a physical Raspberry Pi 5 was unavailable, the hardware layer has been substituted with a software simulation while preserving the full software architecture described in the lab (threading model, Flask web server, state machine logic, and smartphone control interface).

---

## Hardware Substitutions

| Lab Component | Substitution | Notes |
|---|---|---|
| Raspberry Pi 5 | Desktop Linux machine | Runs the same Python code |
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

## How to Run

**1. Install dependencies**
```bash
pip install flask
```

**2. Find your machine's local IP**
```bash
ip addr show | grep "inet "
# Example output: 192.168.1.75
```

**3. Start the server**
```bash
python3 smart_car.py
```

The server starts on port `5000`. On a real Raspberry Pi this would be port `80`; port `5000` is used here to avoid requiring root privileges.

---

## Interacting via Smartphone (Phase 3 — unchanged from lab)

Ensure your phone is on the **same WiFi network** as your machine, then open the phone's browser.

| Action | URL |
|---|---|
| Move forward | `http://192.168.1.75:5000/control?cmd=forward` |
| Stop | `http://192.168.1.75:5000/control?cmd=stop` |

> Replace `192.168.1.75` with your machine's actual local IP address.

---

## Simulating the HC-SR04 Sensor

Since there is no physical sensor, obstacle distance is injected via a dedicated endpoint. This replicates the effect of waving your hand in front of the sensor during the lab demo.

**Simulate a clear path (100 cm):**
```
http://192.168.1.75:5000/sensor?dist=100
```

**Simulate an obstacle at 15 cm (triggers emergency override):**
```
http://192.168.1.75:5000/sensor?dist=15
```

This can be done from the phone's browser or a second browser tab, matching the "Autonomous Event" described in Phase 3 of the lab instructions.

---

## Expected Behavior

| Command / Event | Vehicle State | Green LED | Red LED |
|---|---|---|---|
| Startup | `idle` | OFF | OFF |
| `cmd=forward` (path clear) | `forward` | ON | OFF |
| `cmd=stop` | `idle` | OFF | OFF |
| `cmd=forward` (path blocked) | unchanged | — | — |
| Obstacle detected < 25 cm while moving | `avoiding` | OFF | ON |
