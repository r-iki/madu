/*
 * ESP32 WiFi Configuration via Bluetooth Low Energy (BLE)
 * 
 * Memungkinkan konfigurasi WiFi pada ESP32 melalui koneksi Bluetooth,
 * tanpa perlu mengedit kode atau menggunakan kabel serial.
 * 
 */

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <WiFi.h>
#include <ArduinoJson.h>

// Definisi UUID untuk layanan BLE dan karakteristik
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define WIFI_CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define SCAN_CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a9"
#define STATUS_CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26aa"

// Variabel untuk menyimpan informasi WiFi
String ssid = "";
String password = "";
bool wifiCredentialsReceived = false;
bool deviceConnected = false;
bool scanRequested = false;
bool oldDeviceConnected = false;

// Objek BLE yang diperlukan
BLEServer* pServer = NULL;
BLECharacteristic* pWifiCharacteristic = NULL;
BLECharacteristic* pScanCharacteristic = NULL;
BLECharacteristic* pStatusCharacteristic = NULL;

// Timeout untuk koneksi WiFi
const int WIFI_TIMEOUT = 10000; // 10 detik

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("Perangkat terhubung melalui BLE");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("Perangkat terputus dari BLE");
    
    // Mulai iklan lagi untuk memungkinkan koneksi baru
    BLEDevice::startAdvertising();
  }
};

class WifiCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    std::string value = pCharacteristic->getValue();
    if (value.length() > 0) {
      Serial.println("*********");
      Serial.print("Data WiFi diterima: ");
      String jsonStr = "";
      for (int i = 0; i < value.length(); i++) {
        jsonStr += value[i];
      }
      Serial.println(jsonStr);
      Serial.println("*********");
      
      // Parse JSON untuk mendapatkan SSID dan password
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, jsonStr);
      
      if (doc.containsKey("ssid")) {
        ssid = doc["ssid"].as<String>();
        Serial.print("SSID: ");
        Serial.println(ssid);
      }
      
      if (doc.containsKey("password")) {
        password = doc["password"].as<String>();
        Serial.print("Password: ");
        Serial.println("********");
      }
      
      wifiCredentialsReceived = true;
    }
  }
};

class ScanCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    std::string value = pCharacteristic->getValue();
    if (value.length() > 0 && value[0] == '1') {
      Serial.println("Permintaan pemindaian WiFi diterima");
      scanRequested = true;
    }
  }
};

void setup() {
  Serial.begin(115200);
  Serial.println("Memulai konfigurasi WiFi via BLE...");

  // Inisialisasi BLE
  BLEDevice::init("ESP32-WiFi-Config");
  
  // Buat server BLE
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Buat layanan BLE
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Buat karakteristik untuk konfigurasi WiFi
  pWifiCharacteristic = pService->createCharacteristic(
                          WIFI_CHARACTERISTIC_UUID,
                          BLECharacteristic::PROPERTY_WRITE
                        );
  pWifiCharacteristic->setCallbacks(new WifiCallbacks());

  // Buat karakteristik untuk permintaan pemindaian WiFi
  pScanCharacteristic = pService->createCharacteristic(
                            SCAN_CHARACTERISTIC_UUID,
                            BLECharacteristic::PROPERTY_READ |
                            BLECharacteristic::PROPERTY_WRITE |
                            BLECharacteristic::PROPERTY_NOTIFY
                          );
  pScanCharacteristic->setCallbacks(new ScanCallbacks());
  pScanCharacteristic->addDescriptor(new BLE2902());

  // Buat karakteristik untuk status WiFi
  pStatusCharacteristic = pService->createCharacteristic(
                             STATUS_CHARACTERISTIC_UUID,
                             BLECharacteristic::PROPERTY_READ |
                             BLECharacteristic::PROPERTY_NOTIFY
                           );
  pStatusCharacteristic->addDescriptor(new BLE2902());

  // Mulai layanan
  pService->start();

  // Mulai iklan
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // Membantu dengan iPhone
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  
  Serial.println("BLE siap dan menunggu koneksi...");
  updateStatusCharacteristic("ready", "", "", "");
}

void loop() {
  // Jika kredensial WiFi diterima, coba hubungkan ke WiFi
  if (wifiCredentialsReceived) {
    wifiCredentialsReceived = false;
    connectToWiFi();
  }

  // Jika permintaan pemindaian WiFi diterima
  if (scanRequested) {
    scanRequested = false;
    scanWiFiNetworks();
  }

  // Menangani notifikasi BLE
  if (deviceConnected) {
    delay(1000); // Tunggu 1 detik
  }
  
  // Menangani pengaturan iklan ulang saat koneksi terputus
  if (!deviceConnected && oldDeviceConnected) {
    delay(500); // Berikan stack BLE waktu untuk siap
    pServer->startAdvertising(); // Mulai iklan lagi
    Serial.println("Mulai iklan BLE");
    oldDeviceConnected = deviceConnected;
  }
  
  // Menangani koneksi baru
  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }
}

void connectToWiFi() {
  if (ssid.length() == 0) {
    Serial.println("SSID kosong, tidak bisa menghubungkan");
    updateStatusCharacteristic("error", "", "", "SSID empty");
    return;
  }

  Serial.println("Mencoba menghubungkan ke WiFi...");
  updateStatusCharacteristic("connecting", ssid, "", "");
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), password.c_str());
  
  unsigned long startAttemptTime = millis();
  
  while (WiFi.status() != WL_CONNECTED && 
         millis() - startAttemptTime < WIFI_TIMEOUT) {
    Serial.print(".");
    delay(500);
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("Terhubung ke WiFi!");
    Serial.print("Alamat IP: ");
    Serial.println(WiFi.localIP().toString());
    
    // Update karakteristik status
    updateStatusCharacteristic("connected", ssid, WiFi.localIP().toString(), String(WiFi.RSSI()));
  } else {
    Serial.println("");
    Serial.println("Koneksi gagal.");
    WiFi.disconnect();
    
    // Update karakteristik status dengan kode kesalahan
    String errorMsg = "Failed to connect";
    switch(WiFi.status()) {
      case WL_NO_SSID_AVAIL: errorMsg = "SSID not available"; break;
      case WL_CONNECT_FAILED: errorMsg = "Wrong password"; break;
      case WL_IDLE_STATUS: errorMsg = "Idle status"; break;
      default: errorMsg = "Unknown error"; break;
    }
    updateStatusCharacteristic("error", ssid, "", errorMsg);
  }
}

void scanWiFiNetworks() {
  Serial.println("Memindai jaringan WiFi...");
  updateStatusCharacteristic("scanning", "", "", "");
  
  int networksFound = WiFi.scanNetworks();
  Serial.println("Pemindaian selesai");
  
  if (networksFound == 0) {
    Serial.println("Tidak ditemukan jaringan WiFi");
    pScanCharacteristic->setValue("No networks found");
    pScanCharacteristic->notify();
  } else {
    Serial.print(networksFound);
    Serial.println(" jaringan ditemukan");
    
    // Buat JSON array untuk daftar jaringan
    DynamicJsonDocument doc(4096);
    JsonArray networks = doc.createNestedArray("networks");
    
    for (int i = 0; i < networksFound; i++) {
      JsonObject network = networks.createNestedObject();
      network["ssid"] = WiFi.SSID(i);
      network["rssi"] = WiFi.RSSI(i);
      network["encryption"] = WiFi.encryptionType(i) == WIFI_AUTH_OPEN ? false : true;
    }
    
    // Serialize JSON ke string
    String jsonString;
    serializeJson(doc, jsonString);
    
    // Jika string terlalu panjang, kirim bagian per bagian
    if (jsonString.length() > 512) {
      // Kirim notifikasi bahwa hasil akan dibagi menjadi beberapa bagian
      pScanCharacteristic->setValue("multi-part-start");
      pScanCharacteristic->notify();
      delay(100);
      
      // Kirim dalam beberapa bagian
      const int chunkSize = 500;
      for (int i = 0; i < jsonString.length(); i += chunkSize) {
        String chunk = jsonString.substring(i, min(i + chunkSize, (int)jsonString.length()));
        pScanCharacteristic->setValue(chunk.c_str());
        pScanCharacteristic->notify();
        delay(100);  // Berikan waktu untuk pemrosesan
      }
      
      // Kirim notifikasi bahwa transmisi selesai
      pScanCharacteristic->setValue("multi-part-end");
      pScanCharacteristic->notify();
    } else {
      // Jika cukup kecil, kirim dalam satu pesan
      pScanCharacteristic->setValue(jsonString.c_str());
      pScanCharacteristic->notify();
    }
  }
  
  // Hapus hasil pemindaian untuk membebaskan memori
  WiFi.scanDelete();
  updateStatusCharacteristic("ready", "", "", "");
}

void updateStatusCharacteristic(String status, String connectedSsid, String ip, String message) {
  DynamicJsonDocument doc(512);
  doc["status"] = status;
  if (connectedSsid.length() > 0) doc["ssid"] = connectedSsid;
  if (ip.length() > 0) doc["ip"] = ip;
  if (message.length() > 0) doc["message"] = message;
  if (status == "connected") doc["rssi"] = WiFi.RSSI();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  pStatusCharacteristic->setValue(jsonString.c_str());
  pStatusCharacteristic->notify();
}