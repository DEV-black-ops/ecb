# ECB Client - Raspberry Pi Setup Guide

## Prerequisites

- Raspberry Pi 4 (2GB+ RAM recommended)
- Raspberry Pi OS (Bullseye or newer)
- Python 3.9+
- USB microphone connected
- IP camera with RTSP stream on same LAN
- PAM8403 amplifier + speaker connected to Pi's audio jack (optional)
- Momentary push button on GPIO pin 17

## Step 1: Prepare Raspberry Pi

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3-dev \
    python3-pip \
    libopus-dev \
    libvpx-dev \
    pkg-config \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    libopus-dev \
    libvpx-dev \
    pkg-config
```

## Step 2: Clone/Copy Project Files

```bash
cd ~
mkdir -p ecb
cd ecb
# Copy ecb_client.py and requirements.txt to /home/pi/ecb/
```

## Step 3: Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install pip dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# If av installation fails, install pre-built wheel
pip install --only-binary :all: av
```

## Step 4: Configure Camera & Audio

### Test Camera Stream
```bash
# Test RTSP connectivity
gsacapsinfo rtsp://192.168.1.100:554/stream

# Or use ffprobe
ffprobe rtsp://192.168.1.100:554/stream
```

### Test Microphone
```bash
# List available audio devices
arecord -l

# Record 5 seconds of audio
arecord -D hw:1,0 -f cd -t wav test.wav

# Play it back
aplay test.wav
```

### Test Speaker Output
```bash
# If using PAM8403 amplifier on GPIO pins:
# Ensure volume is increased
alsamixer  # Press F5 to select sound card, adjust with arrow keys

# Test with tone
speaker-test -t sine -f 1000 -l 1
```

## Step 5: Configure IP Camera

### Access Camera Web UI
Navigate to `http://[CAMERA_IP]` in browser

### Enable RTSP
1. Login to camera (default is usually admin/12345)
2. Go to Settings → Video → Video Stream
3. Enable RTSP protocol
4. Note the RTSP stream URL (usually rtsp://[IP]:554/stream)

## Step 6: Update Configuration

Edit `ecb_client.py` and update these variables:

```python
SIGNALING_SERVER = 'http://YOUR_SERVER_IP:3000'  # Your Node.js server IP
CAMERA_RTSP_URL = 'rtsp://192.168.1.100:554/stream'  # Your camera RTSP URL
```

## Step 7: Test the Client

```bash
# Run directly (for debugging)
python3 ecb_client.py

# Mock test without hardware (check connections only)
python3 -c "
import sys
sys.path.insert(0, '.')
from ecb_client import *
print('✓ Imports successful')
"
```

## Step 8: Set Up Auto-start with Systemd

```bash
# Copy service file
sudo cp ecb_client.service /etc/systemd/system/

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable ecb_client
sudo systemctl start ecb_client

# Check status
sudo systemctl status ecb_client

# View logs
sudo journalctl -u ecb_client -f  # Follow logs
sudo journalctl -u ecb_client --since "1 hour ago"  # Last hour
```

## Step 9: Verify GPIO Button

```bash
# Test GPIO pin 17
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('GPIO 17 state:', GPIO.input(17))
GPIO.cleanup()
"

# When button is pressed, GPIO 17 should go from 1 → 0
```

## Step 10: Network Configuration (Local TURN Server - Optional)

For reliable P2P connection without internet:

```bash
# Install coturn (TURN/STUN server)
sudo apt install coturn

# Edit /etc/coturn/turnserver.conf
sudo nano /etc/coturn/turnserver.conf

# Add:
# listening-port=3478
# fingerprint
# user=admin:password
# realm=192.168.1.1

# Enable and start
sudo systemctl enable coturn
sudo systemctl start coturn
```

Then update the WebRTC config in `ecb_client.py`:
```python
iceServers=[
    {'urls': ['stun:192.168.1.1:3478']},
    {'urls': ['turn:192.168.1.1:3478'], 'username': 'admin', 'credential': 'password'}
]
```

## Troubleshooting

### Camera Stream Not Loading
```bash
# Check RTSP connectivity with verbose output
ffmpeg -rtsp_transport tcp -v verbose -i rtsp://192.168.1.100:554/stream -f null -
```

### Microphone Issues
```bash
# Check audio devices
arecord -l
pactl list short sources

# Test specific device
arecord -D hw:1,0 -f cd -t wav /tmp/test.wav && aplay /tmp/test.wav
```

### No Connection to Server
```bash
# Test connectivity
telnet YOUR_SERVER_IP 3000
nc -zv YOUR_SERVER_IP 3000
```

### GPIO Permission Denied
```bash
# Add pi user to gpio group
sudo usermod -a -G gpio pi
# Log out and log back in
```

### High CPU Usage
- Reduce camera resolution in IP camera settings
- Lower frame rate in camera RTSP stream settings
- Check for error loops in logs

## Monitoring

### View Real-time Logs
```bash
sudo journalctl -u ecb_client -f
```

### Check Process Status
```bash
ps aux | grep ecb_client
```

### Monitor Resource Usage
```bash
top -p $(pgrep -f ecb_client)
```

## Updating the Code

```bash
# Stop service
sudo systemctl stop ecb_client

# Pull new code
cd ~/ecb
git pull origin main  # if using git

# Reinstall dependencies (if changed)
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start ecb_client
```

## Hardware Wiring

### GPIO Button
```
GPIO 17 ----[Button]---- GND
(with internal pull-up enabled)
```

### USB Microphone
- Connect to any USB port on Pi

### Audio Output (Optional PAM8403 Amp)
```
Pi 3.5mm Audio Jack → PAM8403 IN+/IN-
PAM8403 OUT → 4Ω Speaker
PAM8403 VCC → Pi 5V
PAM8403 GND → Pi GND
```

## Support & Logs

If issues persist, collect diagnostic info:
```bash
#!/bin/bash
echo "=== Pi Info ==="
uname -a
python3 --version
echo "=== Network ==="
ip addr | grep inet
ping -c 1 YOUR_SERVER_IP
echo "=== Audio Devices ==="
arecord -l
echo "=== Logs ==="
sudo journalctl -u ecb_client -n 50
```
