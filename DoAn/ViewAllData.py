from flask import Flask, jsonify
from server import db, WeatherData

app = Flask(__name__)

@app.route('/view_all_data', methods=['GET'])
def view_all_data():
    all_records = WeatherData.query.all()  # Lấy tất cả các bản ghi
    result = []
    for record in all_records:
        result.append({
            "station": record.station_name,
            "lightIntensity": record.lightIntensity,
            "rainLevel": record.rainLevel,
            "temperature": record.temperature,
            "humidity": record.humidity,
            "pressure": record.pressure,
            "windSpeed": record.windSpeed,
            "windDirection": record.windDirection,
            "timestamp": record.timestamp.strftime('%Y-%m-%d %H:%M:%S')  # Định dạng lại timestamp
        })
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
