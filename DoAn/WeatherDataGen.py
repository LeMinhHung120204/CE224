import random
import datetime
import sqlite3  # Correct import for sqlite3 module
from server import app  # You only need to import app from server.py

# Tạo danh sách các trạm
stations = [f"station{i}" for i in range(1, 6)]

# Tạo danh sách các hướng gió tương ứng với các góc trên la bàn
wind_directions = [
    (0, "N"),      # Bắc
    (45, "NE"),    # Đông Bắc
    (90, "E"),     # Đông
    (135, "SE"),   # Đông Nam
    (180, "S"),    # Nam
    (225, "SW"),   # Tây Nam
    (270, "W"),    # Tây
    (315, "NW")    # Tây Bắc
]

# Hàm sinh dữ liệu mỗi giờ và lưu vào cơ sở dữ liệu
def generate_hourly_data(start_date, end_date):
    conn = sqlite3.connect('weather_station.db')
    c = conn.cursor()

    current_time = start_date

    while current_time <= end_date:
        # Chọn trạm ngẫu nhiên
        station = random.choice(stations)

        # Sinh dữ liệu ngẫu nhiên cho các chỉ số
        light_intensity = round(random.uniform(0, 10000), 2)  # Cường độ ánh sáng (0 - 10,000 lux)
        rain_level = round(random.uniform(0, 100), 2)          # Mưa (0 - 100 mm)
        temperature = round(random.uniform(0, 40), 2)         # Nhiệt độ (0°C to 40°C)
        humidity = round(random.uniform(20, 100), 2)           # Độ ẩm (20% to 100%)
        pressure = round(random.uniform(980, 1030), 2)         # Áp suất (980 hPa to 1030 hPa)
        wind_speed = round(random.uniform(0, 30), 2)           # Tốc độ gió (0 - 30 m/s)
        
        # Chọn hướng gió ngẫu nhiên từ danh sách wind_directions
        wind_direction_angle, wind_direction_label = random.choice(wind_directions)

        # Tạo bản ghi vào cơ sở dữ liệu
        c.execute('''INSERT INTO station_data (station_name, temperature, humidity, light_intensity, 
                    rainfall, pressure, wind_speed, wind_direction, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (station, temperature, humidity, light_intensity, rain_level, pressure,
                   wind_speed, wind_direction_label, current_time.strftime('%Y-%m-%d %H:%M:%S')))

        # Commit và lưu vào DB
        conn.commit()

        # Tăng thời gian thêm 1 giờ
        current_time += datetime.timedelta(hours=1)

    conn.close()
    print(f"Đã tạo và lưu dữ liệu mỗi giờ từ {start_date} đến {end_date} vào cơ sở dữ liệu!")

# Chạy hàm và tạo dữ liệu
start_date = datetime.datetime(2024, 1, 1)
end_date = datetime.datetime(2024, 12, 31)

generate_hourly_data(start_date, end_date)
