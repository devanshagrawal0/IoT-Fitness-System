# Smart Gym Raspberry Pi Telemetry

This project converts any standard gym machine into a **smart IoT device** using a Raspberry Pi and a Hall-effect sensor.  
It tracks reps, cadence, and activity in real time, logs the data locally, and can stream it to a remote server.

---

## Hardware
- Raspberry Pi  
- Hall-effect sensor (e.g., A3144)  
- Magnet(s) on the moving part of the machine  

**Wiring (typical):**
- VCC → 3.3V  
- GND → GND  
- OUT → GPIO (default BCM 17)

---

## What the system does
1. Reads magnetic pulses from the Hall-effect sensor  
2. Converts pulses → reps and cadence  
3. Estimates workout intensity  
4. Logs all data to a CSV file  
5. Optionally sends live telemetry to a server

This allows gyms to upgrade **any existing machine** into a data-driven smart device.

---

## Installed (on Raspberry Pi)
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip
pip3 install -r requirements.txt
