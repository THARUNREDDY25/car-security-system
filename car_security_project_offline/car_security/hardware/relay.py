"""
hardware/relay.py — Stage 5
Controls the 5V relay module connected to the car ignition line.
Uses RPi.GPIO for pin control.
"""

import time
import logging

logger = logging.getLogger("relay")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available — relay running in SIMULATION mode.")


class RelayController:
    def __init__(self, pin: int):
        self.pin      = pin
        self.unlocked = False

        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
            logger.info("Relay initialized on GPIO pin %d (BCM).", pin)
        else:
            logger.info("[SIM] Relay initialized on pin %d.", pin)

    def unlock(self, duration: int = 5):
        """
        Pull relay HIGH (close the ignition circuit) for `duration` seconds,
        then return to LOW (open circuit).
        """
        logger.info("Relay → UNLOCKED for %ds", duration)
        self.unlocked = True

        if GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.pin, GPIO.LOW)
        else:
            logger.info("[SIM] Relay HIGH → wait %ds → LOW", duration)
            time.sleep(duration)

        self.unlocked = False
        logger.info("Relay → LOCKED (circuit open)")

    def cleanup(self):
        if GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.LOW)
            GPIO.cleanup(self.pin)
            logger.info("Relay GPIO cleaned up.")
