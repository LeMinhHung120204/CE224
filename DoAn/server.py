import paho.mqtt.client as mqtt
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime
import pandas as pd
import os
import glob
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_data.db'  # Tên file SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)  # Khởi tạo SQLAlchemy
# Data storage for the web app
class WeatherData(db.Model):
    id = Column(Integer, primary_key=True)  # Khóa chính
    station_name = Column(String(255), nullable=False)  # Tên trạm
    lightIntensity = Column(Float, nullable=False)
    rainLevel = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    windSpeed = Column(Float, nullable=False)
    windDirection = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)  # Thời gian nhận dữ liệu

# Tạo bảng trong cơ sở dữ liệu
with app.app_context():
    db.create_all()
data = {
    "name": [],
    "lightIntensity": [],
    "rainLevel": [],
    "temperature": [],
    "humidity": [],
    "pressure": [],
    "windSpeed": [],
    "windDirection": [],
    "rainFlowRate": [],
    "month_data": []  # Placeholder for monthly data
}
df = None

# MQTT Broker configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "station1/#"

# MQTT callback functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")  # Giải mã payload
    payload = payload.split('#')  # Tách dữ liệu từ chuỗi
    features = [
        "lightIntensity",
        "rainLevel",
        "temperature",
        "humidity",
        "pressure",
        "windSpeed",
        "windDirection"
    ]

    # Tạo bản ghi mới và lưu vào SQLite
    new_entry = WeatherData(
        station_name="station1",
        lightIntensity=float(payload[0]),
        rainLevel=float(payload[1]),
        temperature=float(payload[2]),
        humidity=float(payload[3]),
        pressure=float(payload[4]),
        windSpeed=float(payload[5]),
        windDirection=float(payload[6])
    )
    db.session.add(new_entry)
    db.session.commit()

    print(f"Data saved to SQLite: {payload}")


# Setup MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start MQTT loop in the background
mqtt_client.loop_start()

# Flask routes

# Trang chủ
@app.route('/')
def index():
    return render_template('index.html', data=data)

# Trang biểu đồ
# @app.route('/chart', methods=['GET'])
# def chart():
#     station_id = request.args.get('station')
#     start_date = request.args.get('start')
#     end_date = request.args.get('end')

#     # Validate input
#     if not station_id or not start_date or not end_date:
#         return render_template('chart.html')

#     station_id = station_id.split(' ')[1]  # Parse station name
#     filtered_data = df[
#         (df['name'] == int(station_id)) &
#         (df['month_data'] >= start_date) &
#         (df['month_data'] <= end_date)
#     ]

#     # Prepare and save charts
#     features = ["lightIntensity", "rainLevel", "temperature", "humidity", 
#                 "pressure", "windSpeed"]
#     save_path = "static/charts"
#     os.makedirs(save_path, exist_ok=True)  # Create folder if not exists

#     chart_paths = {}
#     for feature in features:
#         if feature in filtered_data:
#             labels = filtered_data["month_data"].tolist()
#             values = filtered_data[feature].tolist()

#             # Plot chart
#             fig, ax = plt.subplots()
#             ax.plot(labels, values, marker='o', label=feature, color='blue')
#             ax.set_xlabel('Date')
#             ax.set_ylabel(f'{feature} Value')
#             ax.set_title(f'{feature} Over Time')
#             ax.legend()
#             ax.grid()

#             # Save the chart to file
#             file_name = f"{feature}.png"
#             file_path = os.path.join(save_path, file_name)
#             fig.savefig(file_path)
#             plt.close(fig)  # Release memory

#             chart_paths[feature] = file_name  # Add to response

#     return jsonify(chart_paths), 200
@app.route('/chart', methods=['GET'])
def chart():
    station_id = request.args.get('station')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    if not station_id or not start_date or not end_date:
        return render_template('chart.html')

    # Handle potential missing space or unexpected format in station_id
    if ' ' in station_id:
        station_id = station_id.split(' ')[1]  # Parse station name
    else:
        # If no space is found, use the station_id as is (or handle appropriately)
        pass

    # Convert to datetime
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Debugging output
    print(f"Filtering data for station: {station_id}")
    print(f"Start Date: {start_date}, End Date: {end_date}")

    # Query for the station's data
    station_data = WeatherData.query.filter(WeatherData.station_name == station_id).all()

    if not station_data:
        return jsonify({"error": "No data found for the selected station."}), 400

    # Debugging: print the timestamps in the data
    timestamps = [entry.timestamp for entry in station_data]
    print(f"Available timestamps: {timestamps}")

    # Filter data within the specified range
    filtered_data = WeatherData.query.filter(
        WeatherData.station_name == station_id,
        WeatherData.timestamp >= start_date,
        WeatherData.timestamp <= end_date
    ).all()

    if not filtered_data:
        return jsonify({"error": "No data found for the selected date range."}), 400

    # Process and return the charts as before
    data_dict = [{
        'timestamp': entry.timestamp,
        'lightIntensity': entry.lightIntensity,
        'rainLevel': entry.rainLevel,
        'temperature': entry.temperature,
        'humidity': entry.humidity,
        'pressure': entry.pressure,
        'windSpeed': entry.windSpeed,
        'windDirection': entry.windDirection
    } for entry in filtered_data]

    station_df = pd.DataFrame(data_dict)

    # Select 10 equally spaced time points within the date range
    time_points = pd.date_range(start=start_date, end=end_date, periods=10)
    filtered_data = station_df[station_df['timestamp'].isin(time_points)]

    # Debugging: print filtered data
    print(f"Filtered data: {filtered_data}")

    # Create charts as before
    features = ["lightIntensity", "rainLevel", "temperature", "humidity", 
                "pressure", "windSpeed"]
    save_path = "static/charts"
    os.makedirs(save_path, exist_ok=True)

    chart_paths = {}
    for feature in features:
        if feature in filtered_data:
            labels = filtered_data["timestamp"].tolist()
            values = filtered_data[feature].tolist()

            # Generate chart
            fig, ax = plt.subplots()
            ax.plot(labels, values, marker='o', label=feature, color='blue')
            ax.set_xlabel('Date')
            ax.set_ylabel(f'{feature} Value')
            ax.set_title(f'{feature} Over Time')
            ax.legend()
            ax.grid()

            # Save chart image
            file_name = f"{feature}.png"
            file_path = os.path.join(save_path, file_name)
            fig.savefig(file_path)
            plt.close(fig)

            chart_paths[feature] = file_name

    return jsonify(chart_paths), 200

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Trang phân tích dữ liệu
@app.route('/analysis')
def analysis():
    month = request.args.get('month')
    year = request.args.get('year')
    if month is None or year is None:
        file_path = "static/output_analysis.txt"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write('')
        return render_template('analysis.html')
    # Phân tích theo tháng-năm
    if month == 'All Months':
        temp = df[df['month_data'].str.contains(year)]
    else:
        temp = df[df['month_data'].str.contains(f"{year}-{month}")]
    genai.configure(api_key="AIzaSyAm8V4F1i_oeF9PCfjwin0gUrfHcRxcV8Q")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"Analyze the weather data of the station: {temp.to_string()}", )
    print(response.text)

        # Lưu nội dung trả về vào file .txt
    output_text = response.text
    file_path = "static/output_analysis.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(output_text)
    return render_template('analysis.html')

@app.route('/all_data')
def all_data():
    # Truy vấn tất cả dữ liệu từ bảng WeatherData
    weather_data = WeatherData.query.all()

    # Chuyển dữ liệu thành một danh sách dictionary để dễ hiển thị
    data_dict = [{
        'id': entry.id,
        'station_name': entry.station_name,
        'lightIntensity': entry.lightIntensity,
        'rainLevel': entry.rainLevel,
        'temperature': entry.temperature,
        'humidity': entry.humidity,
        'pressure': entry.pressure,
        'windSpeed': entry.windSpeed,
        'windDirection': entry.windDirection,
        'timestamp': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for entry in weather_data]

    # Trả về dữ liệu dưới dạng bảng HTML
    return render_template('all_data.html', data=data_dict)

# API route to handle receiving data
@app.route('/data', methods=['POST'])
def receive_data():
    try:
        received_data = request.get_json()
        if not received_data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        print(f"Received Data: {json.dumps(received_data, indent=4)}")

        station = received_data.get('station', '')
        if station:
            if station not in data:
                data[station] = {}

            # Cập nhật dữ liệu nhận được
            data[station].update({
                "lightIntensity": received_data.get("lightIntensity"),
                "rainLevel": received_data.get("rainLevel"),
                "temperature": received_data.get("temperature"),
                "humidity": received_data.get("humidity"),
                "pressure": received_data.get("pressure"),
                "windSpeed": received_data.get("windSpeed"),
                "windDirection": received_data.get("windDirection"),
            })

            # Gửi cập nhật tới client qua WebSocket
            socketio.emit('update', data)

        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/clear_data', methods=['POST'])
def clear_data():
    try:
        # Lấy tham số xác nhận từ form (thông qua request.form)
        confirm = request.form.get('confirm')  
        
        if confirm != 'true':
            return jsonify({"status": "error", "message": "Data deletion not confirmed."}), 400

        # Xóa tất cả dữ liệu trong bảng WeatherData
        db.session.query(WeatherData).delete()
        db.session.commit()

        return jsonify({"status": "success", "message": "All data has been deleted."}), 200
    except Exception as e:
        db.session.rollback()  # Rollback nếu có lỗi
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/clear_data_page')
def clear_data_page():
    return render_template('clear_data.html')

if __name__ == "__main__":
    df = pd.read_csv("weather.csv", delimiter=",")
    socketio.run(app, debug=True, host="0.0.0.0", port=8000)
