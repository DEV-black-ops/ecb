# ECB Client - Emergency Call Button WebRTC System

A Raspberry Pi WebRTC client for emergency call button systems. When a physical button is pressed, it initiates a secure audio/video call with a remote operator through a Node.js signaling server.

## 🎯 Features

- **WebRTC-based Audio/Video Calls** - Secure peer-to-peer communication
- **IP Camera Support** - RTSP stream integration from surveillance cameras
- **USB Microphone/Speaker** - Clear audio input/output
- **GPIO Button Detection** - Hardware button trigger with debounce
- **Auto-reconnection** - Automatic reconnection to signaling server
- **Detailed Logging** - Comprehensive logs for debugging
- **Systemd Integration** - Auto-start on Raspberry Pi boot

## 📋 System Architecture

```
┌─────────────────┐
│  Raspberry Pi   │
│  (ECB Client)   │───RTSP───┌──────────────┐
│  • Button (GPIO)│          │ IP Camera    │
│  • Mic/Speaker  │          └──────────────┘
│  • WebRTC PC    │
└────────┬────────┘
         │ WebSocket
         │ (Socket.io)
         │
┌────────▼────────────────────┐
│  Node.js Signaling Server   │
│  (Relays SDP & ICE)         │
└────────┬────────────────────┘
         │ WebSocket
         │ (Socket.io)
         │
┌────────▼──────────────────────┐
│  Operator Browser Dashboard   │
│  • Accept/End Calls           │
│  • View Remote Video/Audio    │
│  • Send Commands              │
└───────────────────────────────┘
```

## 📦 Quick Start

### 1. **Configure for Your Environment**

Edit `config.py`:
```python
SIGNALING_SERVER = 'http://192.168.1.50:3000'  # Your server IP
CAMERA_RTSP_URL = 'rtsp://192.168.1.100:554/stream'  # Your camera IP
```

### 2. **Run Diagnostics** (recommended first step)

```bash
python3 diagnostics.py
```

This checks:
- Python/dependencies
- GPIO access
- Audio devices
- Camera RTSP stream
- Network connectivity
- Socket.io server

### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 4. **Test the Client**

```bash
# Manual test (for debugging)
python3 ecb_client.py
```

### 5. **Set Up Auto-start**

```bash
# Copy systemd service
sudo cp ecb_client.service /etc/systemd/system/

# Enable auto-start
sudo systemctl enable ecb_client
sudo systemctl start ecb_client

# Check status
sudo systemctl status ecb_client
```

## 📁 File Structure

```
ecb/
├── ecb_client.py          # Main WebRTC client (run this)
├── config.py              # Configuration (edit this)
├── requirements.txt       # Python dependencies
├── ecb_client.service     # Systemd service for auto-start
├── diagnostics.py         # Troubleshooting tool
├── SETUP.md              # Detailed setup guide
├── README.md             # This file
└── server.py             # TCP socket server (legacy - kept for reference)
```

## 🔧 Configuration Reference

### Key Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `SIGNALING_SERVER` | `http://YOUR_SERVER_IP:3000` | Node.js server address |
| `CAMERA_RTSP_URL` | `rtsp://192.168.1.100:554/stream` | IP camera stream URL |
| `BUTTON_PIN` | `17` | GPIO pin for button |
| `BUTTON_DEBOUNCE` | `2000` | Button debounce time (ms) |
| `LOG_LEVEL` | `INFO` | Logging detail (DEBUG/INFO/WARNING/ERROR) |

See `config.py` for all options.

## 🚀 Common Tasks

### View Live Logs

```bash
# Real-time logs from systemd
sudo journalctl -u ecb_client -f

# Last 50 lines
sudo journalctl -u ecb_client -n 50

# Logs from last hour
sudo journalctl -u ecb_client --since "1 hour ago"
```

### Stop/Restart Client

```bash
# Stop
sudo systemctl stop ecb_client

# Restart
sudo systemctl restart ecb_client

# Disable auto-start
sudo systemctl disable ecb_client
```

### Test Individual Components

```bash
# Test camera stream
ffprobe rtsp://192.168.1.100:554/stream

# Test microphone
arecord -D default -f cd -t wav /tmp/test.wav && aplay /tmp/test.wav

# Test speaker
speaker-test -t sine -f 1000 -l 1

# Test GPIO button
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP); print('GPIO 17 state:', GPIO.input(17)); GPIO.cleanup()"

# Test network to server
curl -I http://192.168.1.50:3000
```

### Update Code

```bash
# Stop service
sudo systemctl stop ecb_client

# Pull latest changes
git pull  # if using git

# Reinstall dependencies if needed
pip install -r requirements.txt

# Restart
sudo systemctl start ecb_client
```

## 🐛 Troubleshooting

### Symptom: "Connection refused" to signaling server

**Cause:** Server unreachable or wrong IP/port

**Fix:**
```bash
# Verify server is running
telnet 192.168.1.50 3000

# Check server IP
ip route | grep default

# Update config.py with correct IP
```

### Symptom: Camera stream not loading

**Cause:** Invalid RTSP URL or camera offline

**Fix:**
```bash
# Test RTSP with ffprobe
ffprobe rtsp://192.168.1.100:554/stream

# Check camera web UI
# http://192.168.1.100
# Verify RTSP is enabled

# Check same LAN
ping 192.168.1.100
```

### Symptom: No audio from microphone

**Cause:** Device not detected or wrong device

**Fix:**
```bash
# List audio devices
arecord -l

# Test recording
arecord -D hw:1,0 -f cd -t wav /tmp/test.wav
aplay /tmp/test.wav

# Update config.py AUDIO_INPUT_DEVICE if needed
```

### Symptom: Button press not detected

**Cause:** GPIO permissions or wiring issue

**Fix:**
```bash
# Check GPIO permissions
groups pi  # should include 'gpio'

# Test GPIO directly
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"

# Verify button wiring:
# Button pin → GPIO 17
# Other side → GND
# Internal pull-up enabled in code
```

### Symptom: High CPU usage / Device gets hot

**Cause:** Camera stream too high quality or infinite error loops

**Fix:**
```bash
# Lower camera resolution in IP camera web UI

# Check for error loops
sudo journalctl -u ecb_client -f | grep -i error

# Increase log level to DEBUG to find issues
# config.py: LOG_LEVEL = 'DEBUG'
```

## 🔐 Security Recommendations

1. **Use HTTPS for signaling** (in production):
   - Configure TLS on Node.js server
   - Update SIGNALING_SERVER to `https://`

2. **Secure IP Camera**:
   - Change default camera login
   - Use strong RTSP password
   - Keep camera on isolated LAN

3. **Firewall Rules**:
   - Only allow port 3000 from trusted networks
   - Block direct access to Pi except SSH

4. **Encryption**:
   - WebRTC uses DTLS/SRTP by default (encrypted)
   - Audio/video encrypted end-to-end

## 📚 Hardware Wiring Diagram

```
Button Wiring:
┌──────────┐
│ Button   │──(NO contact)──┬────→ GPIO 17 (Pi pin 11)
│ (N.O.)   │                │
└──────────┘                │
                       Pull-up (enabled in code)
                            │
                           GND (Pi pin 6)

USB Microphone:
USB Hub ─────→ (any USB port)

Audio Out (Optional):
Pi 3.5mm ─────→ PAM8403 IN ─────→ 4Ω Speaker
Pi GND   ─────→ PAM8403 GND
Pi 5V    ─────→ PAM8403 VCC
```

## 📞 Developer Info

### API Events (Client → Server)

```javascript
// Button pressed - initiate call
socket.emit('call_request', {
  from: 'ECB-001',
  location: 'Main Entrance',
  timestamp: '2026-04-10T10:30:00'
})

// WebRTC session description
socket.emit('sdp_offer', {
  sdp: '...',
  type: 'offer'
})

// ICE candidate
socket.emit('ice_candidate', {
  candidate: {...},
  target: 'operator'
})
```

### Expected Events (Server → Client)

```javascript
// Operator accepted the call
socket.on('call_accepted', (data) => {
  // data.sdp_answer - remote SDP answer
})

// Remote ICE candidate
socket.on('ice_candidate', (data) => {
  // data.candidate - ICE candidate
})

// Call ended by operator
socket.on('call_ended', () => {
  // cleanup connection
})
```

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

Found a bug? Have a suggestion?

1. Check existing issues on GitHub
2. Create a detailed bug report
3. Include:
   - OS/Python version
   - `diagnostics.py` output
   - Relevant log excerpt
   - Steps to reproduce

## 📞 Support

For issues:
1. Run `python3 diagnostics.py` first
2. Check [SETUP.md](SETUP.md) for detailed instructions
3. Review logs: `sudo journalctl -u ecb_client -f`
4. See troubleshooting section above

---

**Version**: 1.0.0  
**Last Updated**: April 2026  
**Python**: 3.9+  
**OS**: Raspberry Pi OS (Bullseye+)
