#!/usr/bin/env python3
"""
ECB Client - Diagnostics & Testing Utility
Run this to verify all components before starting the full client
"""

import subprocess
import sys
import socket
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-8s %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(text):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_python_version():
    """Verify Python version"""
    print_header("Python Environment")
    version = sys.version_info
    logger.info(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        logger.error("Python 3.9+ required")
        return False
    logger.info("✓ Python version OK")
    return True

def check_dependencies():
    """Verify all Python packages are installed"""
    print_header("Python Dependencies")
    
    required = [
        'aiortc',
        'socketio',
        'RPi.GPIO',
        'av',
        'cv2'  # opencv
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            logger.info(f"✓ {package}")
        except ImportError as e:
            logger.error(f"✗ {package} - {e}")
            missing.append(package)
    
    if missing:
        logger.error(f"Install missing packages: pip install {' '.join(missing)}")
        return False
    return True

def check_system_packages():
    """Verify required system packages"""
    print_header("System Packages")
    
    packages = [
        ('gstreamer1.0', 'gst-inspect-1.0'),
        ('libopus', 'libopus-dev'),
        ('libvpx', 'libvpx-dev'),
    ]
    
    all_ok = True
    for package, cmd_to_check in packages:
        result = subprocess.run(
            f"which {cmd_to_check} || dpkg -l | grep {package}",
            shell=True,
            capture_output=True
        )
        if result.returncode == 0:
            logger.info(f"✓ {package}")
        else:
            logger.error(f"✗ {package} not found")
            all_ok = False
    
    return all_ok

def check_gpio():
    """Test GPIO setup"""
    print_header("GPIO Configuration")
    
    try:
        import RPi.GPIO as GPIO
        logger.info("✓ RPi.GPIO imported")
        
        # Check if we can access GPIO (might fail in container or non-Pi)
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            state = GPIO.input(17)
            logger.info(f"✓ GPIO 17 accessible - Current state: {state}")
            GPIO.cleanup()
            return True
        except Exception as e:
            logger.warning(f"⚠ GPIO 17 not accessible: {e}")
            logger.info("  (Normal if running in container or over SSH)")
            return True  # Not a fatal error
    except ImportError:
        logger.error("✗ RPi.GPIO not installed")
        return False

def check_audio_devices():
    """List available audio devices"""
    print_header("Audio Devices")
    
    try:
        result = subprocess.run(
            "arecord -l",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("Available recording devices:")
            for line in result.stdout.split('\n')[1:]:
                if line.strip():
                    logger.info(f"  {line}")
            return True
        else:
            logger.warning("Could not list audio devices")
            return True
    except Exception as e:
        logger.error(f"Error checking audio: {e}")
        return False

def check_camera_rtsp(url):
    """Test RTSP camera connectivity"""
    print_header("Camera RTSP Stream")
    
    try:
        # Try with ffprobe
        result = subprocess.run(
            f'ffprobe -v quiet -print_format json -show_streams "{url}" 2>&1',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'codec_type' in result.stdout:
            logger.info(f"✓ RTSP stream accessible: {url}")
            return True
        else:
            logger.warning(f"⚠ Could not verify RTSP stream")
            logger.info(f"  Try: ffprobe {url}")
            logger.info(f"  Or: gst-discoverer-1.0 {url}")
            return True  # Not fatal, camera might be offline
    except subprocess.TimeoutExpired:
        logger.warning("⚠ RTSP stream check timed out (camera may be unreachable)")
        return True
    except Exception as e:
        logger.error(f"Error checking RTSP: {e}")
        return False

def check_network_connectivity(host, port):
    """Test connectivity to signaling server"""
    print_header("Network Connectivity")
    
    logger.info(f"Testing connection to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info(f"✓ Can reach {host}:{port}")
            return True
        else:
            logger.error(f"✗ Cannot reach {host}:{port}")
            logger.info(f"  Verify server is running and accessible")
            logger.info(f"  Try: telnet {host} {port}")
            return False
    except socket.gaierror as e:
        logger.error(f"✗ Cannot resolve hostname {host}: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Network error: {e}")
        return False

def check_config_file():
    """Verify config.py is properly configured"""
    print_header("Configuration File")
    
    try:
        from config import SIGNALING_SERVER, CAMERA_RTSP_URL
        
        if SIGNALING_SERVER == 'http://YOUR_SERVER_IP:3000':
            logger.error("✗ SIGNALING_SERVER not configured in config.py")
            return False
        logger.info(f"✓ Server configured: {SIGNALING_SERVER}")
        
        if CAMERA_RTSP_URL == 'rtsp://192.168.1.100:554/stream':
            logger.warning("⚠ CAMERA_RTSP_URL using default, verify it's correct")
            logger.info(f"  {CAMERA_RTSP_URL}")
        else:
            logger.info(f"✓ Camera configured: {CAMERA_RTSP_URL}")
        
        return True
    except ImportError:
        logger.error("✗ config.py not found")
        return False

def test_socketio_connection():
    """Test Socket.io connection to server"""
    print_header("Socket.io Connection Test")
    
    try:
        import socketio
        logger.info("✓ Socket.io library available")
        
        from config import SIGNALING_SERVER
        
        if SIGNALING_SERVER == 'http://YOUR_SERVER_IP:3000':
            logger.warning("⚠ Cannot test - server not configured")
            return True
        
        logger.info(f"Attempting connection to {SIGNALING_SERVER}...")
        
        # This is a simple sync test (real client uses async)
        # Just checking if server is reachable
        import asyncio
        import time
        
        async def test_connection():
            sio = socketio.AsyncClient()
            try:
                await asyncio.wait_for(
                    sio.connect(SIGNALING_SERVER),
                    timeout=5
                )
                await sio.disconnect()
                logger.info("✓ Socket.io connection successful")
                return True
            except asyncio.TimeoutError:
                logger.error("✗ Connection timeout")
                return False
            except Exception as e:
                logger.error(f"✗ Connection failed: {e}")
                return False
        
        result = asyncio.run(test_connection())
        return result
        
    except Exception as e:
        logger.warning(f"⚠ Could not test Socket.io: {e}")
        return True

def run_full_diagnostics():
    """Run all diagnostic checks"""
    print_header("ECB CLIENT DIAGNOSTICS")
    
    checks = [
        ("Python Version", check_python_version),
        ("Python Dependencies", check_dependencies),
        ("System Packages", check_system_packages),
        ("GPIO Setup", check_gpio),
        ("Audio Devices", check_audio_devices),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"Error running {name}: {e}")
            results[name] = False
    
    # Config checks
    try:
        from config import SIGNALING_SERVER, CAMERA_RTSP_URL
        results["Configuration"] = check_config_file()
        results["RTSP Stream"] = check_camera_rtsp(CAMERA_RTSP_URL)
        results["Network"] = check_network_connectivity(
            SIGNALING_SERVER.split('//')[1].split(':')[0],
            int(SIGNALING_SERVER.split(':')[-1])
        )
        results["Socket.io"] = test_socketio_connection()
    except Exception as e:
        logger.error(f"Error in advanced checks: {e}")
    
    # Print summary
    print_header("DIAGNOSTICS SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} {name}")
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("\n✓ All checks passed! Ready to start ECB client.")
        return True
    else:
        logger.error(f"\n✗ {total - passed} check(s) failed. Review configuration.")
        return False

if __name__ == '__main__':
    success = run_full_diagnostics()
    sys.exit(0 if success else 1)
