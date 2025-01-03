import os
import pandas as pd
from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta
import threading
import matplotlib
matplotlib.use('Agg')  # Sử dụng backend 'Agg' không yêu cầu GUI
import matplotlib.pyplot as plt
import google.generativeai as genai


app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('weather_station.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS station_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_name TEXT,
                    temperature REAL,
                    humidity REAL,
                    light_intensity REAL,
                    rainfall REAL,
                    pressure REAL,
                    wind_speed REAL,
                    wind_direction TEXT,
                    timestamp DATETIME
                )''')
    conn.commit()
    conn.close()

init_db()

# In-memory data for real-time updates
real_time_data = {}
lock = threading.Lock()

# Function to log data to the database every 30 seconds
last_logged_time = datetime.now()

def log_to_db():
    global last_logged_time
    while True:
        with lock:
            current_time = datetime.now()
            if current_time - last_logged_time >= timedelta(seconds=30):
                conn = sqlite3.connect('weather_station.db')
                c = conn.cursor()
                for station, data in real_time_data.items():
                    c.execute('''INSERT INTO station_data (station_name, temperature, humidity, light_intensity, 
                                 rainfall, pressure, wind_speed, wind_direction, timestamp)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (station, data['temperature'], data['humidity'], data['light_intensity'],
                               data['rainfall'], data['pressure'], data['wind_speed'], data['wind_direction'], 
                               data['timestamp']))
                conn.commit()
                conn.close()
                last_logged_time = current_time

# Start the logging thread
threading.Thread(target=log_to_db, daemon=True).start()

@app.route('/update', methods=['POST'])
def update_data():
    data = request.json
    station_name = data.get('station_name')
    if not station_name:
        return jsonify({'error': 'Station name is required'}), 400

    with lock:
        real_time_data[station_name] = {
            'temperature': data.get('temperature'),
            'humidity': data.get('humidity'),
            'light_intensity': data.get('light_intensity'),
            'rainfall': data.get('rainfall'),
            'pressure': data.get('pressure'),
            'wind_speed': data.get('wind_speed'),
            'wind_direction': data.get('wind_direction'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    return jsonify({'message': 'Data updated successfully'})

@app.route('/data', methods=['GET', 'POST'])
def data_endpoint():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        station_name = data.get('station_name')
        if not station_name:
            return jsonify({'error': 'Station name is required'}), 400

        with lock:
            real_time_data[station_name] = {
                'station_name': station_name,  # Thêm tên trạm
                'temperature': data.get('temperature'),
                'humidity': data.get('humidity'),
                'light_intensity': data.get('light_intensity'),
                'rainfall': data.get('rainfall'),
                'pressure': data.get('pressure'),
                'wind_speed': data.get('wind_speed'),
                'wind_direction': data.get('wind_direction'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        return jsonify({'message': 'Data received successfully'}), 200

    elif request.method == 'GET':
        with lock:
            # Trả về dữ liệu đã được bổ sung tên trạm
            return jsonify(list(real_time_data.values()))

@app.route('/chart', methods=['GET'])
def chart():
    station_id = request.args.get('station')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    print(f"Received chart request: Station={station_id}, Start={start_date}, End={end_date}")  # Log for debugging

    if not station_id or not start_date or not end_date:
        return render_template('chart.html')

    # Xử lý dữ liệu đầu vào
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Lọc dữ liệu từ cơ sở dữ liệu trong khoảng thời gian
    conn = sqlite3.connect('weather_station.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM station_data WHERE station_name=? AND timestamp BETWEEN ? AND ? 
                 ORDER BY timestamp''', 
              (station_id, start_date, end_date))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "No data found for the selected date range."}), 400

    # Chuyển dữ liệu thành DataFrame
    data_dict = [{
        'timestamp': row[9],
        'lightIntensity': row[4],
        'rainLevel': row[5],
        'temperature': row[2],
        'humidity': row[3],
        'pressure': row[6],
        'windSpeed': row[7],
        'windDirection': row[8]
    } for row in rows]

    station_df = pd.DataFrame(data_dict)

    # Phương pháp nội suy để lấy các điểm dữ liệu
    # Ensure that 'timestamp' is in the correct datetime format
    station_df['timestamp'] = pd.to_datetime(station_df['timestamp'])

    # Ensure time_points are of type 'datetime'
    time_points = pd.to_datetime(pd.date_range(start=start_date, end=end_date, periods=20))

    # Reindex with 'nearest' method
    station_df = station_df.set_index('timestamp').reindex(time_points, method='nearest').reset_index()


    # Tạo biểu đồ và lưu file
    save_path = "static/charts"
    os.makedirs(save_path, exist_ok=True)

    chart_paths = {}
    features = ["lightIntensity", "rainLevel", "temperature", "humidity", "pressure", "windSpeed"]

    for feature in features:
        if feature in station_df:
            labels = station_df["index"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
            values = station_df[feature].tolist()

            # Tạo biểu đồ
            fig, ax = plt.subplots(figsize=(12, 8))  # Tăng chiều cao để tránh bị cắt
            ax.plot(labels, values, marker='o', label=feature, color='blue')

            # Xử lý việc hiển thị các mốc thời gian
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')  # Nghiêng mốc thời gian 45 độ

            plt.subplots_adjust(bottom=0.25)
            ax.set_xlabel('Date')
            ax.set_ylabel(f'{feature} Value')
            ax.set_title(f'{feature} Over Time')
            ax.legend()
            ax.grid()

            # Lưu biểu đồ
            file_name = f"{feature}.png"
            file_path = os.path.join(save_path, file_name)
            fig.savefig(file_path)
            plt.close(fig)

            chart_paths[feature] = file_name

    print(f"Chart paths generated: {chart_paths}")  # Log the generated chart paths

    return jsonify(chart_paths), 200

@app.route('/')
def index():
    with lock:
        data = real_time_data.copy()
    return render_template('index.html', data=data)

@app.route('/all-data', methods=['GET'])
def all_data():
    # Kết nối tới cơ sở dữ liệu SQLite
    conn = sqlite3.connect('weather_station.db')
    c = conn.cursor()
    # Truy vấn dữ liệu từ bảng station_data
    c.execute('SELECT * FROM station_data ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()

    # Chuyển đổi dữ liệu truy vấn thành danh sách từ điển
    data = [
        {
            'id': row[0],
            'station_name': row[1],
            'lightIntensity': row[4],  # Cường độ ánh sáng
            'rainLevel': row[5],  # Lượng mưa
            'temperature': row[2],  # Nhiệt độ
            'humidity': row[3],  # Độ ẩm
            'pressure': row[6],  # Áp suất
            'windSpeed': row[7],  # Tốc độ gió
            'windDirection': row[8],  # Hướng gió
            'timestamp': row[9],  # Thời gian
        } for row in rows
    ]

    # Truyền dữ liệu vào tệp HTML và hiển thị
    return render_template('all_data.html', data=data)


@app.route('/analysis')
def analysis():
    month = request.args.get('month')
    year = request.args.get('year')
    station_name = request.args.get('stationName')

    if month is None or year is None:
        file_path = "static/output_analysis.txt"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write('')
        return render_template('analysis.html')

    # Chuyển đổi tháng và năm sang khoảng thời gian
    start_date = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d") if month != 'all' else datetime.strptime(f"{year}-01-01", "%Y-%m-%d")
    end_date = datetime.strptime(f"{year}-{month}-28", "%Y-%m-%d") if month != 'all' else datetime.strptime(f"{year}-12-31", "%Y-%m-%d")

    # Truy vấn dữ liệu từ SQL
    conn = sqlite3.connect('weather_station.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM station_data WHERE station_name=? AND timestamp BETWEEN ? AND ? ORDER BY timestamp''', 
              (station_name, start_date, end_date))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "No data found for the selected month, year, and station."}), 400

    # Chuyển dữ liệu thành dictionary để xử lý
    data_dict = [{
        'timestamp': row[9],
        'lightIntensity': row[4],
        'rainLevel': row[5],
        'temperature': row[2],
        'humidity': row[3],
        'pressure': row[6],
        'windSpeed': row[7],
        'windDirection': row[8]
    } for row in rows]

    # Gửi dữ liệu cho GenAI để phân tích
    genai.configure(api_key="AIzaSyAm8V4F1i_oeF9PCfjwin0gUrfHcRxcV8Q")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"Analyze the weather data for the station {station_name} with this data: {data_dict} use instructions: 1. Temperature: Description: Temperature can be described as how hot or cold the environment is at any given time. Seasonal changes, time of day, or unusual changes in temperature can affect health and the environment. Average: Calculate the average temperature over a day, week, or month. Standard Deviation: Measure the variability of temperature. Max/Min: Find the highest and lowest temperature within a time period. 2. Humidity: Description: Humidity indicates the amount of water vapor in the air. It can be described as dry or humid air. Average: Calculate the average humidity over a specific time period. Standard Deviation: Measure the variability of humidity. Max/Min: Find the highest and lowest humidity values. 3. Rain Level: Description: Rain level measures the amount of rainfall in the area. It can be described as heavy rain, light rain, or seasonal changes in precipitation. Total Rainfall: Calculate the total amount of rain over a period (e.g., daily, weekly, or monthly). Rain Frequency Analysis: Determine the number of rainy days within a given period. Max/Min: Identify the highest and lowest rainfall values in a given time period. 4. Pressure: Description: Atmospheric pressure can provide insights into weather patterns. High pressure typically corresponds to dry weather, while low pressure is associated with rain or storms. Average: Calculate the average pressure over a day or week. Standard Deviation: Measure the variation in pressure. Max/Min: Find the highest and lowest pressure values. 5. Wind Speed: Description: Wind speed can be described as light wind, strong wind, or stormy wind. It can also be used to discuss the effects of wind on outdoor activities or extreme weather events like storms. Average: Calculate the average wind speed over a period. Max/Min: Identify the highest and lowest wind speed values. Standard Deviation: Measure the variation in wind speed. 6. Wind Direction: Description: Wind direction can be described as the direction from which the wind is blowing (e.g., wind from the north, south). It plays a role in weather phenomena like storms or rain. Analysis of Dominant Wind Direction: Determine the most common wind direction over a day or week. Wind Rose: Use a circular chart to represent the distribution of wind directions. 7. Light Intensity: Description: Light intensity can describe how bright the environment is (e.g., bright sunlight during the day, dim light at night). Average: Calculate the average light intensity over a day or week. Max/Min: Identify the highest and lowest light intensity levels in a given time period. Variation: Measure the fluctuation in light intensity over time. 8. Relationships Between Variables: Description: There could be relationships between the variables. For example, when the temperature is high, humidity may decrease, or when there is strong wind, rainfall may increase. Pearson Correlation Coefficient: Calculate the correlation between different variables, such as temperature and humidity, or wind and rain. Scatter Plot: Create scatter plots to visualize the relationships between variables. 9. Anomaly Detection: Description: Unusual events may occur, such as very high rainfall or strong winds. These anomalies need to be detected and assessed. Outlier Detection: Use statistical methods such as Z-scores or IQR (Interquartile Range) to find outlier values (e.g., extremely high rainfall in one day). 10. Forecasting and Trends: Description: Based on the collected data, predictions can be made about future trends, such as the rainy season, the highest temperature in the next month, or wind patterns. Basic Weather Forecasting: Use simple forecasting models based on data trends. Trend Calculation: Use techniques like linear regression to predict future trends (e.g., rising temperatures over time).")

    # Lưu kết quả phân tích vào file
    file_path = "static/output_analysis.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(response.text)

    return render_template('analysis.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
