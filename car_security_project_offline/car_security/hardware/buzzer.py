"""
hardware/buzzer.py — Stage 4
Controls the piezo buzzer on a GPIO pin.
"""

import time
import threading
import logging

logger = logging.getLogger("buzzer")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available — buzzer running in SIMULATION mode.")


class BuzzerController:
    def __init__(self, pin: int):
        self.pin    = pin
        self._timer = None

        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.LOW)
            logger.info("Buzzer initialized on GPIO pin %d (BCM).", pin)
        else:
            logger.info("[SIM] Buzzer initialized on pin %d.", pin)

    def activate(self, duration: int = 30):
        """
        Turn buzzer ON and schedule auto-off after `duration` seconds.
        Non-blocking — uses a background timer thread.
        """
        self._set(True)
        # Cancel any existing timer
        if self._timer and self._timer.is_alive():
            self._timer.cancel()
        self._timer = threading.Timer(duration, self._set, args=[False])
        self._timer.start()
        logger.info("Buzzer ON for %ds", duration)

    def deactivate(self):
        self._set(False)
        if self._timer:
            self._timer.cancel()

    def _set(self, state: bool):
        if GPIO_AVAILABLE:
            GPIO.output(self.pin, GPIO.HIGH if state else GPIO.LOW)
        else:
            logger.info("[SIM] Buzzer %s", "ON" if state else "OFF")

    def cleanup(self):
        self.deactivate()
        if GPIO_AVAILABLE:
            GPIO.cleanup(self.pin)
