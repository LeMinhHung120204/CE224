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

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Data storage for the web app
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
    # topic = msg.topic
    # payload = msg.payload.decode("utf-8")
    # print(f"Received message '{payload}' on topic '{topic}'")

    payload = msg.payload.decode("utf-8")  # Giải mã payload (dạng chuỗi)
    payload = payload.split('#')
    features = [
        "lightIntensity", 
        "rainLevel",
        "temperature",
        "humidity",
        "pressure",
        "windSpeed",
        "windDirection",
        "rainFlowRate"
    ]
    data["name"].append(data["name"][-1] + 1)
    current_date = datetime.now().strftime("%Y-%m-%d")
    data["month_data"].append(current_date)
    for i, f in enumerate(features):
        data[f].append(payload[i])
    pd.DataFrame(data).to_csv('weather.csv', index=False, mode='a', header=False)
    

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
@app.route('/chart', methods=['GET'])
def chart():
    # Lấy tham số từ query string
    station_id = request.args.get('station')
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    print(station_id, start_date, end_date)
    # Nếu không có tham số, trả về JSON trống
    # Xóa các file trong thư mục static/charts
    save_path = "static/charts"
    if os.path.exists(save_path):
        files = glob.glob(os.path.join(save_path, "*.png"))
        for file in files:
            os.remove(file)  # Xóa từng file .png
    if not station_id or not start_date or not end_date:
        return render_template('chart.html')
    station_id = station_id.split(' ')[1]
    data = df[df['name'] == int(station_id)].to_dict()
    print(station_id)

    # Nếu có tham số, xử lý logic để tạo biểu đồ
    features = ["lightIntensity", "rainLevel", "temperature", "humidity", 
                "pressure", "windSpeed", "rainFlowRate"]
    charts = {}
    save_path = "static/charts"  # Đường dẫn thư mục để lưu biểu đồ
    os.makedirs(save_path, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

    for feature in features:
        if feature in data:
            month_data = data["month_data"]
            feature_values = data[feature]

            # Chuyển đổi dữ liệu thành danh sách
            labels = list(map(str, month_data.values()))
            values = list(map(float, feature_values.values()))

            # Tạo biểu đồ Matplotlib
            fig, ax = plt.subplots()
            ax.plot(labels, values, marker='o', label=feature, color='blue')
            ax.set_xlabel('Date')
            ax.set_ylabel(f'{feature} Value')
            ax.set_title(f'{feature} Over Time')
            ax.legend()
            ax.grid()

            # Lưu biểu đồ vào file
            file_path = os.path.join(save_path, f"{feature}.png")
            fig.savefig(file_path, format='png')

            # Mã hóa Base64 để nhúng vào JSON
            img = io.BytesIO()
            fig.savefig(img, format='png')
            img.seek(0)
            # charts[feature] = base64.b64encode(img.getvalue()).decode('utf-8')

            #plt.close(fig)  # Giải phóng bộ nhớ
    print('ábd')
    # Trả về dữ liệu JSON và lưu biểu đồ
    return render_template('chart.html')

    # return jsonify(charts), 200

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

if __name__ == "__main__":
    df = pd.read_csv("weather.csv", delimiter=",")
    socketio.run(app, debug=True, host="0.0.0.0", port=8000)
