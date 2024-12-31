import random
import datetime
from server import app, db, WeatherData  # Import từ server.py để truy cập DB và model WeatherData

# Tạo danh sách các trạm
stations = [f"station{i}" for i in range(1, 6)]

# Hàm sinh dữ liệu theo thứ tự thời gian và lưu vào cơ sở dữ liệu
def generate_ordered_data(start_date, end_date, num_records):
    with app.app_context():  # Đảm bảo có app context
        # Tính toán khoảng thời gian giữa start_date và end_date
        time_diff = end_date - start_date

        # Tạo ra các timestamp theo thứ tự liên tiếp
        for i in range(num_records):
            # Tính toán thời gian theo thứ tự từ start_date, tăng dần theo chỉ số i
            timestamp = start_date + (time_diff / num_records) * i

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

# Chạy hàm và tạo dữ liệu theo thứ tự thời gian
start_date = datetime.datetime(2022, 1, 1)
end_date = datetime.datetime(2024, 12, 31)

# Số lượng bản ghi cần tạo
num_records = 1000

generate_ordered_data(start_date, end_date, num_records)
