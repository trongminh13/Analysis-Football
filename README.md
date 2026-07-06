# AI Football Match Analysis

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-yellow?logo=ultralytics&logoColor=black)

Đây là dự án cá nhân áp dụng Computer Vision và Deep Learning để phân tích dữ liệu từ video các trận đấu bóng đá. Hệ thống tự động nhận diện cầu thủ, theo dõi chuyển động, phân loại đội bóng và tính toán các chỉ số như tốc độ hay quãng đường di chuyển.

## Các tính năng chính

* **Object Detection & Tracking:** Sử dụng YOLOv8 (đã fine-tune) kết hợp với ByteTrack để nhận diện và theo dõi cầu thủ, trọng tài, và quả bóng.
* **Camera Movement Compensation:** Dùng thuật toán Lucas-Kanade Optical Flow để tính toán và bù trừ độ rung lắc, di chuyển của camera, giúp tọa độ tracking không bị lệch khi góc máy quay thay đổi.
* **Perspective Transformation:** Ánh xạ tọa độ 2D từ camera (pixel) sang mặt phẳng 2D thực tế của sân bóng (mét) bằng `cv2.getPerspectiveTransform`.
* **Speed & Distance Estimation:** Dựa trên hệ tọa độ mặt sân để đo lường vận tốc tức thời (km/h) và tổng quãng đường di chuyển (m) của từng cầu thủ.
* **Team Assignment:** Áp dụng K-Means Clustering lên các pixel màu áo để tự động phân nhóm cầu thủ thành 2 đội hình.
* **Ball Possession:** Tính toán khoảng cách để xác định xem cầu thủ nào đang ở gần và kiểm soát bóng nhất.

## Tổng quan cấu trúc thư mục

* `trackers/`: Xử lý detection (YOLOv8) và tracking (ByteTrack). Bao gồm cả logic nội suy (interpolate) vị trí bóng bằng `pandas` ở những frame bị mất dấu.
* `camera_movement_estimator/`: Tính toán vector dịch chuyển của camera bằng Optical Flow.
* `view_transformer/`: Logic xử lý phép biến đổi phối cảnh từ pixel sang mét.
* `speed_and_distance_estimator/`: Tính toán thông số vật lý (tốc độ, quãng đường chạy).
* `team_assigner/`: Phân loại đội hình dựa trên màu áo đấu.
* `player_ball_assigner/`: Gán trạng thái kiểm soát bóng.
* `stubs/`: Chứa các file `.pkl` dùng để cache lại kết quả tracking (đỡ phải chạy lại inference mỗi lần test code).
* `main.py`: Entry point kết nối toàn bộ pipeline.

## Hướng dẫn chạy dự án

**1. Cài đặt thư viện:**
Dự án yêu cầu Python >= 3.8. Bạn có thể cài đặt các package cần thiết bằng lệnh:
```bash
pip install ultralytics supervision opencv-python numpy pandas scikit-learn
```

**2. Trọng số mô hình:**
Hãy đảm bảo bạn đã copy file trọng số mô hình YOLO (ví dụ: `best.pt`) vào thư mục `models/`.

**3. Khởi chạy:**
Đặt video đầu vào của bạn tại `input_videos/football-video.mp4` và chạy:
```bash
python main.py
```

*Lưu ý nhỏ: Lần chạy đầu tiên sẽ khá tốn thời gian vì model phải detect từng frame. Tuy nhiên, kết quả sẽ được cache vào thư mục `stubs/`, nên những lần chạy sau để debug vẽ vời các thứ sẽ lấy thẳng từ cache lên rất nhanh. Video kết quả cuối cùng nằm trong thư mục `output_videos/`.*