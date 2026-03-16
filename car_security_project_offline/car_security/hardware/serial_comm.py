"""
hardware/serial_comm.py — Stage 4
Sends commands from Raspberry Pi to ESP32 over UART serial.
Connects via /dev/ttyS0 (GPIO14=TX, GPIO15=RX on RPi4).
"""

import serial
import logging
import time

logger = logging.getLogger("serial_comm")


class SerialComm:
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        self._ser = None
        self._connect()

    def _connect(self):
        try:
            self._ser = serial.Serial(
                port        = self.port,
                baudrate    = self.baud,
                timeout     = 2,
                bytesize    = serial.EIGHTBITS,
                parity      = serial.PARITY_NONE,
                stopbits    = serial.STOPBITS_ONE,
            )
            time.sleep(0.5)  # Allow ESP32 to boot/reset
            logger.info("Serial opened: %s @ %d baud", self.port, self.baud)
        except serial.SerialException as e:
            logger.error("Failed to open serial port %s: %s", self.port, e)
            self._ser = None

    def send_command(self, cmd: str):
        """
        Send a newline-terminated command string to the ESP32.
        E.g. send_command("LOC") → ESP32 receives "LOC\n"
        """
        if self._ser is None or not self._ser.is_open:
            logger.error("Serial not open. Cannot send command: %s", cmd)
            return

        message = f"{cmd}\n".encode("utf-8")
        self._ser.write(message)
        self._ser.flush()
        logger.info("Sent serial command: %s", cmd.strip())

        # Optional: wait for ESP32 ACK
        try:
            ack = self._ser.readline().decode("utf-8").strip()
            logger.info("ESP32 ACK: %s", ack)
        except Exception:
            pass

    def close(self):
        if self._ser and self._ser.is_open:
            self._ser.close()
            logger.info("Serial port closed.")
