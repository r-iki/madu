#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <Wire.h>
#include "SparkFun_AS7265X.h" // Library untuk sensor AS7265x
#include <time.h> // Library untuk waktu
#include <ArduinoJson.h>

// Konfigurasi WiFi - akan diisi dari UI
String ssid = ""; 
String password = "";
const char* websocket_server = "wss://madu.software/ws/sensor/";

const char* root_ca = \
"-----BEGIN CERTIFICATE-----\n"
"MIICnzCCAiWgAwIBAgIQf/MZd5csIkp2FV0TttaF4zAKBggqhkjOPQQDAzBHMQsw\n"
"CQYDVQQGEwJVUzEiMCAGA1UEChMZR29vZ2xlIFRydXN0IFNlcnZpY2VzIExMQzEU\n"
"MBIGA1UEAxMLR1RTIFJvb3QgUjQwHhcNMjMxMjEzMDkwMDAwWhcNMjkwMjIwMTQw\n"
"MDAwWjA7MQswCQYDVQQGEwJVUzEeMBwGA1UEChMVR29vZ2xlIFRydXN0IFNlcnZp\n"
"Y2VzMQwwCgYDVQQDEwNXRTEwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAARvzTr+\n"
"Z1dHTCEDhUDCR127WEcPQMFcF4XGGTfn1XzthkubgdnXGhOlCgP4mMTG6J7/EFmP\n"
"LCaY9eYmJbsPAvpWo4H+MIH7MA4GA1UdDwEB/wQEAwIBhjAdBgNVHSUEFjAUBggr\n"
"BgEFBQcDAQYIKwYBBQUHAwIwEgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHQ4EFgQU\n"
"kHeSNWfE/6jMqeZ72YB5e8yT+TgwHwYDVR0jBBgwFoAUgEzW63T/STaj1dj8tT7F\n"
"avCUHYwwNAYIKwYBBQUHAQEEKDAmMCQGCCsGAQUFBzAChhhodHRwOi8vaS5wa2ku\n"
"Z29vZy9yNC5jcnQwKwYDVR0fBCQwIjAgoB6gHIYaaHR0cDovL2MucGtpLmdvb2cv\n"
"ci9yNC5jcmwwEwYDVR0gBAwwCjAIBgZngQwBAgEwCgYIKoZIzj0EAwMDaAAwZQIx\n"
"AOcCq1HW90OVznX+0RGU1cxAQXomvtgM8zItPZCuFQ8jSBJSjz5keROv9aYsAm5V\n"
"sQIwJonMaAFi54mrfhfoFNZEfuNMSQ6/bIBiNLiyoX46FohQvKeIoJ99cx7sUkFN\n"
"7uJW\n"
"-----END CERTIFICATE-----\n";

const char* ntpServer = "pool.ntp.org"; // Server NTP
const long gmtOffset_sec = 7 * 3600;    // Offset GMT untuk zona waktu (GMT+7)
const int daylightOffset_sec = 0;      // Tidak ada daylight saving time

using namespace websockets;
WebsocketsClient client;
AS7265X sensor; // Instance sensor AS7265x

// Variabel konfigurasi
String deviceName = "setup"; // Nama perangkat
int delayTime = 2000;   // Delay time (ms)
int duration = 10000;   // Duration (ms)
int iterations = 1;     // Jumlah iterasi pengukuran
bool dataSent = false;  // Flag untuk menandai apakah data sudah terkirim
bool webSocketConnected = false; // Status koneksi WebSocket

// Status variable untuk UI
bool isConnected = false;
String ipAddress = "";
int signalStrength = 0;
bool isMeasuring = false;

// Buffer untuk perintah
String commandBuffer = "";
bool newCommand = false;

void setup() {
    Serial.begin(115200);
    Serial.println("=== ESP32 AS7265X Controller ===");
    Serial.println("Ready to receive commands");
    
    Wire.begin();

    // Inisialisasi sensor AS7265x
    if (!sensor.begin()) {
        Serial.println("AS7265x sensor not detected. Check wiring.");
    } else {
        Serial.println("AS7265x sensor initialized!");
        sensor.disableIndicator(); // Matikan LED indikator biru
    }

    // Tunggu perintah dari serial atau via WebSocket
    Serial.println("Waiting for configuration...");
    Serial.println("Type 'help' for command list");
}

void loop() {
    // Cek untuk perintah dari serial
    checkSerialCommands();
    
    // Jika ada perintah baru, proses
    if (newCommand) {
        processCommand(commandBuffer);
        commandBuffer = "";
        newCommand = false;
    }
    
    // Jika terhubung ke WiFi, jaga koneksi WebSocket
    if (WiFi.status() == WL_CONNECTED) {
        maintainWebSocketConnection();
    }
    
    // Nonaktifkan untuk sementara, akan diaktifkan oleh perintah start
    // runMeasurementCycle();
    
    delay(100); // Tunggu sebentar untuk mengurangi penggunaan CPU
}

void checkSerialCommands() {
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        
        // Tampilkan input ke monitor serial untuk debugging
        Serial.print("Command received: ");
        Serial.println(input);
        
        commandBuffer = input;
        newCommand = true;
    }
}

void processCommand(String command) {
    // Perintah dasar
    if (command == "help") {
        printHelp();
    }
    else if (command == "status") {
        printStatus();
    }
    else if (command == "get_info") {
        sendStatusInfo();
    }
    // Perintah untuk koneksi
    else if (command.startsWith("set_wifi:")) {
        String params = command.substring(9);
        int commaIndex = params.indexOf(',');
        if (commaIndex > 0) {
            ssid = params.substring(0, commaIndex);
            password = params.substring(commaIndex + 1);
            connectWiFi();
        } else {
            Serial.println("Invalid WiFi format. Use: set_wifi:SSID,PASSWORD");
        }
    }
    // Perintah untuk konfigurasi
    else if (command.startsWith("set_config:")) {
        String params = command.substring(11);
        parseConfigCommand(params);
    }
    // Perintah untuk pengukuran
    else if (command == "start") {
        startMeasurement();
    }
    // Perintah untuk sensor
    else if (command.startsWith("set_integration_time:")) {
        String value = command.substring(20);
        setIntegrationTime(value.toInt());
    }
    else if (command.startsWith("set_gain:")) {
        String value = command.substring(9);
        setGain(value.toFloat());
    }
    else if (command.startsWith("set_mode:")) {
        String value = command.substring(9);
        setMode(value.toInt());
    }
    else if (command.startsWith("set_led:")) {
        String params = command.substring(8);
        parseLEDCommand(params);
    }
    else {
        Serial.println("Unknown command. Type 'help' for command list.");
    }
}

void printHelp() {
    Serial.println("=== Available Commands ===");
    Serial.println("help - Display this help message");
    Serial.println("status - Show current device status");
    Serial.println("get_info - Send status info to web UI");
    Serial.println("set_wifi:SSID,PASSWORD - Configure WiFi connection");
    Serial.println("set_config:NAME,DELAY,DURATION,ITERATIONS - Configure measurement settings");
    Serial.println("start - Start measurement cycle");
    Serial.println("set_integration_time:VALUE - Set sensor integration time (ms)");
    Serial.println("set_gain:VALUE - Set sensor gain (1, 3.7, 16, 64)");
    Serial.println("set_mode:VALUE - Set sensor mode (0-4)");
    Serial.println("set_led:TYPE,STATE,BRIGHTNESS - Configure LED (TYPE=indicator/bulb, STATE=on/off, BRIGHTNESS=0-100)");
}

void printStatus() {
    Serial.println("=== Device Status ===");
    Serial.print("Device Name: ");
    Serial.println(deviceName);
    Serial.print("WiFi Status: ");
    Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
    if (WiFi.status() == WL_CONNECTED) {
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.print("Signal Strength: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
    }
    Serial.print("WebSocket Status: ");
    Serial.println(webSocketConnected ? "Connected" : "Disconnected");
    Serial.print("Delay Time: ");
    Serial.print(delayTime);
    Serial.println(" ms");
    Serial.print("Duration: ");
    Serial.print(duration);
    Serial.println(" ms");
    Serial.print("Iterations: ");
    Serial.println(iterations);
    Serial.print("Measuring: ");
    Serial.println(isMeasuring ? "Yes" : "No");
}

void sendStatusInfo() {
    // Create a JSON object with status information
    DynamicJsonDocument statusDoc(256);
    statusDoc["ip"] = WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : "Not connected";
    statusDoc["signal"] = WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0;
    statusDoc["device_name"] = deviceName;
    statusDoc["wifi_connected"] = WiFi.status() == WL_CONNECTED;
    statusDoc["websocket_connected"] = webSocketConnected;
    statusDoc["measuring"] = isMeasuring;
    
    String statusJson;
    serializeJson(statusDoc, statusJson);
    
    // Send to serial with STATUS prefix for UI to recognize
    Serial.print("STATUS:");
    Serial.println(statusJson);
}

void connectWiFi() {
    if (ssid.length() == 0) {
        Serial.println("WiFi SSID not configured. Use set_wifi:SSID,PASSWORD");
        return;
    }

    Serial.print("Connecting to WiFi: ");
    Serial.println(ssid);
    
    WiFi.begin(ssid.c_str(), password.c_str());
    
    // Wait up to 20 seconds for connection
    int timeout = 20;
    while (WiFi.status() != WL_CONNECTED && timeout > 0) {
        delay(1000);
        Serial.print(".");
        timeout--;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
        Serial.print("Signal strength: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
        
        // Sinkronisasi waktu dengan NTP server
        configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
        Serial.println("Synchronizing time...");
        struct tm timeinfo;
        if (!getLocalTime(&timeinfo)) {
            Serial.println("Failed to obtain time");
        } else {
            Serial.println("Time synchronized!");
        }
        
        // Connect to WebSocket server
        connectWebSocket();
        
        // Update status variables
        ipAddress = WiFi.localIP().toString();
        signalStrength = WiFi.RSSI();
        isConnected = true;
        
        // Send status update
        sendStatusInfo();
    } else {
        Serial.println("\nWiFi connection failed!");
        isConnected = false;
    }
}

void connectWebSocket() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Cannot connect to WebSocket: WiFi not connected");
        webSocketConnected = false;
        return;
    }

    Serial.println("Connecting to WebSocket server...");
    client.setCACert(root_ca);
    
    if (client.connect(websocket_server)) {
        Serial.println("Connected to WebSocket server!");
        client.onMessage([](WebsocketsMessage message) {
            Serial.println("Received from server: " + message.data());
            processWebSocketMessage(message.data());
        });
        webSocketConnected = true;
    } else {
        Serial.println("WebSocket connection failed!");
        webSocketConnected = false;
    }
}

void processWebSocketMessage(String message) {
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, message);
    
    if (error) {
        Serial.print("Failed to parse JSON: ");
        Serial.println(error.c_str());
        return;
    }
    
    // Check if this is a command from the UI
    if (doc.containsKey("command")) {
        String command = doc["command"].as<String>();
        
        // Process commands from WebSocket
        commandBuffer = command;
        if (doc.containsKey("params")) {
            commandBuffer += ":" + doc["params"].as<String>();
        }
        newCommand = true;
    }
    
    // Check if this is a confirmation message from our data send
    if (doc.containsKey("status")) {
        String status = doc["status"].as<String>();
        if (status == "success") {
            dataSent = true;
            Serial.println("Data successfully received by server!");
        }
    }
}

void maintainWebSocketConnection() {
    if (webSocketConnected) {
        // Keep the connection alive with poll
        client.poll();
    } else if (WiFi.status() == WL_CONNECTED) {
        // Try to reconnect if disconnected but WiFi is available
        static unsigned long lastReconnectAttempt = 0;
        unsigned long now = millis();
        
        if (now - lastReconnectAttempt > 30000) { // Try every 30 seconds
            lastReconnectAttempt = now;
            connectWebSocket();
        }
    }
}

void parseConfigCommand(String params) {
    // Format: NAME,DELAY,DURATION,ITERATIONS
    int firstComma = params.indexOf(',');
    int secondComma = params.indexOf(',', firstComma + 1);
    int thirdComma = params.indexOf(',', secondComma + 1);
    
    if (firstComma > 0 && secondComma > 0 && thirdComma > 0) {
        deviceName = params.substring(0, firstComma);
        delayTime = params.substring(firstComma + 1, secondComma).toInt();
        duration = params.substring(secondComma + 1, thirdComma).toInt();
        iterations = params.substring(thirdComma + 1).toInt();
        
        Serial.println("Configuration updated:");
        Serial.print("Device Name: ");
        Serial.println(deviceName);
        Serial.print("Delay Time: ");
        Serial.print(delayTime);
        Serial.println(" ms");
        Serial.print("Duration: ");
        Serial.print(duration);
        Serial.println(" ms");
        Serial.print("Iterations: ");
        Serial.println(iterations);
    } else {
        Serial.println("Invalid config format. Use: set_config:NAME,DELAY,DURATION,ITERATIONS");
    }
}

void parseLEDCommand(String params) {
    // Format: TYPE,STATE,BRIGHTNESS
    int firstComma = params.indexOf(',');
    int secondComma = params.indexOf(',', firstComma + 1);
    
    if (firstComma > 0 && secondComma > 0) {
        String type = params.substring(0, firstComma);
        String state = params.substring(firstComma + 1, secondComma);
        int brightness = params.substring(secondComma + 1).toInt();
        
        Serial.print("Setting ");
        Serial.print(type);
        Serial.print(" LED: ");
        Serial.print(state);
        Serial.print(" with brightness ");
        Serial.println(brightness);
        
        // Implement LED control
        if (type == "indicator") {
            if (state == "on") {
                sensor.enableIndicator();
            } else {
                sensor.disableIndicator();
            }
        } else if (type == "bulb") {
            if (state == "on") {
                sensor.enableBulb(AS7265x_LED_WHITE);
                // Set bulb current/brightness if supported by your sensor library
            } else {
                sensor.disableBulb(AS7265x_LED_WHITE);
            }
        }
    } else {
        Serial.println("Invalid LED command format. Use: set_led:TYPE,STATE,BRIGHTNESS");
    }
}

void startMeasurement() {
    Serial.println("Starting measurement cycle...");
    isMeasuring = true;
    
    // Lakukan pengukuran sebanyak jumlah loop yang diatur
    for (int loopCount = 1; loopCount <= iterations; loopCount++) {
        Serial.println("Starting measurement loop " + String(loopCount) + "...");

        int numReadings = duration / delayTime;
        float sum[18] = {0};
        for (int i = 0; i < numReadings; i++) {
            // Check for commands even during measurement
            checkSerialCommands();
            if (newCommand) {
                processCommand(commandBuffer);
                commandBuffer = "";
                newCommand = false;
            }
            
            sensor.takeMeasurementsWithBulb();

            float readings[18] = {
                // Sensor readings AS72653
                sensor.getCalibratedA(), sensor.getCalibratedB(), sensor.getCalibratedC(),
                sensor.getCalibratedD(), sensor.getCalibratedE(), sensor.getCalibratedF(),
                // Sensor readings AS72652
                sensor.getCalibratedG(), sensor.getCalibratedH(), sensor.getCalibratedI(),
                sensor.getCalibratedJ(), sensor.getCalibratedK(), sensor.getCalibratedL(),
                // Sensor readings AS72651
                sensor.getCalibratedR(), sensor.getCalibratedS(), sensor.getCalibratedT(),
                sensor.getCalibratedU(), sensor.getCalibratedV(), sensor.getCalibratedW()
            };

            for (int j = 0; j < 18; j++) {
                sum[j] += readings[j];
            }

            // Cetak hasil pembacaan sensor
            Serial.print("Reading " + String(i + 1) + ": ");
            for (int j = 0; j < 18; j++) {
                Serial.print("[" + String(j) + "]: " + String(readings[j], 2)); // Format dengan 2 desimal
                if (j < 17) Serial.print(", "); // Tambahkan koma untuk memisahkan nilai
            }
            Serial.println(); // Baris baru setelah semua nilai dicetak

            delay(delayTime);
        }

        Serial.println("Measurement completed for loop " + String(loopCount) + "!");
        Serial.println("Data siap dikalkulasi");
        
        // Kirim data ke server
        String currentName = deviceName + String(loopCount); // Tambahkan loopCount ke nama perangkat
        sendDataToServer(currentName, sensor.getTemperatureAverage(), sum, numReadings);
        
        // Pause between iterations
        Serial.println("Loop " + String(loopCount) + " selesai.");
        delay(5000); // Delay singkat antara iterasi
    }

    Serial.println("Semua loop selesai.");
    isMeasuring = false;
}

void sendDataToServer(String name, float temperature, float* sum, int numReadings) {
    if (!webSocketConnected) {
        Serial.println("WebSocket not connected. Cannot send data.");
        return;
    }
    
    StaticJsonDocument<1024> doc;

    // Tambahkan data utama ke JSON
    doc["name"] = name;
    doc["timestamp"] = getTimestamp(); // Fungsi untuk mendapatkan timestamp
    doc["temperature"] = String(temperature, 2).toFloat(); // Format dengan 2 angka desimal

    // Tambahkan data sensor AS7263 ke JSON
    doc["uv_410"] = String(sum[0] / numReadings, 2).toFloat();
    doc["uv_435"] = String(sum[1] / numReadings, 2).toFloat();
    doc["uv_460"] = String(sum[2] / numReadings, 2).toFloat();
    doc["uv_485"] = String(sum[3] / numReadings, 2).toFloat();
    doc["uv_510"] = String(sum[4] / numReadings, 2).toFloat();
    doc["uv_535"] = String(sum[5] / numReadings, 2).toFloat();

    // Tambahkan data sensor As7262 ke JSON
    doc["vis_560"] = String(sum[6] / numReadings, 2).toFloat();
    doc["vis_585"] = String(sum[7] / numReadings, 2).toFloat();
    doc["vis_645"] = String(sum[8] / numReadings, 2).toFloat();
    doc["vis_705"] = String(sum[9] / numReadings, 2).toFloat();
    doc["vis_900"] = String(sum[10] / numReadings, 2).toFloat();
    doc["vis_940"] = String(sum[11] / numReadings, 2).toFloat();

    // Tambahkan data sensor AS7261 ke JSON
    doc["nir_610"] = String(sum[12] / numReadings, 2).toFloat();
    doc["nir_680"] = String(sum[13] / numReadings, 2).toFloat();
    doc["nir_730"] = String(sum[14] / numReadings, 2).toFloat();
    doc["nir_760"] = String(sum[15] / numReadings, 2).toFloat();
    doc["nir_810"] = String(sum[16] / numReadings, 2).toFloat();
    doc["nir_860"] = String(sum[17] / numReadings, 2).toFloat();

    // Serialisasi JSON ke string
    String dataSensor;
    serializeJson(doc, dataSensor);

    // Kirim data ke server
    Serial.println("Data JSON yang dikirim:");
    Serial.println(dataSensor);
    
    client.send(dataSensor);
    Serial.println("Data sent to server. Waiting for response...");
    
    // The server response will be handled by the websocket message callback
    dataSent = false;
    unsigned long startTime = millis();
    while (!dataSent && millis() - startTime < 5000) {
        client.poll(); // Keep the connection alive while waiting for response
        delay(100);
    }
    
    if (!dataSent) {
        Serial.println("No server response received. Data may not have been saved.");
    }
}

void setIntegrationTime(int time) {
    Serial.print("Setting integration time to ");
    Serial.print(time);
    Serial.println(" ms");
    
    // Implementation depends on your specific sensor library
    // This is a placeholder - update with actual implementation
    // sensor.setIntegrationTime(time);
    
    Serial.println("Integration time set!");
}

void setGain(float gain) {
    Serial.print("Setting gain to ");
    Serial.print(gain);
    Serial.println("x");
    
    // Implementation depends on your specific sensor library
    // This is a placeholder - update with actual implementation
    // sensor.setGain(gain);
    
    Serial.println("Gain set!");
}

void setMode(int mode) {
    Serial.print("Setting measurement mode to ");
    Serial.println(mode);
    
    // Implementation depends on your specific sensor library
    // This is a placeholder - update with actual implementation
    // sensor.setMeasurementMode(mode);
    
    Serial.println("Measurement mode set!");
}

String getTimestamp() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        return "1970-01-01T00:00:00Z"; // Default timestamp if time not available
    }

    char timeString[30];
    strftime(timeString, sizeof(timeString), "%Y-%m-%dT%H:%M:%S%z", &timeinfo);
    return String(timeString);
}