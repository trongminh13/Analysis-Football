# 🏟️ AI Football Match Analysis System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-yellow?logo=ultralytics&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-blue)

Dự án **AI Football Match Analysis** là một hệ thống ứng dụng Computer Vision (Thị giác máy tính) và Trí tuệ nhân tạo (AI) end-to-end để phân tích toàn diện các trận đấu bóng đá từ video. Hệ thống không chỉ dừng lại ở việc nhận diện cầu thủ, mà còn đi sâu vào phân tích các chỉ số thực tế trên sân cỏ như tốc độ di chuyển, quãng đường đã chạy, tỷ lệ kiểm soát bóng, và tự động phân biệt đội hình.

---

## 🌟 Kiến Trúc Hệ Thống (Pipeline)

Hệ thống hoạt động theo một luồng dữ liệu liên tục qua nhiều module chuyên biệt:

1. **Video Đầu Vào** được chia thành các khung hình (frames).
2. **YOLOv8 + ByteTrack** nhận diện và theo dõi quỹ đạo của cầu thủ, trọng tài và bóng.
3. **Camera Movement Estimator** tính toán và bù trừ độ rung lắc/lia của camera.
4. **View Transformer** chiếu tọa độ pixel trên video xuống mặt phẳng 2D của sân (đơn vị: mét).
5. **Speed & Distance Estimator** dựa vào tọa độ đã chiếu để tính toán tốc độ (km/h) và quãng đường (m).
6. **Team Assigner** phân tích màu áo bằng thuật toán gom cụm để chia cầu thủ vào 2 đội.
7. **Player Ball Assigner** gán quyền kiểm soát bóng cho cầu thủ gần nhất.
8. **Video Đầu Ra** được vẽ đè (annotate) các thông số trực quan lên từng khung hình.

---

## 🧩 Phân Tích Các Module Chính

### 1. 🔍 Object Detection & Tracking (`trackers/`)
- Sử dụng mô hình **YOLOv8** đã được fine-tune để phát hiện 4 class: `player`, `referee`, `ball`, `goalkeeper` (thủ môn được gộp chung vào player).
- Tích hợp **ByteTrack** từ thư viện `supervision` để cấp phát ID cho các đối tượng, đảm bảo quỹ đạo di chuyển (track) không bị đứt đoạn ngay cả khi cầu thủ chuyển động nhanh hoặc bị che khuất.
- **Ball Interpolation:** Nội suy vị trí bóng bằng `pandas` ở những khung hình mô hình không nhận diện được bóng do bị khuất hoặc tốc độ bay quá nhanh.

### 2. 📷 Camera Movement Estimator (`camera_movement_estimator/`)
- Cầu thủ di chuyển trên sân nhưng camera cũng di chuyển (pan/tilt) theo bóng. Nếu chỉ tính tọa độ pixel, việc tính toán tốc độ sẽ sai lệch hoàn toàn.
- Hệ thống dùng thuật toán **Lucas-Kanade Optical Flow** trích xuất các điểm đặc trưng (features) đứng yên ở rìa sân để tính toán vector di chuyển của camera, sau đó **bù trừ (compensate)** vector này vào tọa độ của cầu thủ.

### 3. 🔄 View Transformer (`view_transformer/`)
- Bầu trời và góc quay camera tạo ra phối cảnh nghiêng (perspective).
- Chức năng này sử dụng `cv2.getPerspectiveTransform` để thực hiện phép biến đổi phối cảnh, ánh xạ tọa độ pixel của chân cầu thủ sang hệ trục tọa độ 2D thực tế trên mặt sân với kích thước chuẩn (đơn vị: mét).

### 4. ⚡ Speed & Distance Estimator (`speed_and_distance_estimator/`)
- Sau khi có tọa độ thực tế (tính bằng mét) từ View Transformer, module này sẽ đo khoảng cách giữa 2 tọa độ của cầu thủ trong 1 khoảng thời gian (dựa trên framerate).
- Tính toán ra **Quãng đường tổng (m)** và **Vận tốc tức thời (km/h)** của từng cầu thủ, giúp huấn luyện viên phân tích thể lực.

### 5. 👕 Team Assigner (`team_assigner/`)
- Cắt (crop) bounding box của từng cầu thủ, trích xuất nửa thân trên (áo đấu).
- Chạy thuật toán **K-Means Clustering (k=2)** trên toàn bộ pixel của áo để loại bỏ màu nền sân cỏ, sau đó tiếp tục gom cụm toàn bộ cầu thủ vào 2 nhóm màu áo khác nhau (Team 1 & Team 2).

### 6. 🏃 Player Ball Possession (`player_ball_assigner/`)
- Tính toán khoảng cách Euclidean từ tâm bóng đến chân của các cầu thủ. Nếu khoảng cách nằm trong ngưỡng cho phép (threshold), cầu thủ đó được xác định là đang giữ bóng.
- Từ đó tổng hợp lại **Tỷ lệ kiểm soát bóng (%)** của mỗi đội.

---

## 📂 Cấu Trúc Thư Mục

```text
Analysis-Football/
├── main.py                          # File thực thi chính của pipeline
├── yolov8x.pt                       # Trọng số mô hình YOLO gốc
├── models/                          # Trọng số mô hình đã được huấn luyện riêng (best.pt)
├── trackers/                        # Chứa logic YOLO detection, ByteTrack và nội suy bóng
├── team_assigner/                   # Logic phân nhóm đội dựa trên K-Means màu áo
├── player_ball_assigner/            # Logic tính toán cầu thủ nào đang cầm bóng
├── camera_movement_estimator/       # Logic Optical Flow để bù trừ chuyển động máy quay
├── view_transformer/                # Logic Perspective Transform đổi góc nhìn 3D sang 2D sân
├── speed_and_distance_estimator/    # Logic vật lý tính km/h và quãng đường mét
├── utils/                           # Các hàm hỗ trợ (Bounding box, I/O video)
├── stubs/                           # Chứa các file pkl lưu cache tracking để khỏi chạy lại YOLO
├── input_videos/                    # Video thô đầu vào
├── output_videos/                   # Video đầu ra sau khi đã vẽ các thông số (annotated)
├── training/                        # Các tệp jupyter notebook dùng để train mô hình
└── development_and_analysis/        # Notebook phân tích màu sắc, thử nghiệm logic
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Chuẩn bị môi trường (Prerequisites)
Yêu cầu Python >= 3.8. Cài đặt các thư viện lõi:

```bash
pip install ultralytics supervision opencv-python numpy pandas scikit-learn
```

### 2. Chuẩn bị trọng số mô hình
Chắc chắn bạn có mô hình đã train (ví dụ: `best.pt`) đặt trong thư mục `models/`. 

### 3. Thực thi Pipeline
Đưa video cần phân tích vào thư mục `input_videos/`. Ví dụ: `football-video.mp4`.
Mở file `main.py` và chạy lệnh:

```bash
python main.py
```

- Lần chạy đầu tiên sẽ tốn thời gian để mô hình YOLO detect toàn bộ khung hình.
- Các lần chạy sau hệ thống sẽ đọc từ file cache (`stubs/track_stubs.pkl`) giúp việc render diễn ra vô cùng nhanh chóng.
- Video kết quả sẽ được tạo ra tại thư mục `output_videos/`.

---
*Dự án được xây dựng với mục tiêu ứng dụng AI vào phân tích thể thao chuyên nghiệp.*