"""
Configuration file for ECB Client
Edit these values to match your environment
"""

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================

# IP or hostname of your Node.js signaling server
SIGNALING_SERVER = 'http://YOUR_SERVER_IP:3000'

# Device identifier (displayed on operator dashboard)
DEVICE_ID = 'ECB-001'
DEVICE_LOCATION = 'Main Entrance'

# ============================================================================
# CAMERA CONFIGURATION
# ============================================================================

# RTSP stream URL from your IP camera
# Format: rtsp://[CAMERA_IP]:[PORT]/[STREAM_PATH]
CAMERA_RTSP_URL = 'rtsp://192.168.1.100:554/stream'

# RTSP transport protocol: 'tcp' (more reliable) or 'udp' (faster)
RTSP_TRANSPORT = 'tcp'

# Camera stream format (auto-detected, but can specify: 'rtsp', 'rtmp', etc.)
CAMERA_FORMAT = 'rtsp'

# ============================================================================
# AUDIO CONFIGURATION
# ============================================================================

# Audio input device (microphone)
# Options: 'default' (system default), 'hw:0', 'hw:1' (specific device)
# Find your device with: arecord -l
AUDIO_INPUT_DEVICE = 'default'

# Audio output device (speaker)
# Options: 'default' (system default), 'hw:0', 'hw:1' (specific device)
AUDIO_OUTPUT_DEVICE = 'default'

# Microphone settings
MIC_CHANNELS = 1  # Mono (1) or Stereo (2)
MIC_SAMPLE_RATE = 44100  # Hz (44100 typical)
MIC_FORMAT = 's16'  # Sample format

# ============================================================================
# GPIO BUTTON CONFIGURATION
# ============================================================================

# GPIO pin number (BCM numbering)
BUTTON_PIN = 17

# Button debounce time in milliseconds
# (time to ignore multiple presses)
BUTTON_DEBOUNCE = 2000

# ============================================================================
# WebRTC CONFIGURATION
# ============================================================================

# STUN servers for NAT traversal
# Keep at least one public STUN server for internet connectivity
ICE_SERVERS = [
    {'urls': ['stun:stun.l.google.com:19302']},
    {'urls': ['stun:stun1.l.google.com:19302']},
    # Uncomment for local TURN server:
    # {'urls': ['turn:192.168.1.1:3478'], 'username': 'admin', 'credential': 'password'}
]

# IPv4 candidates only (set False to include IPv6)
PREFER_IPV4 = True

# Enable consent checks (RFC 7675)
ENABLE_CONSENT_CHECK = True

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'INFO'

# Log file path
LOG_FILE = '/var/log/ecb_client.log'

# Maximum log file size (bytes) - 10MB
LOG_FILE_SIZE = 10485760

# Number of backup log files to keep
LOG_BACKUP_COUNT = 5

# ============================================================================
# HEALTH CHECK CONFIGURATION
# ============================================================================

# Health check interval (seconds)
# Checks server connection and call status
HEALTH_CHECK_INTERVAL = 30

# Timeout for connection attempts (seconds)
CONNECTION_TIMEOUT = 10

# Reconnection delay (seconds)
RECONNECT_DELAY = 5

# ============================================================================
# MEDIA RECORDING CONFIGURATION
# ============================================================================

# Directory to save audio/video recordings
RECORDINGS_DIR = '/tmp'

# Record operator audio to file (for debugging)
RECORD_OPERATOR_AUDIO = False

# Record call statistics
RECORD_STATS = True

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Maximum bitrate for video (kbps)
# Higher = better quality, more bandwidth
VIDEO_MAX_BITRATE = 2500

# Maximum bitrate for audio (kbps)
AUDIO_MAX_BITRATE = 128

# Preferred codecs (in order of preference)
# WebRTC will use the first mutually supported codec
PREFERRED_VIDEO_CODECS = ['VP8', 'VP9', 'H264']
PREFERRED_AUDIO_CODECS = ['opus', 'PCMU']

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Enable DTLS (Datagram Transport Layer Security) for encrypted RTC
ENABLE_DTLS = True

# DTLS fingerprint algorithm
DTLS_FINGERPRINT_ALGORITHM = 'sha-256'

# Enable SRTP (Secure Real-time Transport Protocol)
ENABLE_SRTP = True
