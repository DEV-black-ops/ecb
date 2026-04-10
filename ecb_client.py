"""
ECB (Emergency Call Button) - Raspberry Pi Client
WebRTC-based audio/video call system with button trigger
"""

import RPi.GPIO as GPIO
import socketio
import asyncio
import logging
from datetime import datetime
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRecorder
import av

# ============================================================================
# CONFIGURATION
# ============================================================================

BUTTON_PIN = 17
SIGNALING_SERVER = 'http://YOUR_SERVER_IP:3000'  # Replace with your server IP
CAMERA_RTSP_URL = 'rtsp://192.168.1.100:554/stream'  # Replace with your camera IP
AUDIO_DEVICE = 'default'  # USB microphone
SPEAKER_DEVICE = 'default'  # Speaker output

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ecb_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE
# ============================================================================

class ECBState:
    def __init__(self):
        self.sio = socketio.AsyncClient()
        self.pc = None  # RTCPeerConnection
        self.call_active = False
        self.camera_stream = None
        self.mic_stream = None
        self.speaker_recorder = None
        self.event_loop = None
        
state = ECBState()

# ============================================================================
# GPIO BUTTON SETUP
# ============================================================================

def setup_gpio():
    """Initialize GPIO for button detection"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        logger.info("GPIO initialized for button on pin %d", BUTTON_PIN)
    except Exception as e:
        logger.error("Failed to initialize GPIO: %s", e)
        raise

def cleanup_gpio():
    """Clean up GPIO resources"""
    try:
        GPIO.cleanup()
        logger.info("GPIO cleanup complete")
    except Exception as e:
        logger.error("Failed to cleanup GPIO: %s", e)

# ============================================================================
# SOCKET.IO CONNECTION & SIGNALING
# ============================================================================

@state.sio.on('connect')
async def on_connect():
    """Handle connection to signaling server"""
    logger.info("Connected to signaling server")
    # Register as ECB device
    await state.sio.emit('register', 'ecb')

@state.sio.on('disconnect')
async def on_disconnect():
    """Handle disconnection from signaling server"""
    logger.warning("Disconnected from signaling server")
    if state.pc:
        await state.pc.close()
        state.pc = None
    state.call_active = False

@state.sio.on('sdp_offer')
async def on_sdp_offer(data):
    """Handle incoming SDP offer from operator"""
    logger.info("Received SDP offer from operator")
    try:
        if state.pc:
            sdp_offer = RTCSessionDescription(sdp=data['sdp'], type='offer')
            await state.pc.setRemoteDescription(sdp_offer)
            
            # Create and send answer
            answer = await state.pc.createAnswer()
            await state.pc.setLocalDescription(answer)
            
            await state.sio.emit('sdp_answer', {
                'sdp': state.pc.localDescription.sdp,
                'type': 'answer'
            })
            logger.info("SDP answer sent to operator")
    except Exception as e:
        logger.error("Error handling SDP offer: %s", e)

@state.sio.on('ice_candidate')
async def on_ice_candidate(data):
    """Handle incoming ICE candidate from operator"""
    try:
        if state.pc and data.get('candidate'):
            await state.pc.addIceCandidate(data['candidate'])
            logger.debug("ICE candidate added")
    except Exception as e:
        logger.error("Error adding ICE candidate: %s", e)

@state.sio.on('call_ended')
async def on_call_ended():
    """Handle call termination from operator"""
    logger.info("Call ended by operator")
    await stop_call()

async def connect_to_server():
    """Connect to Socket.io signaling server"""
    try:
        logger.info("Connecting to signaling server at %s", SIGNALING_SERVER)
        await state.sio.connect(SIGNALING_SERVER)
        await state.sio.wait()
    except Exception as e:
        logger.error("Failed to connect to signaling server: %s", e)
        raise

# ============================================================================
# WebRTC SETUP
# ============================================================================

async def load_camera_stream():
    """Load RTSP camera stream"""
    try:
        logger.info("Loading camera stream from %s", CAMERA_RTSP_URL)
        player = MediaPlayer(
            CAMERA_RTSP_URL,
            format='rtsp',
            options={'rtsp_transport': 'tcp'}
        )
        state.camera_stream = player
        return player
    except Exception as e:
        logger.error("Failed to load camera stream: %s", e)
        return None

async def load_microphone_stream():
    """Load USB microphone stream"""
    try:
        logger.info("Loading microphone stream")
        mic = MediaPlayer(
            f'default',
            format='alsa',
            options={'channels': '1', 'sample_rate': '44100'}
        )
        state.mic_stream = mic
        return mic
    except Exception as e:
        logger.error("Failed to load microphone: %s", e)
        return None

async def start_webrtc_call():
    """Initialize WebRTC peer connection and start media streams"""
    try:
        logger.info("Starting WebRTC call")
        
        # Create peer connection with STUN servers
        state.pc = RTCPeerConnection(
            iceServers=[
                {'urls': ['stun:stun.l.google.com:19302']},
                {'urls': ['stun:stun1.l.google.com:19302']}
            ]
        )
        
        # Load camera stream
        camera = await load_camera_stream()
        if camera and camera.video:
            state.pc.addTrack(camera.video)
            logger.info("Camera video track added")
        else:
            logger.warning("No video track available from camera")
        
        # Load microphone stream
        mic = await load_microphone_stream()
        if mic and mic.audio:
            state.pc.addTrack(mic.audio)
            logger.info("Microphone audio track added")
        else:
            logger.warning("No audio track available from microphone")
        
        # Handle incoming audio/video from operator
        @state.pc.on("track")
        async def on_track(track):
            logger.info("Received %s track from operator", track.kind)
            
            if track.kind == "audio":
                # Create a recorder to pipe audio to speaker
                audio_file = f'/tmp/ecb_audio_{datetime.now().timestamp()}.wav'
                recorder = MediaRecorder(audio_file)
                recorder.addTrack(track)
                await recorder.start()
                state.speaker_recorder = recorder
                logger.info("Audio recorder started for speaker")
            
            elif track.kind == "video":
                logger.info("Video track received (for future use)")
        
        # Handle ICE candidates
        @state.pc.on("icecandidate")
        async def on_ice(candidate):
            if candidate:
                await state.sio.emit('ice_candidate', {
                    'candidate': candidate,
                    'target': 'operator'
                })
                logger.debug("ICE candidate sent to operator")
        
        # Create SDP offer and send to operator
        offer = await state.pc.createOffer()
        await state.pc.setLocalDescription(offer)
        
        await state.sio.emit('sdp_offer', {
            'sdp': state.pc.localDescription.sdp,
            'type': 'offer'
        })
        logger.info("WebRTC call initiated - SDP offer sent to operator")
        state.call_active = True
        
    except Exception as e:
        logger.error("Error starting WebRTC call: %s", e)
        state.call_active = False
        raise

async def stop_call():
    """Terminate WebRTC call and clean up resources"""
    try:
        logger.info("Stopping call")
        
        # Close speaker recorder
        if state.speaker_recorder:
            await state.speaker_recorder.stop()
            state.speaker_recorder = None
        
        # Close peer connection
        if state.pc:
            await state.pc.close()
            state.pc = None
        
        # Stop media streams
        if state.camera_stream:
            state.camera_stream = None
        if state.mic_stream:
            state.mic_stream = None
        
        state.call_active = False
        logger.info("Call stopped and resources cleaned up")
        
    except Exception as e:
        logger.error("Error stopping call: %s", e)

# ============================================================================
# BUTTON PRESS HANDLER
# ============================================================================

def button_callback(channel):
    """Handle button press event"""
    logger.info("Button pressed on GPIO pin %d", channel)
    
    try:
        # Debounce: only trigger if not already in a call
        if not state.call_active and state.event_loop:
            # Schedule call initiation in the event loop
            asyncio.run_coroutine_threadsafe(
                initiate_call(),
                state.event_loop
            )
    except Exception as e:
        logger.error("Error in button callback: %s", e)

def setup_button_detection():
    """Set up edge detection for button press"""
    try:
        GPIO.add_event_detect(
            BUTTON_PIN,
            GPIO.FALLING,  # Button press (goes from HIGH to LOW)
            callback=button_callback,
            bouncetime=2000  # 2 second debounce
        )
        logger.info("Button edge detection enabled (GPIO pin %d)", BUTTON_PIN)
    except Exception as e:
        logger.error("Failed to set up button detection: %s", e)
        raise

# ============================================================================
# CALL INITIATION
# ============================================================================

async def initiate_call():
    """Trigger call initiation when button is pressed"""
    try:
        logger.info("Initiating call request to operator")
        
        # Get device location/identifier (customize as needed)
        call_data = {
            'from': 'ECB-001',
            'location': 'Main Entrance',
            'timestamp': datetime.now().isoformat()
        }
        
        # Send call request to signaling server
        await state.sio.emit('call_request', call_data)
        logger.info("Call request sent: %s", call_data)
        
        # Start WebRTC call setup
        await start_webrtc_call()
        
    except Exception as e:
        logger.error("Error initiating call: %s", e)

# ============================================================================
# HEALTH CHECK & MONITORING
# ============================================================================

async def health_check():
    """Periodic health check of connection and call status"""
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            # Check signaling server connection
            if not state.sio.connected:
                logger.warning("Signaling server connection lost, attempting reconnect")
                try:
                    await state.sio.connect(SIGNALING_SERVER)
                except Exception as e:
                    logger.error("Reconnection failed: %s", e)
            
            # Log current state
            logger.debug(
                "Health check - Connected: %s, Call Active: %s",
                state.sio.connected,
                state.call_active
            )
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in health check: %s", e)

# ============================================================================
# MAIN APPLICATION LOOP
# ============================================================================

async def main():
    """Main async entry point"""
    logger.info("ECB Client starting...")
    
    # Setup GPIO
    setup_gpio()
    setup_button_detection()
    
    # Store event loop for button callback
    state.event_loop = asyncio.get_event_loop()
    
    try:
        # Start health check task
        health_task = asyncio.create_task(health_check())
        
        # Connect to signaling server (blocking)
        await connect_to_server()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Fatal error: %s", e)
    finally:
        # Cleanup
        logger.info("Shutting down ECB Client")
        
        # Stop call if active
        if state.call_active:
            await stop_call()
        
        # Disconnect from server
        if state.sio.connected:
            await state.sio.disconnect()
        
        # Cleanup GPIO
        cleanup_gpio()
        
        logger.info("ECB Client stopped")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error("Unhandled exception: %s", e)
        raise
