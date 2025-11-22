#!/usr/bin/env python3
"""
Visant Device Client v2.0 - Cloud-Triggered Architecture

This is a simplified device client that listens for capture commands from the cloud
and executes them. All trigger scheduling logic now lives in the cloud.

Usage:
    python -m device.main \\
        --api-url https://cloud.visant.com \\
        --device-id FLOOR1 \\
        --camera-source 0
"""

import sys
import time
import json
import base64
import argparse
import logging

# Import version number
from version import __version__ as DEVICE_VERSION
from datetime import datetime, timezone
from pathlib import Path

import requests

# Add parent directory to path to import from device module
sys.path.insert(0, str(Path(__file__).parent.parent))

from device.capture import OpenCVCamera, StubCamera
from device.light_tower import LightTower

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Visant Device Client v2.0 (Cloud-Triggered)")

    # Required arguments
    parser.add_argument("--api-url", required=True, help="Cloud API base URL (e.g., https://cloud.visant.com)")
    parser.add_argument("--device-id", required=True, help="Device identifier (e.g., FLOOR1)")

    # Camera configuration
    parser.add_argument("--camera-source", default="0", help="Camera source (0 for default webcam, path for image file, RTSP URL)")
    parser.add_argument("--camera-backend", default=None, help="OpenCV backend (dshow, msmf, etc.)")
    parser.add_argument("--camera-resolution", default=None, help="Camera resolution (e.g., 1920x1080)")
    parser.add_argument("--camera-warmup", type=int, default=2, help="Number of warmup frames to discard")
    parser.add_argument("--flip-horizontal", action="store_true", help="Flip image horizontally (mirror)")
    parser.add_argument("--flip-vertical", action="store_true", help="Flip image vertically")

    # Alarm tower configuration
    parser.add_argument("--alarm-enabled", action="store_true", help="Enable alarm light tower")
    parser.add_argument("--alarm-port", default="/dev/ttyUSB0", help="Serial port for alarm tower")
    parser.add_argument("--alarm-baud", type=int, default=9600, help="Baud rate for alarm tower")
    parser.add_argument("--alarm-beep-duration", type=float, default=3.0, help="Duration of beep in seconds for alerts")

    # Connection settings
    parser.add_argument("--upload-timeout", type=int, default=30, help="Timeout for capture upload (seconds)")
    parser.add_argument("--stream-timeout", type=int, default=70, help="Timeout for SSE stream read (seconds)")
    parser.add_argument("--reconnect-delay", type=int, default=5, help="Delay before reconnecting after error (seconds)")

    # Debug options
    parser.add_argument("--save-frames", action="store_true", help="Save captured frames locally for debugging")
    parser.add_argument("--save-frames-dir", default="debug_captures", help="Directory for saved frames")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


def setup_camera(args):
    """Initialize camera based on arguments."""
    # Check if source is a file (stub camera)
    if args.camera_source and Path(args.camera_source).is_file():
        logger.info(f"Using stub camera with image: {args.camera_source}")
        return StubCamera(sample_path=Path(args.camera_source))

    # Otherwise use OpenCV camera
    try:
        # Parse camera source (int for device index, str for RTSP URL)
        try:
            source = int(args.camera_source)
        except ValueError:
            source = args.camera_source  # RTSP URL or other string

        # Parse resolution if provided
        resolution = None
        if args.camera_resolution:
            width, height = map(int, args.camera_resolution.split('x'))
            resolution = (width, height)

        logger.info(f"Initializing OpenCV camera (source={source}, backend={args.camera_backend}, resolution={resolution})")

        camera = OpenCVCamera(
            source=source,
            backend=args.camera_backend,
            resolution=resolution,
            warmup_frames=args.camera_warmup
        )

        logger.info("Camera initialized successfully")
        return camera

    except Exception as e:
        logger.error(f"Failed to initialize camera: {e}")
        sys.exit(1)



def setup_light_tower(args) -> LightTower | None:
    """Initialize light tower if enabled."""
    if not args.alarm_enabled:
        logger.info("Alarm tower: disabled")
        return None

    try:
        tower = LightTower(port=args.alarm_port, baud=args.alarm_baud)
        logger.info(f"Alarm tower: enabled (port={args.alarm_port}, baud={args.alarm_baud})")
        # Set initial state to normal (green)
        tower.trigger_normal()
        return tower
    except Exception as e:
        logger.error(f"Failed to initialize alarm tower: {e}")
        return None


def encode_frame_base64(frame) -> str:
    """Encode frame as base64 JPEG."""
    import cv2
    import numpy as np
    from device.capture import Frame

    # Handle Frame objects (from StubCamera)
    if isinstance(frame, Frame):
        # Frame already has image bytes, just encode to base64
        image_base64 = base64.b64encode(frame.data).decode('utf-8')
        return image_base64

    # Handle numpy arrays (from OpenCVCamera)
    # Encode as JPEG
    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        raise ValueError("Failed to encode frame as JPEG")

    # Convert to base64
    image_bytes = buffer.tobytes()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    return image_base64


def save_frame_debug(frame, trigger_id: str, save_dir: str):
    """Save frame to debug directory."""
    import cv2
    from device.capture import Frame

    debug_dir = Path(save_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{trigger_id}.jpg"
    filepath = debug_dir / filename

    # Handle Frame objects (from StubCamera)
    if isinstance(frame, Frame):
        filepath.write_bytes(frame.data)
    else:
        # Handle numpy arrays (from OpenCVCamera)
        cv2.imwrite(str(filepath), frame)

    logger.debug(f"Saved debug frame: {filepath}")


def handle_capture_command(camera, command: dict, args):
    """
    Execute a capture command from the cloud.

    Args:
        camera: Camera instance
        command: Command dict with {cmd, trigger_id, type}
        args: Command line arguments
    """
    trigger_id = command.get("trigger_id", "unknown")
    trigger_type = command.get("type", "unknown")

    logger.info(f"[{trigger_id}] Executing capture command (type: {trigger_type})")

    try:
        # Capture frame with flip settings from config
        flip_h = getattr(args, 'flip_horizontal', False)
        flip_v = getattr(args, 'flip_vertical', False)
        frame = camera.capture(flip_horizontal=flip_h, flip_vertical=flip_v)

        # Save debug frame if requested
        if args.save_frames:
            save_frame_debug(frame, trigger_id, args.save_frames_dir)

        # Encode as base64
        image_base64 = encode_frame_base64(frame)

        # Upload to cloud
        payload = {
            "device_id": args.device_id,
            "trigger_id": trigger_id,
            "image_base64": image_base64,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "trigger_label": f"{trigger_type}_{trigger_id}",
            "metadata": {
                "device_version": "2.0.0",
                "trigger_type": trigger_type
            }
        }

        upload_url = f"{args.api_url}/v1/captures"

        logger.debug(f"[{trigger_id}] Uploading capture (size: {len(image_base64)} bytes)")

        response = requests.post(
            upload_url,
            json=payload,
            timeout=args.upload_timeout
        )

        response.raise_for_status()

        result = response.json()
        record_id = result.get("record_id", "unknown")

        logger.info(f"[{trigger_id}] ✓ Capture uploaded successfully (record_id: {record_id})")

    except Exception as e:
        logger.error(f"[{trigger_id}] ✗ Capture failed: {e}")


def handle_config_update(camera, config: dict, args):
    """
    Handle configuration update from cloud.

    Args:
        camera: Current camera instance
        config: Configuration dict from cloud (e.g., {"camera": {"resolution_width": 1920, "resolution_height": 1080}})
        args: Command line arguments

    Returns:
        Camera instance (may be new if reinitialized)
    """
    camera_config = config.get("camera", {})

    if not camera_config:
        logger.debug("No camera config in update, ignoring")
        return camera

    new_width = camera_config.get("resolution_width")
    new_height = camera_config.get("resolution_height")

    # Update flip settings (always apply, even if resolution doesn't change)
    args.flip_horizontal = camera_config.get("flip_horizontal", False)
    args.flip_vertical = camera_config.get("flip_vertical", False)
    if args.flip_horizontal or args.flip_vertical:
        logger.info(f"Flip settings updated: horizontal={args.flip_horizontal}, vertical={args.flip_vertical}")

    if new_width and new_height:
        logger.info(f"Received camera config update: resolution {new_width}x{new_height}")

        # Update args so future camera reinitializations use new resolution
        args.camera_resolution = f"{new_width}x{new_height}"

        # Reinitialize camera with new resolution
        try:
            logger.info("Reinitializing camera with new resolution...")
            camera.release()
            camera = setup_camera(args)
            logger.info(f"✓ Camera reinitialized with resolution {new_width}x{new_height}")
        except Exception as e:
            logger.error(f"✗ Failed to reinitialize camera: {e}")
            # Try to recover with original camera
            try:
                camera = setup_camera(args)
            except Exception as recovery_error:
                logger.error(f"✗ Camera recovery failed: {recovery_error}")

    elif new_width is None and new_height is None:
        # Reset to camera default
        logger.info("Received camera config update: reset to camera default resolution")
        args.camera_resolution = None

        try:
            logger.info("Reinitializing camera with default resolution...")
            camera.release()
            camera = setup_camera(args)
            logger.info("✓ Camera reinitialized with default resolution")
        except Exception as e:
            logger.error(f"✗ Failed to reinitialize camera: {e}")

    return camera



def handle_alarm_command(light_tower: LightTower | None, command: dict, args):
    """
    Handle alarm command from cloud based on AI evaluation state.

    Args:
        light_tower: LightTower instance (or None if disabled)
        command: Command dict with {cmd, state, record_id}
        args: Command line arguments
    """
    if light_tower is None:
        logger.debug("Alarm command received but tower is disabled")
        return

    state = command.get("state", "normal")
    record_id = command.get("record_id", "unknown")

    logger.info(f"[{record_id}] Alarm command received: state={state}")

    try:
        # Handle alarm based on AI evaluation state
        # 'alert' -> red flash + beep (timed)
        # 'normal' or 'uncertain' -> green on
        light_tower.handle_alarm_state(state, beep_duration=args.alarm_beep_duration)
    except Exception as e:
        logger.error(f"[{record_id}] Alarm command failed: {e}")


def main():
    """Main entry point for cloud-triggered device client."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Visant Device Client v2.0 - Cloud-Triggered Architecture")
    logger.info("=" * 60)
    logger.info(f"Device ID: {args.device_id}")
    logger.info(f"API URL: {args.api_url}")
    logger.info(f"Camera: {args.camera_source}")
    logger.info("=" * 60)

    # Setup camera
    camera = setup_camera(args)

    # Setup alarm tower
    light_tower = setup_light_tower(args)

    # Connect to command stream with device version
    stream_url = f"{args.api_url}/v1/devices/{args.device_id}/commands?device_version={DEVICE_VERSION}"

    logger.info(f"Connecting to command stream: {stream_url} (version: {DEVICE_VERSION})")

    while True:
        try:
            # Connect to SSE stream
            response = requests.get(
                stream_url,
                stream=True,
                timeout=args.stream_timeout
            )

            response.raise_for_status()

            logger.info("✓ Connected to command stream")

            # Process SSE events
            for line in response.iter_lines():
                if not line:
                    continue

                # Parse SSE event
                line = line.decode('utf-8')

                if line.startswith('data:'):
                    data = line[5:].strip()  # Remove "data:" prefix

                    try:
                        event = json.loads(data)

                        # Handle different event types
                        if event.get("event") == "connected":
                            logger.info(f"✓ Connection confirmed by server")

                        elif event.get("event") == "ping":
                            logger.debug("← Keepalive ping received")

                        elif event.get("cmd") == "capture":
                            # Execute capture command
                            handle_capture_command(camera, event, args)

                        elif event.get("cmd") == "update_config":
                            # Handle config update from cloud
                            config = event.get("config", {})
                            camera = handle_config_update(camera, config, args)

                        elif event.get("cmd") == "alarm":
                            # Handle alarm command from cloud
                            handle_alarm_command(light_tower, event, args)

                        else:
                            logger.warning(f"Unknown event: {event}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse event JSON: {e}")

        except KeyboardInterrupt:
            logger.info("\nShutdown requested by user")
            break

        except requests.exceptions.Timeout:
            logger.warning("Stream timeout (expected for keepalive), reconnecting...")
            time.sleep(1)

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            logger.info(f"Reconnecting in {args.reconnect_delay} seconds...")
            time.sleep(args.reconnect_delay)

        except requests.exceptions.ChunkedEncodingError as e:
            logger.warning(f"Stream connection reset, reconnecting...")
            time.sleep(1)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            logger.info(f"Reconnecting in {args.reconnect_delay} seconds...")
            time.sleep(args.reconnect_delay)

    # Cleanup: turn off alarm tower on exit
    if light_tower:
        logger.info("Turning off alarm tower...")
        light_tower.all_off()

    logger.info("Device client stopped")


if __name__ == "__main__":
    main()
