#!/usr/bin/env python3
"""
Light Tower Controller for Alarm Signaling

Controls a serial-connected light tower to provide visual and audio alerts
based on AI evaluation results.
"""

import serial
import time
import threading
import logging

logger = logging.getLogger(__name__)


class LightTower:
    """Controller for serial-connected light tower with RGB lights and buzzer."""

    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 9600):
        self.port = port
        self.baud = baud
        self._beep_timer: threading.Timer | None = None

        # Verify port is accessible at startup
        try:
            with serial.Serial(self.port, self.baud, timeout=1) as ser:
                pass  # Just test connection
            logger.info(f"Light tower connected on {port}")
        except serial.SerialException as e:
            raise RuntimeError(f"Light tower port {port} not available: {e}")

        self.commands = {
            "red_on":            bytes.fromhex("A0 01 01 A2"),
            "red_flash":         bytes.fromhex("A0 01 01 B3"),
            "red_off":           bytes.fromhex("A0 01 00 A1"),

            "yellow_on":         bytes.fromhex("A0 03 01 A4"),
            "yellow_flash":      bytes.fromhex("A0 03 01 B5"),
            "yellow_off":        bytes.fromhex("A0 03 00 A3"),

            "green_on":          bytes.fromhex("A0 02 01 A3"),
            "green_flash":       bytes.fromhex("A0 02 01 B4"),
            "green_off":         bytes.fromhex("A0 02 00 A2"),

            "beep_loud":         bytes.fromhex("A0 04 01 A5"),
            "beep_loud_flash":   bytes.fromhex("A0 04 01 B6"),
            "beep_on":           bytes.fromhex("A0 04 01 C7"),
            "beep_intermit":     bytes.fromhex("A0 04 01 D8"),
            "beep_off":          bytes.fromhex("A0 04 00 A4"),
        }

    def send(self, name: str) -> bool:
        """Send a command to the light tower.

        Args:
            name: Command name (e.g., 'red_on', 'beep_intermit')

        Returns:
            True if command was sent successfully, False otherwise
        """
        if name not in self.commands:
            logger.error(f"Unknown light tower command: {name}")
            return False

        data = self.commands[name]
        return self._send_raw(data, name)

    def _send_raw(self, data: bytes, name: str = "") -> bool:
        """Send raw bytes to the light tower via serial."""
        try:
            with serial.Serial(self.port, self.baud, timeout=1) as ser:
                ser.write(data)
            logger.debug(f"Light tower command sent: {name}")
            return True
        except Exception as e:
            logger.error(f"Light tower serial error: {e}")
            return False

    def all_off(self) -> None:
        """Turn off all lights (including flash modes) and buzzer."""
        self._cancel_beep_timer()
        for cmd in ["red_off", "yellow_off", "green_off", "beep_off"]:
            self._send_raw(self.commands[cmd], cmd)
            time.sleep(0.05)
        logger.info("Light tower: all off")

    def _cancel_beep_timer(self) -> None:
        """Cancel any pending beep-off timer."""
        if self._beep_timer is not None:
            self._beep_timer.cancel()
            self._beep_timer = None

    def trigger_alert(self, beep_duration: float = 3.0) -> None:
        """Trigger alert state: red light on (solid) + beep (timed).

        Args:
            beep_duration: Seconds before beep automatically turns off
        """
        self._cancel_beep_timer()

        # Turn off other lights first
        self.send("green_off")
        time.sleep(0.05)

        # Start red light (solid) and intermittent beep
        self.send("red_on")
        time.sleep(0.05)
        self.send("beep_intermit")

        # Schedule beep to turn off after duration
        self._beep_timer = threading.Timer(beep_duration, self._beep_off_callback)
        self._beep_timer.daemon = True
        self._beep_timer.start()

        logger.info(f"Light tower: ALERT (beep will stop after {beep_duration}s)")

    def _beep_off_callback(self) -> None:
        """Callback to turn off beep after timer expires."""
        self.send("beep_off")
        self._beep_timer = None
        logger.debug("Light tower: beep auto-off")

    def trigger_normal(self) -> None:
        """Trigger normal state: all off, then green light on."""
        self._cancel_beep_timer()

        # Turn everything off first
        time.sleep(0.1)
        self.all_off()
        time.sleep(0.1)

        # Turn on green
        self.send("green_on")

        logger.info("Light tower: NORMAL (green)")

    def handle_alarm_state(self, state: str, beep_duration: float = 3.0) -> None:
        """Handle alarm based on AI evaluation state.

        Args:
            state: AI evaluation state ('alert', 'normal', 'uncertain')
            beep_duration: Seconds before beep turns off for alerts
        """
        if state == "alert":
            self.trigger_alert(beep_duration)
        else:
            # 'normal' and 'uncertain' both show green
            self.trigger_normal()


# CLI interface for testing
if __name__ == "__main__":
    import sys

    def print_usage():
        print("Usage:")
        print("  python light_tower.py <command>\n")
        print("Commands:")
        print("  red_on, red_flash, red_off")
        print("  yellow_on, yellow_flash, yellow_off")
        print("  green_on, green_flash, green_off")
        print("  beep_loud, beep_loud_flash, beep_on, beep_intermit, beep_off")
        print("  all_off")
        print("  alert    - Trigger alert state (red flash + beep)")
        print("  normal   - Trigger normal state (green on)")
        print("")
        print("Example:")
        print("  python light_tower.py red_on")

    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    logging.basicConfig(level=logging.DEBUG)
    command = sys.argv[1].strip()
    tower = LightTower()

    if command == "all_off":
        tower.all_off()
    elif command == "alert":
        tower.trigger_alert()
        # Keep running for beep timer
        import time
        time.sleep(4)
    elif command == "normal":
        tower.trigger_normal()
    elif command in tower.commands:
        tower.send(command)
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
