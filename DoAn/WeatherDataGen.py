import random
import datetime
from server import app, db, WeatherData  # Import từ server.py để truy cập DB và model WeatherData

# Tạo danh sách các trạm
stations = [f"station{i}" for i in range(1, 6)]

# Hàm sinh dữ liệu ngẫu nhiên và lưu vào cơ sở dữ liệu
def generate_random_data(start_date, end_date, num_records):
    with app.app_context():  # Đảm bảo có app context
        for _ in range(num_records):
            # Tạo timestamp ngẫu nhiên trong khoảng thời gian
            timestamp = start_date + (end_date - start_date) * random.random()
            # Chuyển đổi timestamp thành đối tượng datetime
            timestamp = timestamp

            # Chọn trạm ngẫu nhiên
            station = random.choice(stations)

            # Sinh dữ liệu ngẫu nhiên cho các chỉ số
            light_intensity = round(random.uniform(0, 10000), 2)  # Light intensity (0 - 10,000 lux)
            rain_level = round(random.uniform(0, 200), 2)          # Rain level (0 - 200 mm)
            temperature = round(random.uniform(-10, 40), 2)        # Temperature (-10°C to 40°C)
            humidity = round(random.uniform(0, 100), 2)            # Humidity (0 - 100%)
            pressure = round(random.uniform(950, 1050), 2)         # Pressure (950 hPa to 1050 hPa)
            wind_speed = round(random.uniform(0, 50), 2)           # Wind speed (0 - 50 m/s)
            wind_direction = round(random.uniform(0, 360), 2)      # Wind direction (0° to 360°)

            # Tạo đối tượng WeatherData và lưu vào cơ sở dữ liệu
            new_entry = WeatherData(
                station_name=station,
                lightIntensity=light_intensity,
                rainLevel=rain_level,
                temperature=temperature,
                humidity=humidity,
                pressure=pressure,
                windSpeed=wind_speed,
                windDirection=wind_direction,
                timestamp=timestamp  # Lưu đối tượng datetime
            )

            # Thêm đối tượng vào phiên làm việc và commit để lưu vào DB
            db.session.add(new_entry)
            db.session.commit()

        print(f"Đã tạo và lưu {num_records} bản ghi vào cơ sở dữ liệu!")

# Chạy hàm và tạo dữ liệu ngẫu nhiên
start_date = datetime.datetime(2022, 1, 1)
end_date = datetime.datetime(2024, 12, 31)

# Số lượng bản ghi cần tạo
num_records = 1000

generate_random_data(start_date, end_date, num_records)
