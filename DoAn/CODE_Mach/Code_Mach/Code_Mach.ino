#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi credentials
const char* ssid = "Giangnam Coffee VN";
const char* password = "";

// Server URL
const char* serverUrl = "http://10.10.3.28:5000/data"; // Nếu client và server khác máy

// Danh sách tên các trạm
const char* stationNames[] = {"Station1", "Station2", "Station3", "Station4", "Station5"};

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to Wi-Fi");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    // Duyệt qua tất cả 5 trạm và gửi dữ liệu
    for (int i = 0; i < 5; i++) {
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");

      // Tạo dữ liệu ngẫu nhiên cho mỗi trạm
      StaticJsonDocument<256> jsonDoc;
      jsonDoc["station_name"] = stationNames[i];
      jsonDoc["light_intensity"] = random(100, 1000);     // Lux
      jsonDoc["rainfall"] = random(0, 100) / 10.0;        // mm
      jsonDoc["temperature"] = random(-10, 40);           // °C
      jsonDoc["humidity"] = random(20, 100);              // %
      jsonDoc["pressure"] = random(950, 1050);            // hPa
      jsonDoc["wind_speed"] = random(0, 15);              // m/s
      jsonDoc["wind_direction"] = random(0, 360);         // Degrees

      // Serialize JSON data
      String jsonData;
      serializeJson(jsonDoc, jsonData);

      // Debug output
      Serial.println("Sending JSON data:");
      Serial.println(jsonData);

      // Gửi yêu cầu HTTP POST
      int httpResponseCode = http.POST(jsonData);
      if (httpResponseCode > 0) {
        Serial.println("Data sent successfully");
        Serial.println("Server response: " + http.getString());
      } else {
        Serial.println("Error in sending data: " + String(httpResponseCode));
      }
      http.end();
    }
  } else {
    Serial.println("Wi-Fi not connected");
  }

  delay(2000); // Chờ 2 giây trước khi gửi dữ liệu cho 5 trạm tiếp theo
}
