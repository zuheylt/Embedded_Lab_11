# --- LAB 11: SMART VEHICLE CONTROL WITH STANDALONE AVOIDANCE ---

# 1. LIBRARY INCLUSION
# import RPi.GPIO as GPIO  <-- substituted below with SimulatedGPIO
import time
import _thread
from flask import Flask, request, jsonify, render_template_string

# =============================================================================
# SUBSTITUTION: RPi.GPIO
# SimulatedGPIO exposes the exact same API (setmode, setup, output, input).
# Instead of switching physical pins it prints the LED state to the terminal
# in color so the behavior is still visible during the demo.
# =============================================================================
_GREEN = "\033[92m"
_RED   = "\033[91m"
_RESET = "\033[0m"

class SimulatedGPIO:
    BCM  = "BCM"
    OUT  = "OUT"
    IN   = "IN"
    HIGH = 1
    LOW  = 0

    _states = {}

    @classmethod
    def setmode(cls, mode):
        pass

    @classmethod
    def setup(cls, pin, direction):
        cls._states[pin] = cls.LOW

    @classmethod
    def output(cls, pin, value):
        if cls._states.get(pin) == value:
            return
        cls._states[pin] = value
        if pin == LED_GREEN:
            label = f"{_GREEN}[GREEN LED] {'ON  — Forward motion active' if value == cls.HIGH else 'OFF'}{_RESET}"
        elif pin == LED_RED:
            label = f"{_RED}[RED LED]   {'ON  — Obstacle / Emergency!' if value == cls.HIGH else 'OFF'}{_RESET}"
        else:
            return
        print(label)

    @classmethod
    def input(cls, pin):
        return cls._states.get(pin, cls.LOW)

GPIO = SimulatedGPIO()

# --- 2. GPIO PIN CONFIGURATION ---
GPIO.setmode(GPIO.BCM)

TRIG_PIN  = 17
ECHO_PIN  = 27
LED_GREEN = 14
LED_RED   = 15

GPIO.setup(TRIG_PIN,  GPIO.OUT)
GPIO.setup(ECHO_PIN,  GPIO.IN)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(LED_RED,   GPIO.OUT)

# --- 3. GLOBAL VARIABLES ---
global vehicle_state
vehicle_state = "idle"

global current_distance
current_distance = 100.0

# =============================================================================
# SUBSTITUTION: HC-SR04 Ultrasonic Sensor
# A real sensor pulses TRIG and times the ECHO pin to measure distance.
# Here, simulated_distance holds the current reading and is updated via the
# /sensor?dist=X endpoint — equivalent to waving a hand at the sensor.
# =============================================================================
global simulated_distance
simulated_distance = 100.0

# --- 4. ULTRASONIC SENSOR LOGIC (CORE 1: THE WATCHDOG) ---
def monitor_obstacles():
    """This function runs forever in the background checking distance."""
    global current_distance
    global vehicle_state
    global simulated_distance

    while True:
        # SUBSTITUTION: read injected value instead of pulsing the GPIO pins
        current_distance = simulated_distance

        if current_distance < 25 and vehicle_state == "forward":
            print(f"!!! STANDALONE OVERRIDE: Obstacle at {current_distance}cm !!!")
            vehicle_state = "avoiding"

        time.sleep(0.1)

# --- 5. HARDWARE EXECUTION LOOP ---
def run_hardware():
    """This function turns states into real-world hardware responses."""
    global vehicle_state

    while True:
        if vehicle_state == "forward":
            GPIO.output(LED_GREEN, GPIO.HIGH)
            GPIO.output(LED_RED,   GPIO.LOW)

        elif vehicle_state == "avoiding":
            GPIO.output(LED_GREEN, GPIO.LOW)
            GPIO.output(LED_RED,   GPIO.HIGH)

        else:
            GPIO.output(LED_GREEN, GPIO.LOW)
            GPIO.output(LED_RED,   GPIO.LOW)

        time.sleep(0.1)

# --- 6. FLASK WEB INTERFACE (REMOTE CONTROL) ---
app = Flask(__name__)

DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Car — Lab 11</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: monospace;
      background: #111;
      color: #eee;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 16px;
      gap: 24px;
    }
    h1 { font-size: 1.2rem; letter-spacing: 2px; color: #aaa; }

    /* State badge */
    #state-badge {
      font-size: 1.6rem;
      font-weight: bold;
      padding: 10px 28px;
      border-radius: 8px;
      background: #222;
      letter-spacing: 2px;
      transition: background 0.3s;
    }

    /* LEDs */
    .leds { display: flex; gap: 32px; align-items: center; }
    .led-wrap { display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 0.8rem; color: #888; }
    .led {
      width: 52px; height: 52px;
      border-radius: 50%;
      transition: background 0.2s, box-shadow 0.2s;
    }
    .led-green-off { background: #0a2a0a; }
    .led-green-on  { background: #00ff00; box-shadow: 0 0 18px 4px #00ff00; }
    .led-red-off   { background: #2a0a0a; }
    .led-red-on    { background: #ff2020; box-shadow: 0 0 18px 4px #ff2020; }

    /* Distance */
    .dist-box {
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 8px;
      padding: 14px 24px;
      text-align: center;
      width: 100%;
      max-width: 360px;
    }
    .dist-box span { font-size: 2rem; font-weight: bold; }
    .dist-box label { display: block; color: #888; font-size: 0.8rem; margin-bottom: 8px; }

    /* Slider */
    input[type=range] { width: 100%; accent-color: #00aaff; cursor: pointer; }

    /* Buttons */
    .controls { display: flex; gap: 16px; width: 100%; max-width: 360px; }
    button {
      flex: 1;
      padding: 18px;
      font-size: 1.1rem;
      font-family: monospace;
      font-weight: bold;
      letter-spacing: 1px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      transition: opacity 0.15s;
    }
    button:active { opacity: 0.7; }
    #btn-forward { background: #00cc44; color: #000; }
    #btn-stop    { background: #cc2200; color: #fff; }

    /* Mic button */
    #btn-mic {
      width: 100%;
      max-width: 360px;
      padding: 18px;
      font-size: 1.1rem;
      font-family: monospace;
      font-weight: bold;
      letter-spacing: 1px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      background: #1a4a8a;
      color: #fff;
      transition: background 0.2s, opacity 0.15s;
    }
    #btn-mic.listening {
      background: #aa4400;
      animation: pulse 1s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0.5; }
    }
    #btn-mic:active { opacity: 0.7; }

    /* Response */
    #response {
      font-size: 0.85rem;
      color: #888;
      min-height: 1.2em;
    }
  </style>
</head>
<body>
  <h1>LAB 11 — SMART CAR</h1>

  <div id="state-badge">IDLE</div>

  <div class="leds">
    <div class="led-wrap">
      <div class="led led-green-off" id="led-green"></div>
      GREEN
    </div>
    <div class="led-wrap">
      <div class="led led-red-off" id="led-red"></div>
      RED
    </div>
  </div>

  <div class="dist-box">
    <label>SENSOR DISTANCE (cm)</label>
    <span id="dist-val">100</span> cm
    <br><br>
    <input type="range" min="5" max="150" value="100" id="slider"
           oninput="updateDist(this.value)">
  </div>

  <div class="controls">
    <button id="btn-forward" onclick="sendCmd('forward')">FORWARD</button>
    <button id="btn-stop"    onclick="sendCmd('stop')">STOP</button>
  </div>

  <button id="btn-mic" onclick="startVoice()">🎤 HOLD &amp; SPEAK</button>

  <div id="response"></div>

  <script>
    function sendCmd(cmd) {
      fetch('/control?cmd=' + cmd)
        .then(r => r.json())
        .then(d => { document.getElementById('response').innerText = d.status; });
    }

    function updateDist(v) {
      document.getElementById('dist-val').innerText = v;
      fetch('/sensor?dist=' + v);
    }

    function poll() {
      fetch('/status')
        .then(r => r.json())
        .then(d => {
          const badge = document.getElementById('state-badge');
          badge.innerText = d.state.toUpperCase();
          badge.style.color = d.state === 'forward' ? '#00ff00'
                            : d.state === 'avoiding' ? '#ff2020'
                            : '#aaa';

          document.getElementById('led-green').className =
            'led ' + (d.led_green ? 'led-green-on' : 'led-green-off');
          document.getElementById('led-red').className =
            'led ' + (d.led_red ? 'led-red-on' : 'led-red-off');

          const slider = document.getElementById('slider');
          if (document.activeElement !== slider) {
            slider.value = d.distance;
            document.getElementById('dist-val').innerText = d.distance.toFixed(0);
          }
        });
    }

    setInterval(poll, 300);
    poll();

    // --- VOICE CONTROL (Web Speech API) ---
    const micBtn = document.getElementById('btn-mic');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      micBtn.innerText = '🎤 NOT SUPPORTED';
      micBtn.disabled = true;
    } else {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        micBtn.classList.add('listening');
        micBtn.innerText = '🎤 LISTENING...';
        document.getElementById('response').innerText = '';
      };

      recognition.onresult = (e) => {
        const heard = e.results[0][0].transcript.toLowerCase();
        document.getElementById('response').innerText = 'Heard: "' + heard + '"';
        if (heard.includes('forward')) {
          sendCmd('forward');
        } else if (heard.includes('stop')) {
          sendCmd('stop');
        } else {
          document.getElementById('response').innerText += ' — Unknown Command';
        }
      };

      recognition.onerror = (e) => {
        document.getElementById('response').innerText = 'Mic error: ' + e.error;
      };

      recognition.onend = () => {
        micBtn.classList.remove('listening');
        micBtn.innerText = '🎤 HOLD & SPEAK';
      };

      function startVoice() { recognition.start(); }
    }
  </script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD)

@app.route("/status")
def get_status():
    return jsonify({
        "state":     vehicle_state,
        "distance":  current_distance,
        "led_green": GPIO._states.get(LED_GREEN, 0),
        "led_red":   GPIO._states.get(LED_RED,   0),
    })

@app.route("/control")
def receive_command():
    global vehicle_state
    cmd = request.args.get('cmd', '').lower()

    if "forward" in cmd:
        if current_distance > 30:
            vehicle_state = "forward"
            return jsonify({"status": "Moving Forward"})
        else:
            return jsonify({"status": "Error: Path Blocked"})

    elif "stop" in cmd:
        vehicle_state = "idle"
        return jsonify({"status": "Stopping"})

    return jsonify({"status": "Unknown Command"})

# SUBSTITUTION endpoint — simulates the HC-SR04 reading.
# Use from phone browser or second tab: /sensor?dist=15
@app.route("/sensor")
def set_sensor():
    global simulated_distance
    dist = request.args.get('dist', type=float)
    if dist is None:
        return jsonify({"error": "Provide ?dist=<cm>"}), 400
    simulated_distance = dist
    return jsonify({"simulated_distance_cm": simulated_distance})

# --- 7. MAIN EXECUTION ---
if __name__ == "__main__":
    _thread.start_new_thread(monitor_obstacles, ())
    _thread.start_new_thread(run_hardware, ())
    # Port 5000 instead of 80 — no sudo needed on a desktop Linux machine.
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
