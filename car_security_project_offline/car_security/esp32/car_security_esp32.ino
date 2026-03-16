/*
 * esp32/car_security_esp32.ino
 *
 * Firmware for ESP32
 * Listens on Serial (UART0) for commands from Raspberry Pi.
 * On receiving "LOC":
 *   1. Polls GPS module (NEO-6M) via Serial2 (UART2)
 *   2. Parses NMEA $GPRMC sentence for lat/lon
 *   3. Sends SMS with location via SIM800L GSM (Serial1 / UART1)
 *
 * Wiring:
 *   RPi TX (GPIO14) → ESP32 RX0 (GPIO3)
 *   RPi RX (GPIO15) → ESP32 TX0 (GPIO1)
 *   NEO-6M TX       → ESP32 GPIO16 (RX2)
 *   NEO-6M RX       → ESP32 GPIO17 (TX2)
 *   SIM800L TX      → ESP32 GPIO4  (RX1)
 *   SIM800L RX      → ESP32 GPIO2  (TX1)
 */

#include <HardwareSerial.h>
#include <TinyGPS++.h>

// ── Pin / Serial assignments ────────────────────────────────────────────────
HardwareSerial GPSSerial(2);   // UART2: RX=16, TX=17
HardwareSerial GSMSerial(1);   // UART1: RX=4,  TX=2

TinyGPSPlus gps;

// ── Config ──────────────────────────────────────────────────────────────────
const char* OWNER_PHONE    = "+919XXXXXXXXX";  // ← replace with owner's number
const int   GPS_TIMEOUT_MS = 60000;            // 60s max GPS lock wait
const int   GSM_BAUD       = 9600;
const int   GPS_BAUD       = 9600;

// ── Setup ───────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(9600);              // UART0 ← RPi
    GPSSerial.begin(GPS_BAUD, SERIAL_8N1, 16, 17);
    GSMSerial.begin(GSM_BAUD, SERIAL_8N1, 4, 2);

    delay(1000);
    Serial.println("ESP32 ready. Waiting for command...");
    gsmInit();
}

// ── Main loop ───────────────────────────────────────────────────────────────
void loop() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        Serial.println("ACK:" + cmd);   // Send ACK back to RPi

        if (cmd == "LOC") {
            Serial.println("LOC command received. Fetching GPS...");
            handleLocCommand();
        }
    }

    // Feed GPS parser continuously
    while (GPSSerial.available()) {
        gps.encode(GPSSerial.read());
    }
}

// ── Command handler ─────────────────────────────────────────────────────────
void handleLocCommand() {
    double lat = 0.0, lon = 0.0;
    bool   gotFix = false;
    unsigned long startTime = millis();

    // Wait for valid GPS fix (up to GPS_TIMEOUT_MS)
    while (millis() - startTime < GPS_TIMEOUT_MS) {
        while (GPSSerial.available()) {
            gps.encode(GPSSerial.read());
        }
        if (gps.location.isValid() && gps.location.isUpdated()) {
            lat    = gps.location.lat();
            lon    = gps.location.lng();
            gotFix = true;
            break;
        }
        delay(500);
    }

    if (gotFix) {
        sendSMS(lat, lon);
    } else {
        Serial.println("GPS fix failed. Sending SMS without coordinates.");
        sendSMSNoFix();
    }
}

// ── SMS helpers ─────────────────────────────────────────────────────────────
void sendSMS(double lat, double lon) {
    // Build Maps link: https://maps.google.com/?q=lat,lon
    String mapsLink = "https://maps.google.com/?q="
                      + String(lat, 6) + ","
                      + String(lon, 6);

    String msg = "ALERT! Unauthorised access attempt on your car.\n"
                 "GPS Location: " + String(lat, 6)
                 + ", " + String(lon, 6)
                 + "\n" + mapsLink;

    gsmSendSMS(OWNER_PHONE, msg);
    Serial.println("SMS sent with location: " + String(lat,6)
                   + "," + String(lon,6));
}

void sendSMSNoFix() {
    String msg = "ALERT! Unauthorised access attempt on your car. "
                 "GPS fix unavailable at this time.";
    gsmSendSMS(OWNER_PHONE, msg);
}

// ── GSM (SIM800L) functions ─────────────────────────────────────────────────
void gsmInit() {
    sendAT("AT", 1000);            // Check module alive
    sendAT("AT+CMGF=1", 1000);    // Set SMS text mode
    sendAT("AT+CSCS=\"GSM\"", 1000);
    Serial.println("GSM initialized.");
}

void gsmSendSMS(const char* number, String message) {
    GSMSerial.print("AT+CMGS=\"");
    GSMSerial.print(number);
    GSMSerial.println("\"");
    delay(500);
    GSMSerial.print(message);
    delay(100);
    GSMSerial.write(26);  // Ctrl+Z to send
    delay(3000);
    Serial.println("SMS dispatch done.");
}

String sendAT(String cmd, int timeout) {
    GSMSerial.println(cmd);
    unsigned long t = millis();
    String resp = "";
    while (millis() - t < (unsigned long)timeout) {
        while (GSMSerial.available()) {
            resp += (char)GSMSerial.read();
        }
    }
    return resp;
}
