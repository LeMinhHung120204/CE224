# CE224
Thiết kế trạm quan trắc môi trường

Giới thiệu

Dự án "Thiết kế trạm quan trắc môi trường" là một hệ thống giám sát môi trường, bao gồm giao diện web để hiển thị và phân tích dữ liệu từ các trạm quan trắc. Người dùng có thể xem dữ liệu biểu đồ, thực hiện phân tích theo tháng và năm, cũng như tải về kết quả phân tích.

Hướng dẫn sử dụng

1. Yêu cầu hệ thống

Python 3.8 hoặc phiên bản mới hơn

Hệ điều hành: Windows, macOS, hoặc Linux

Cài đặt pip (Python Package Installer)

2. Cài đặt thư viện

Đảm bảo bạn đã cài đặt Python và pip.

Mở terminal hoặc command prompt, chuyển đến thư mục chứa dự án.

Chạy lệnh sau để cài đặt các thư viện cần thiết:

pip install -r requirements.txt

3. Khởi động server

Đảm bảo bạn đang ở trong thư mục chứa file server.py.

Chạy lệnh sau để khởi động server:

python server.py

Sau khi server khởi động thành công, mở trình duyệt web và truy cập vào địa chỉ:

http://127.0.0.1:5000

4. Chức năng chính

Trang Home: Hiển thị tổng quan hệ thống.

Trang Chart: Xem biểu đồ dữ liệu từ các trạm quan trắc.

Trang Analysis: Phân tích dữ liệu theo tháng và năm, hiển thị kết quả từ file phân tích.

5. Lưu ý

File dữ liệu phân tích được lưu tại thư mục static/output_analysis.txt sau khi hoàn thành phân tích.

Đảm bảo file requirements.txt được cập nhật đầy đủ trước khi cài đặt thư viện.

Thông tin thêm

Nếu bạn gặp vấn đề hoặc cần thêm thông tin, vui lòng liên hệ qua email hỗ trợ của nhóm phát triển.