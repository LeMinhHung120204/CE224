#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <Adafruit_BMP085.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <WiFi.h>

// WiFi thông tin
const char* ssid = "A19.09_5G";      // Thay bằng SSID của bạn
const char* password = "01234567891011"; // Thay bằng mật khẩu WiFi

// MQTT Broker thông tin
const char* mqtt_server = "192.168.1.134"; // Địa chỉ server MQTT
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

// Định nghĩa các chân kết nối
#define TFT_CS   5
#define TFT_RST  19
#define TFT_DC   2
#define TFT_MOSI 23
#define TFT_SCK  18

#define LIGHT_SENSOR_A0 35
#define RAIN_SENSOR_A0  32
#define DHT_PIN 16
#define DHT_TYPE DHT22
#define GY87_SCL 22
#define GY87_SDA 21
#define KY003_PIN 13 // Cảm biến từ trường KY003
#define WIND_SPEED_A0 25
#define WIND_SPEED_D0 17

// Hệ số chuyển đổi tốc độ gió
#define WIND_RADIUS 0.0125 // Bán kính bánh xe quay (m)
#define WIND_HOLES 20       // Số lỗ trên bánh xe

// Hệ số chuyển đổi: Số xung tương ứng với 1 ml nước
const float PULSES_PER_ML = 1.0; // Thay đổi tùy thuộc vào cơ cấu đo thực tế

// Khởi tạo màn hình TFT
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

// Khởi tạo DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// Khởi tạo BMP180 và MPU6050
Adafruit_BMP085 bmp;
Adafruit_MPU6050 mpu;

// Biến để lưu dữ liệu
float lightIntensity;
float rainLevel;
float temperature;
float humidity;
float pressure;
float windDirection;
volatile int windPulseCount = 0; // Đếm xung của FC03
volatile int rainPulseCount = 0; // Đếm xung của cảm biến từ trường KY003
float windSpeed; // Tốc độ gió
float rainFlowRate; // Lưu lượng mưa (ml/s)

sensors_event_t mpu_accel, mpu_gyro, mpu_temp;

// Hàm xử lý ngắt cho FC03
void windPulseISR() {
  windPulseCount++;
}

// Hàm xử lý ngắt cho KY003
void rainPulseISR() {
  rainPulseCount++;
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) { // Tên client MQTT
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");

  // Kết nối MQTT Broker
  client.setServer(mqtt_server, mqtt_port);

  // Khởi tạo màn hình TFT
  tft.begin();
  tft.setRotation(3);
  tft.fillScreen(ILI9341_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(ILI9341_WHITE);

  // Khởi tạo DHT22
  dht.begin();

  // Khởi tạo giao tiếp I2C
  Wire.begin(GY87_SDA, GY87_SCL);

  // Khởi tạo BMP180
  if (!bmp.begin()) {
    Serial.println("BMP180 not detected");
    while (1);
  }

  // Khởi tạo MPU6050
  if (!mpu.begin()) {
    Serial.println("MPU6050 not detected");
    while (1);
  }

  // Cấu hình chân FC03 và gắn ngắt
  pinMode(WIND_SPEED_D0, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(WIND_SPEED_D0), windPulseISR, FALLING);

  // Cấu hình chân KY003 và gắn ngắt
  pinMode(KY003_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(KY003_PIN), rainPulseISR, FALLING);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Đọc dữ liệu từ cảm biến ánh sáng
  lightIntensity = analogRead(LIGHT_SENSOR_A0);

  // Đọc dữ liệu từ cảm biến mưa
  rainLevel = analogRead(RAIN_SENSOR_A0);

  // Đọc dữ liệu từ DHT22
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();

  // Đọc dữ liệu từ BMP180
  pressure = bmp.readPressure() / 100.0; // Đơn vị hPa

  // Đọc dữ liệu từ MPU6050
  mpu.getEvent(&mpu_accel, &mpu_gyro, &mpu_temp);

  // Tính hướng gió từ MPU6050 (tọa độ X, Y)
  windDirection = atan2(mpu_accel.acceleration.y, mpu_accel.acceleration.x) * 180 / PI;
  if (windDirection < 0) windDirection += 360; // Chuyển sang giá trị dương

  // Tính tốc độ gió
  noInterrupts();
  int windPulses = windPulseCount;
  windPulseCount = 0;
  interrupts();
  float windCircumference = 2 * PI * WIND_RADIUS; // Chu vi bánh xe (m)
  float windFrequency = (float)windPulses / WIND_HOLES; // Tần số quay bánh xe
  windSpeed = windFrequency * windCircumference; // Tính tốc độ gió (m/s)

  // Tính lưu lượng mưa
  noInterrupts();
  int rainPulses = rainPulseCount;
  rainPulseCount = 0;
  interrupts();
  rainFlowRate = rainPulses / PULSES_PER_ML; // Tính lưu lượng mưa (ml/s)

  // Gửi dữ liệu qua MQTT
  client.publish("station", + "#");
  // 
  client.publish("station1/lightIntensity", String(lightIntensity).c_str());
  client.publish("station1/rainLevel", String(rainLevel).c_str());
  client.publish("station1/temperature", String(temperature).c_str());
  client.publish("station1/humidity", String(humidity).c_str());
  client.publish("station1/pressure", String(pressure).c_str());
  client.publish("station1/windSpeed", String(windSpeed).c_str());
  client.publish("station1/rainFlowRate", String(rainFlowRate).c_str());
  
  // Hiển thị dữ liệu trên màn hình TFT
  tft.fillScreen(ILI9341_BLACK);
  tft.setCursor(10, 40);
  tft.print("Light: "); tft.println(lightIntensity);
  tft.setCursor(10, 70);
  tft.print("Rain Lvl: "); tft.println(rainLevel);
  tft.setCursor(10, 100);
  tft.print("Rain Flow: "); tft.print(rainFlowRate); tft.println(" ml/s");
  tft.setCursor(10, 130);
  tft.print("Temp: "); tft.println(temperature);
  tft.setCursor(10, 160);
  tft.print("Humidity: "); tft.println(humidity);
  tft.setCursor(10, 190);
  tft.print("Pressure: "); tft.println(pressure);
  tft.setCursor(10, 220);
  tft.print("Wind Dir: "); tft.print(windDirection); tft.println(" deg");
  tft.setCursor(10, 250);
  tft.print("Wind Spd: "); tft.print(windSpeed); tft.println(" m/s");

  delay(1000); // Đợi 1 giây trước lần đọc tiếp theo
}
