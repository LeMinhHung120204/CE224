document.addEventListener("DOMContentLoaded", () => {
    const socket = io();
    const tableBody = document.getElementById('data-table-body');

    socket.on('update', (stations) => {
        tableBody.innerHTML = ''; // Xóa nội dung cũ

        for (const [station, details] of Object.entries(stations)) {
            const row = `
                <div class="row">
                    <div class="cell">${station}</div>
                    <div class="cell">${details.lightIntensity || "N/A"} lux</div>
                    <div class="cell">${details.rainLevel || "N/A"} mm</div>
                    <div class="cell">${details.temperature || "N/A"} °C</div>
                    <div class="cell">${details.humidity || "N/A"} %</div>
                    <div class="cell">${details.pressure || "N/A"} hPa</div>
                    <div class="cell">${details.windSpeed || "N/A"} m/s</div>
                    <div class="cell">${details.windDirection || "N/A"} °</div>
                </div>`;
            tableBody.innerHTML += row;
        }
    });
});
