import paho.mqtt.client as mqtt
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import base64
import matplotlib.pyplot as plt
import io
from datetime import datetime
import openai  # Import OpenAI library
import numpy as np 
import pandas as pd
import os

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

    # Nếu không có tham số, trả về JSON trống
    if not station_id or not start_date or not end_date:
        return render_template('chart.html', charts={})

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
            charts[feature] = base64.b64encode(img.getvalue()).decode('utf-8')

            plt.close(fig)  # Giải phóng bộ nhớ

    # Trả về dữ liệu JSON và lưu biểu đồ
    return render_template('chart.html', charts=charts)

    # return jsonify(charts), 200



# Add your OpenAI API key
openai.api_key = ""

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        request_data = request.get_json()
        option = request_data.get('option', '')
        custom_query = request_data.get('query', '')

        # Predefined analysis prompts
        prompts = {
            "average_temperature": "Analyze the average temperature data for the selected station over the past month.",
            "rain_trends": "Provide an analysis of the rainfall trends for the selected station.",
            "wind_analysis": "Discuss the wind speed and direction trends for the selected station.",
        }

        # Choose the appropriate prompt
        if option == "custom" and custom_query:
            prompt = custom_query
        else:
            prompt = prompts.get(option, "Provide a general analysis of the station's data.")

        # Generate response using ChatGPT
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=200,
            temperature=0.7,
        )

        result = response.choices[0].text.strip()
        return jsonify({"result": result})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

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
    data = df.to_dict()
    print(data["month_data"])
    # print(df.columns)
    socketio.run(app, debug=True, host="0.0.0.0", port=8000)
