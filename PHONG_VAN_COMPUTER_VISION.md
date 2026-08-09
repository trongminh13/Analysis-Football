============================================================
TÀI LIỆU ÔN PHỎNG VẤN COMPUTER VISION
DỰ ÁN: AI FOOTBALL MATCH ANALYSIS
Định hướng liên hệ: Computer Vision cho công trình và bản vẽ
============================================================

MỤC ĐÍCH CỦA TÀI LIỆU

Tài liệu này giúp trình bày đúng những gì dự án hiện có, hiểu bản chất
kỹ thuật đằng sau code, trả lời các câu hỏi đào sâu, và liên hệ kinh
nghiệm của dự án với bài toán Computer Vision trong xây dựng/bản vẽ.

Quy tắc quan trọng khi phỏng vấn:

1. Phân biệt rõ "đã làm", "đang là hạn chế" và "hướng cải tiến".
2. Không nói hệ thống production-ready vì repo hiện là prototype.
3. Không nói tốc độ/khoảng cách chính xác tuyệt đối. Đây là ước lượng.
4. Không nói ball possession là ground truth. Đây là heuristic khoảng cách.
5. README ghi YOLOv8 nhưng artifact train ghi yolov5x.pt. Phải nói rõ sự
   không đồng nhất này nếu được hỏi.
6. Khi không biết, trình bày giả thuyết, cách kiểm chứng và metric sẽ dùng.


# PHẦN 1. GIỚI THIỆU DỰ ÁN

### 1.1. Bài toán

Dự án nhận video một trận bóng đá và tạo ra video phân tích, gồm:

- Phát hiện cầu thủ, thủ môn, trọng tài và bóng.
- Duy trì ID cầu thủ giữa các frame.
- Phân cầu thủ thành hai đội dựa trên màu áo.
- Ước lượng cầu thủ và đội đang kiểm soát bóng.
- Ước lượng chuyển động camera.
- Chuyển tọa độ từ pixel sang tọa độ mặt sân.
- Ước lượng tốc độ và quãng đường của từng cầu thủ.
- Vẽ kết quả lên video đầu ra.

### 1.2. Câu giới thiệu 30 giây

"Đây là dự án Computer Vision phân tích video bóng đá. Em fine-tune một
mô hình YOLO để phát hiện bốn lớp: bóng, thủ môn, cầu thủ và trọng tài,
sau đó dùng ByteTrack để duy trì ID qua thời gian. Em kết hợp Optical
Flow để bù chuyển động camera và Perspective Transformation để đưa tọa
độ pixel về mặt phẳng sân, từ đó ước lượng tốc độ và quãng đường. K-Means
được dùng để phân đội theo màu áo, còn quyền kiểm soát bóng được ước lượng
bằng khoảng cách giữa bóng và chân cầu thủ."

### 1.3. Câu giới thiệu 60-90 giây

"Mục tiêu của dự án là biến video bóng đá thô thành dữ liệu phân tích có
ý nghĩa. Đầu tiên, mô hình YOLO đã fine-tune phát hiện player, goalkeeper,
referee và ball trên từng frame. YOLO chỉ phát hiện độc lập từng ảnh nên
em đưa kết quả qua ByteTrack để liên kết detection và tạo track ID.

Vì camera bóng đá thường pan theo trận đấu, tọa độ pixel không phản ánh
hoàn toàn chuyển động thật. Em dùng Lucas-Kanade Optical Flow để ước lượng
dịch chuyển camera và trừ nó khỏi tọa độ đối tượng. Sau đó em dùng bốn cặp
điểm để tính homography, ánh xạ vị trí từ ảnh phối cảnh sang mặt phẳng sân.
Trên hệ tọa độ này, em tính tốc độ và quãng đường theo cửa sổ nhiều frame.

Phần phân đội dùng K-Means hai cấp: tách màu áo khỏi nền trong crop cầu thủ,
rồi gom màu đại diện thành hai đội. Bóng thường bị mất detection nên em nội
suy các bbox bị thiếu. Cuối cùng hệ thống ước lượng quyền kiểm soát bóng,
vẽ ID, đội, bóng, tốc độ, quãng đường và tỷ lệ kiểm soát lên video. Điểm
em đánh giá cao nhất là sự kết hợp giữa Deep Learning và Computer Vision
hình học trong một pipeline end-to-end."

### 1.4. Điểm sáng nhất

Không nên trả lời đơn giản rằng điểm sáng là "dùng YOLO". Điểm sáng là:

- Kết hợp detection và tracking để biến dự đoán từng frame thành trajectory.
- Hiểu rằng tọa độ pixel chưa đủ để đo chuyển động vật lý.
- Bù camera motion trước khi phân tích chuyển động đối tượng.
- Dùng homography để ánh xạ mặt phẳng ảnh sang mặt phẳng sân.
- Kết hợp Deep Learning, clustering, tracking và geometry.

Câu trả lời mẫu:

"Điểm sáng nhất là pipeline chuyển từ detection trong pixel sang phân tích
chuyển động có ý nghĩa hơn. YOLO cho em bbox, ByteTrack cho em identity theo
thời gian, Optical Flow giảm ảnh hưởng camera, còn homography đưa vị trí về
mặt phẳng sân. Nhờ chuỗi xử lý đó mới có thể ước lượng tốc độ và quãng đường."


# PHẦN 2. LUỒNG HOẠT ĐỘNG END-TO-END

Video đầu vào
    |
    v
OpenCV đọc video thành các frame
    |
    v
YOLO inference theo batch 20 frame
    |
    +--> bbox + class + confidence
    |
    v
Đổi goalkeeper thành player cho logic downstream
    |
    v
ByteTrack liên kết detection --> track_id
    |
    +--> players[frame][id]
    +--> referees[frame][id]
    +--> ball[frame][1]
    |
    v
Nội suy bbox bóng bị thiếu bằng Pandas
    |
    v
Chọn vị trí đại diện
    +--> bóng: tâm bbox
    +--> người: trung điểm cạnh đáy bbox (vị trí chân)
    |
    v
Lucas-Kanade Optical Flow --> camera movement X/Y
    |
    v
position_adjusted = position - camera_movement
    |
    v
Homography/Perspective Transform --> tọa độ mặt sân
    |
    +--> tính tốc độ và quãng đường
    |
    v
K-Means màu áo --> team 1/team 2
    |
    v
Khoảng cách bóng đến chân --> cầu thủ giữ bóng
    |
    v
Tích lũy frame kiểm soát bóng theo đội
    |
    v
Vẽ annotation + ghi video đầu ra

Các biểu diễn dữ liệu quan trọng:

tracks = {
    "players": [
        {
            track_id: {
                "bbox": [x1, y1, x2, y2],
                "position": (x, y),
                "position_adjusted": (x, y),
                "position_transformed": [x_meter, y_meter],
                "team": 1 hoặc 2,
                "team_color": [B, G, R],
                "has_ball": True/False,
                "speed": km/h,
                "distance": mét
            }
        }
    ],
    "referees": [...],
    "ball": [...]
}


# PHẦN 3. BẢN ĐỒ FILE VÀ CHỨC NĂNG

### 3.1. main.py

Vai trò: entry point và orchestration của toàn pipeline.

Các bước:

- read_video('input_videos/football-video.mp4')
- Tracker('models/best.pt')
- tracker.get_object_tracks(...)
- tracker.add_position_to_tracks(...)
- CameraMovementEstimator(...)
- get_camera_movement(...)
- add_adjust_positions_to_tracks(...)
- ViewTransformer().add_transformed_position_to_tracks(...)
- tracker.interpolate_ball_positions(...)
- SpeedAndDistance_Estimator().add_speed_and_distance_to_tracks(...)
- TeamAssigner().assign_team_color(...)
- Gán đội cho từng track.
- PlayerBallAssigner().assign_ball_to_player(...)
- Vẽ annotation.
- Ghi output_videos/output_video.avi.

Điểm cần biết:

- Input/model/cache/output đang hard-code.
- Code giả định video có ít nhất một frame.
- Code giả định frame đầu có đủ cầu thủ để K-Means hai đội.
- Nếu frame đầu không xác định possession, team_ball_control[-1] sẽ lỗi.
- Model, stubs và output directory chưa được đảm bảo tồn tại.

### 3.2. yolo_inference.py

Vai trò: script thử nghiệm đơn giản cho YOLO.

- Load models/best.pt.
- Chạy predict trực tiếp trên video.
- Lưu kết quả bằng tùy chọn save=True.
- In detection/box để debug.

Đây không phải pipeline chính.

### 3.3. utils/video_utils.py

read_video(video_path):

- Dùng cv2.VideoCapture.
- Đọc tuần tự cho tới khi ret=False.
- Mỗi frame là NumPy ndarray có shape (height, width, channels).
- Trả về list frame.

save_video(frames, path):

- Codec XVID.
- Kích thước lấy từ frame đầu.
- Ghi từng frame bằng VideoWriter.
- FPS hiện hard-code 24.

Hạn chế:

- Không kiểm tra cap.isOpened().
- Không release VideoCapture rõ ràng.
- Không kiểm tra VideoWriter mở thành công.
- Giữ toàn bộ video trong RAM.
- Không giữ FPS gốc; video mẫu thực tế là 25 FPS.

### 3.4. utils/bbox_utils.py

get_center_of_bbox(bbox):
    center = ((x1+x2)/2, (y1+y2)/2)

get_bbox_width(bbox):
    width = x2-x1

measure_distance(p1, p2):
    Euclidean distance = sqrt(dx^2 + dy^2)

measure_xy_distance(p1, p2):
    Trả riêng dx, dy.

get_foot_position(bbox):
    ((x1+x2)/2, y2)

Tại sao dùng foot position?

- Bbox center nằm ở thân người, không nằm trên mặt sân.
- Chân gần điểm tiếp xúc với mặt phẳng sân.
- Homography được định nghĩa trên mặt phẳng nên foot point hợp lý hơn.

### 3.5. trackers/tracker.py

Tracker.__init__(model_path):

- Load YOLO bằng Ultralytics.
- Tạo supervision.ByteTrack.

detect_frames(frames):

- Batch size 20.
- Confidence threshold 0.1.
- Cộng output theo đúng thứ tự frame.

get_object_tracks(frames, read_from_stub, stub_path):

- Nếu cache tồn tại thì pickle.load.
- Nếu không thì chạy detection.
- sv.Detections.from_ultralytics chuyển output về cấu trúc Supervision.
- Chuyển class goalkeeper thành player.
- ByteTrack xử lý player/referee.
- Ball lấy trực tiếp từ detection và gán key cố định 1.
- Kết quả có thể pickle.dump để dùng lại.

add_position_to_tracks(tracks):

- Ball dùng bbox center.
- Player/referee dùng bbox foot point.

interpolate_ball_positions(ball_positions):

- Lấy bbox bóng theo từng frame.
- Tạo DataFrame gồm x1, y1, x2, y2.
- interpolate() lấp khoảng trống bên trong.
- bfill() lấp khoảng trống đầu chuỗi.
- Trả về cùng dạng dictionary.

draw_ellipse(...):

- Ellipse dưới chân người.
- Rectangle màu chứa ID.

draw_traingle(...):

- Vẽ tam giác trên bbox bóng hoặc người giữ bóng.
- Tên hàm bị sai chính tả; đúng là draw_triangle.

draw_team_ball_control(...):

- Đếm số frame team_ball_control bằng 1 và 2.
- Chia cho tổng frame đã có possession.
- Vẽ tỷ lệ phần trăm.

draw_annotations(...):

- Copy frame để tránh sửa input trực tiếp.
- Vẽ player, referee, ball và possession.
- Vẽ thống kê ball control.

Rủi ro:

- pickle.load không an toàn với file không tin cậy.
- Cache không có version/fingerprint; đổi video/model vẫn có thể đọc cache cũ.
- Chỉ giữ một bbox bóng cuối cùng nếu detector trả nhiều bóng.
- Không dùng confidence để chọn bbox bóng tốt nhất.
- Detection threshold 0.1 thấp, tăng recall nhưng dễ tăng false positive.
- Nội suy toàn chuỗi có thể tạo vị trí sai nếu mất bóng lâu.

### 3.6. camera_movement_estimator/camera_movement_estimator.py

Mục tiêu: ước lượng chuyển động của camera giữa các frame.

__init__(frame):

- Chuyển frame đầu sang grayscale.
- Tạo mask vùng dùng để tìm feature.
- Cấu hình goodFeaturesToTrack.
- Cấu hình Lucas-Kanade Pyramidal Optical Flow.

get_camera_movement(frames, ...):

- Tìm corner ở frame cũ.
- calcOpticalFlowPyrLK tìm vị trí corner ở frame mới.
- Với từng cặp old/new, tính độ dịch chuyển.
- Code hiện chọn vector có khoảng cách lớn nhất.
- Nếu lớn hơn minimum_distance=5 thì ghi movement.
- Có cache pickle.

add_adjust_positions_to_tracks(...):

    position_adjusted = position - camera_movement

draw_camera_movement(...):

- Vẽ movement X/Y lên góc video.

Nhận xét kỹ thuật:

- Dùng vector lớn nhất không robust; dễ bị outlier hoặc feature trên cầu thủ.
- Cách tốt hơn là lấy median của nhiều flow vector sau khi lọc outlier.
- Có thể dùng RANSAC để estimate affine transform/homography.
- Code chỉ mô hình hóa translation X/Y, chưa mô hình hóa zoom/rotation.
- Mask hard-code theo độ phân giải/góc quay 1920x1080.
- Cần kiểm tra old_features/new_features/status có None hay không.

### 3.7. view_transformer/view_transformer.py

Mục tiêu: chuyển điểm pixel thành điểm trên mặt phẳng sân.

__init__():

- pixel_vertices: bốn điểm trong ảnh.
- target_vertices: bốn điểm tương ứng trên sân.
- cv2.getPerspectiveTransform tạo ma trận 3x3.

transform_point(point):

- pointPolygonTest kiểm tra điểm có trong vùng calibration.
- cv2.perspectiveTransform thực hiện phép biến đổi.
- Ngoài polygon thì trả None.

add_transformed_position_to_tracks(tracks):

- Chuyển position_adjusted của mọi detection.
- Lưu position_transformed.

Kiến thức cần nói:

Homography mô tả quan hệ projective giữa hai mặt phẳng:

    s * [x', y', 1]^T = H * [x, y, 1]^T

H là ma trận 3x3, chỉ xác định tới một hệ số scale nên có 8 bậc tự do.
Mỗi cặp điểm cho hai phương trình, vì vậy tối thiểu cần bốn cặp điểm
không thẳng hàng.

Điều kiện áp dụng:

- Các điểm cần ánh xạ nằm trên hoặc gần cùng một mặt phẳng.
- Với cầu thủ, dùng chân vì chân tiếp xúc mặt sân.
- Vật thể cao không thể biến đổi toàn bbox như một vật thể phẳng.

Hạn chế:

- Calibration hard-code theo video mẫu.
- Camera zoom/đổi góc làm H cố định mất chính xác.
- Tên court_length=23.32 cần giải thích; nó chỉ đại diện vùng sân đã chọn,
  không phải toàn bộ chiều dài tiêu chuẩn của sân bóng.

### 3.8. team_assigner/team_assigner.py

get_clustering_model(image):

- Reshape HxWx3 thành Nx3.
- K-Means n_clusters=2.
- Hai cluster kỳ vọng là foreground áo và background.

get_player_color(frame, bbox):

- Crop bbox cầu thủ.
- Chỉ lấy nửa trên.
- K-Means pixel thành hai cluster.
- Nhìn cluster ở bốn góc để đoán background.
- Cluster còn lại được coi là màu áo.
- Trả cluster center RGB/BGR đại diện màu áo.

assign_team_color(frame, player_detections):

- Thu màu áo của tất cả player trong frame đầu.
- K-Means lần hai với n_clusters=2.
- Hai centroid là màu hai đội.

get_player_team(frame, bbox, player_id):

- Nếu player_id đã có đội thì dùng cache.
- Nếu chưa, trích màu và predict cluster.
- Code có workaround player_id==91 ép team=1.

Điểm tốt:

- Không cần label riêng cho team.
- Unsupervised, dễ áp dụng cho một trận mới.
- Cache theo track ID giảm chi phí.

Hạn chế/cải tiến:

- Crop phải được clamp vào biên ảnh.
- Crop rỗng sẽ làm K-Means lỗi.
- Frame đầu có dưới hai player sẽ lỗi.
- RGB/BGR nhạy với ánh sáng; HSV hoặc CIE Lab có thể tốt hơn.
- Có thể mask vùng người bằng segmentation trước khi lấy màu.
- Có thể lấy median màu qua nhiều frame rồi majority vote.
- Có thể dùng embedding/Re-ID nếu hai đội có áo tương tự.
- Workaround ID 91 phải loại bỏ.

### 3.9. player_ball_assigner/player_ball_assigner.py

assign_ball_to_player(players, ball_bbox):

- Lấy tâm bóng.
- Với mỗi bbox người, lấy góc chân trái (x1,y2) và chân phải (x2,y2).
- Tính khoảng cách từ bóng tới hai điểm.
- Lấy khoảng cách nhỏ hơn.
- Chọn player gần nhất trong ngưỡng 70 pixel.

Đây là heuristic, không phải nhận biết possession theo ngữ nghĩa.

Cải tiến:

- Đo khoảng cách sau homography bằng mét thay vì pixel.
- Dùng khoảng cách đến đoạn chân/bottom-center.
- Dùng vận tốc và hướng bóng.
- Temporal smoothing: phải gần bóng N frame liên tục.
- Thêm trạng thái loose ball/unknown.
- HMM/Kalman/logic state machine để tránh possession nhảy liên tục.

### 3.10. speed_and_distance_estimator/speed_and_distance_estimator.py

add_speed_and_distance_to_tracks(tracks):

- Bỏ ball và referees.
- frame_window=5.
- Với một track tồn tại ở đầu/cuối cửa sổ:
    distance = Euclidean(start_position, end_position)
    time = frame_delta / FPS
    speed_mps = distance / time
    speed_kph = speed_mps * 3.6
- Cộng dồn distance theo track_id.
- Gắn speed/distance vào các frame trong cửa sổ.

draw_speed_and_distance(...):

- Vẽ km/h và mét ở dưới bbox.

Vấn đề:

- FPS hard-code 24, video mẫu là 25.
- Frame cuối có thể không được gắn metric do range không gồm last_frame.
- Nếu track mất ở đúng điểm cuối cửa sổ thì bỏ cả đoạn.
- Track ID switch làm tổng distance của một người bị chia hoặc trộn.
- Không lọc speed phi thực tế.
- import skimage.measure nhưng không dùng.

### 3.11. training/football_training_yolo_v5.ipynb

- Cài ultralytics và roboflow.
- Tải dataset từ Roboflow.
- Train command dùng model=yolov5x.pt.
- epochs=100, imgsz=640.

### 3.12. training/football-players-detection-1/data.yaml

- nc=4.
- names: ball, goalkeeper, player, referee.
- Dataset Roboflow, license CC BY 4.0.
- Khai báo train/valid/test.

### 3.13. training/runs/detect/train7

Chứa artifact:

- args.yaml: cấu hình train.
- results.csv/results.png: loss và metric qua epoch.
- confusion_matrix*.png: confusion matrix.
- PR/P/R/F1 curve.
- batch labels/pred: ảnh trực quan ground truth và prediction.

Thông số train được ghi nhận:

- Base checkpoint: yolov5x.pt.
- Epoch: 100.
- Batch: 4.
- Image size: 640.
- Pretrained: true.
- AMP: true.
- Seed: 0.
- Validation: true.
- Augmentation có HSV, translate, scale, horizontal flip, mosaic.

Kết quả epoch 100 trong results.csv:

- Precision: khoảng 0.8985.
- Recall: khoảng 0.7567.
- mAP@0.5: khoảng 0.8380.
- mAP@0.5:0.95: khoảng 0.5966.

Không nên chỉ đọc metric epoch cuối. Khi báo cáo chính thức cần lấy epoch
best checkpoint và metric trên test set độc lập.

### 3.14. development_and_analysis/color_assignement.ipynb

Notebook thử nghiệm ý tưởng K-Means màu áo:

- Crop một player.
- Chọn nửa trên.
- Cluster pixel thành hai nhóm.
- Dùng góc ảnh để tìm background.
- Lấy centroid còn lại làm màu áo.

Notebook có chuỗi thừa/sai cú pháp hiển thị "0904648928plt.show()", nên cần
làm sạch trước khi dùng làm tài liệu trình bày.

### 3.15. create_interview_deck.py

Vai trò: Script tự động tạo slide PowerPoint phỏng vấn.

- Dùng thư viện python-pptx.
- Tự động hóa layout, màu sắc, font chữ và xuất ra file
  Do_Trong_Minh_Applied_AI_Interview_Deck.pptx.
- Có chứa speaker notes (lời thoại) chi tiết cho từng slide.
- Nằm trong thư mục gốc dự án nhưng không thuộc pipeline AI chính.
- Điểm cộng: chứng minh khả năng viết script tự động hóa công việc.

### 3.16. README.md

Vai trò: Bộ mặt của dự án trên Github.

- Mục đích: Hướng dẫn cài đặt, giới thiệu kiến trúc, mô tả chức năng.
- Hạn chế hiện tại: Chứa nợ kỹ thuật (ghi YOLOv8 nhưng train bằng YOLOv5),
  chưa có instruction rõ ràng để người khác clone-and-run dễ dàng.
- Cần cập nhật đồng bộ với cấu trúc thực tế trước khi gửi link cho NTD.

### 3.17. TU_VUNG_PHONG_VAN_APPLIED_AI_CV_AEC.txt

Vai trò: Tài liệu cá nhân phục vụ ôn thi phỏng vấn.

- Chứa từ vựng tiếng Anh chuyên ngành CV và AEC (Architecture, Engineering, Construction).
- Dung lượng khá lớn (~121KB).
- Không thuộc logic code, nên bỏ qua hoặc đưa vào `.gitignore` nếu dọn dẹp repo
  để tránh làm rối người đọc code.

# PHẦN 4. THƯ VIỆN VÀ LÝ DO SỬ DỤNG

OpenCV (cv2):

- VideoCapture/VideoWriter.
- cvtColor.
- goodFeaturesToTrack.
- calcOpticalFlowPyrLK.
- getPerspectiveTransform/perspectiveTransform.
- pointPolygonTest.
- Vẽ shape và text.

Ultralytics:

- Load YOLO checkpoint.
- Inference image/video/batch.
- Output bbox/class/confidence.

Supervision:

- Chuyển Ultralytics output thành Detections.
- ByteTrack để association và track ID.

NumPy:

- Frame/matrix/point/polygon.
- Vector và array operation.
- Mảng team_ball_control.

Pandas:

- DataFrame bốn tọa độ bbox bóng.
- Nội suy dữ liệu thiếu theo thời gian.

Scikit-learn:

- KMeans cho foreground/background màu áo.
- KMeans cho hai đội.

Pickle:

- Cache object Python.
- Nhanh và tiện trong prototype.
- Không an toàn với nguồn không đáng tin; không phải format trao đổi production.

Matplotlib:

- Chỉ dùng trong notebook để trực quan ảnh và cluster.

Roboflow:

- Nguồn/quản lý dataset trong notebook train.


# PHẦN 5. KIẾN THỨC OBJECT DETECTION CẦN NẮM

### 5.1. Classification, localization, detection, segmentation

- Classification: ảnh thuộc lớp gì.
- Localization: một object chính ở đâu.
- Object detection: nhiều object, mỗi object có bbox và class.
- Semantic segmentation: mỗi pixel thuộc class nào, không tách instance.
- Instance segmentation: mỗi instance có mask riêng.
- Panoptic segmentation: kết hợp semantic và instance.

Trong bản vẽ:

- Detection phù hợp tìm symbol/cửa/thiết bị.
- Segmentation phù hợp tường, vùng phòng, vết nứt, vật liệu.
- OCR phù hợp text, kích thước, mã cấu kiện.
- Line/graph extraction phù hợp đường ống, dây điện, kết nối.

### 5.2. Bounding box

Các format thường gặp:

- xyxy: x_min, y_min, x_max, y_max.
- xywh: x, y, width, height.
- cxcywh: center_x, center_y, width, height.
- Có thể absolute pixel hoặc normalized 0..1.

Phải kiểm tra format khi đổi giữa dataset/framework.

### 5.3. IoU

    IoU = area(intersection) / area(union)

Dùng để:

- So prediction với ground truth.
- Quyết định true positive.
- Non-Maximum Suppression.
- Association trong tracking.

### 5.4. Precision và Recall

    Precision = TP / (TP + FP)
    Recall    = TP / (TP + FN)

- Precision cao: dự đoán ra thường đúng, ít false positive.
- Recall cao: tìm được nhiều object thật, ít bỏ sót.

Ví dụ công trình:

- Phát hiện nguy hiểm an toàn: thường ưu tiên recall để hạn chế bỏ sót.
- Tự động bóc tách khối lượng đưa thẳng vào báo cáo: precision rất quan trọng.
- Chọn threshold dựa trên cost của FP và FN, không chỉ dựa metric tổng.

### 5.5. AP và mAP

- AP là diện tích dưới Precision-Recall curve của một class.
- mAP là mean AP qua các class.
- mAP@0.5 dùng IoU threshold 0.5.
- mAP@0.5:0.95 trung bình từ IoU 0.5 tới 0.95, khắt khe hơn về localization.

Không nói "mAP 0.84 nghĩa là model đúng 84%". Đó là diễn giải sai.

### 5.6. Confidence threshold

- Threshold thấp: recall tăng, FP thường tăng.
- Threshold cao: precision tăng, FN thường tăng.
- Repo dùng conf=0.1, khá thấp; có thể hữu ích cho ByteTrack nhưng cần validate.

### 5.7. NMS

Mục tiêu: loại bbox trùng cho cùng object.

Quy trình cơ bản:

1. Chọn bbox confidence cao nhất.
2. Loại bbox cùng class có IoU lớn hơn threshold.
3. Lặp lại.

Biến thể: Soft-NMS giảm score thay vì loại ngay.

### 5.8. YOLO hoạt động ở mức khái niệm

YOLO là one-stage detector: model dự đoán vị trí bbox, objectness/confidence
và class trong một forward pass. Nó thường nhanh hơn pipeline two-stage như
Faster R-CNN, phù hợp video real-time. Đổi lại, object rất nhỏ/dày đặc có thể
khó hơn và cần image size, feature pyramid, dataset và augmentation phù hợp.

### 5.9. Vì sao bóng khó detect?

- Kích thước rất nhỏ so với ảnh 1920x1080.
- Motion blur.
- Bị che khuất.
- Hình dạng/màu giống chi tiết nền.
- Ít pixel sau resize về 640.
- Class imbalance so với player.

Cải tiến:

- Tăng image size.
- Tile/crop ROI.
- Tăng và cân bằng mẫu ball.
- Augmentation phù hợp small object/motion blur.
- Temporal model hoặc detector + tracker riêng.
- Hard-negative mining.
- Đánh giá AP riêng cho class ball, không chỉ mAP chung.

### 5.10. Data augmentation

Artifact train có HSV, translation, scale, horizontal flip và mosaic.

Phải đảm bảo augmentation không phá semantics. Với bản vẽ:

- Rotate 90/180/270 có thể hợp lý với symbol nhưng text bị đổi hướng.
- Perspective mạnh có thể không hợp với bản vẽ scan phẳng.
- Color jitter ít ý nghĩa với CAD đen trắng nhưng hữu ích với ảnh công trường.
- Random crop có thể cắt mất context/ký hiệu kích thước.


# PHẦN 6. TRACKING VÀ TEMPORAL COMPUTER VISION

### 6.1. Detection khác tracking

- Detection trả object ở từng frame độc lập.
- Tracking trả trajectory và identity qua thời gian.
- Tracking-by-detection dùng detection làm observation rồi association.

### 6.2. ByteTrack ở mức phỏng vấn

ByteTrack nổi bật ở việc association cả detection score cao và score thấp:

1. Dự đoán trạng thái track hiện tại, thường dựa Kalman Filter.
2. Ghép track với detection confidence cao.
3. Dùng detection confidence thấp để cứu các track chưa ghép.
4. Tạo track mới hoặc đánh dấu track lost/removed theo quy tắc vòng đời.

Điều này giúp giảm mất ID khi object bị che hoặc confidence giảm tạm thời.

### 6.3. Kalman Filter ở mức khái niệm

Hai bước:

- Predict: dự đoán state mới từ motion model.
- Update: kết hợp prediction với measurement mới.

State có thể chứa position, aspect ratio, height, velocity. Kalman Filter
giả định mô hình tuyến tính và nhiễu Gaussian.

### 6.4. Data association

Có thể dựa trên:

- IoU giữa bbox dự đoán và bbox detection.
- Khoảng cách tâm.
- Appearance embedding/Re-ID.
- Motion gating.
- Hungarian algorithm để tìm matching tổng chi phí nhỏ nhất.

### 6.5. ID switch

ID switch xảy ra khi identity của hai người bị đổi hoặc một người nhận ID mới.
Nó làm sai:

- Tổng quãng đường.
- Tốc độ theo cầu thủ.
- Đội đã cache theo ID.
- Thống kê possession.

Metric tracking có thể dùng:

- MOTA.
- MOTP.
- IDF1.
- HOTA.
- ID switches.


# PHẦN 7. HÌNH HỌC ẢNH VÀ CAMERA

### 7.1. Hệ tọa độ

- World coordinate: tọa độ vật lý.
- Camera coordinate: tọa độ tương đối camera.
- Image coordinate: tọa độ liên tục trên mặt phẳng ảnh.
- Pixel coordinate: hàng/cột pixel.

### 7.2. Camera intrinsic và extrinsic

Intrinsic gồm:

- Focal length fx, fy.
- Principal point cx, cy.
- Skew (thường gần 0).
- Distortion coefficients.

Extrinsic gồm:

- Rotation R.
- Translation t.
- Biến đổi world coordinate sang camera coordinate.

### 7.3. Lens distortion

- Radial distortion: barrel/pincushion.
- Tangential distortion: lens/sensor không hoàn toàn song song.
- Calibrate bằng checkerboard/Charuco và cv2.calibrateCamera.
- Undistort trước đo hình học chính xác.

Dự án hiện chưa làm lens calibration.

### 7.4. Homography và affine transform

Affine giữ:

- Đường thẳng.
- Tính song song.
- Tỷ lệ trên cùng đường.

Homography giữ:

- Đường thẳng vẫn là đường thẳng.
- Không nhất thiết giữ song song/góc/khoảng cách.
- Mô tả quan hệ hai mặt phẳng dưới phép chiếu phối cảnh.

Affine có 6 bậc tự do, cần tối thiểu 3 cặp điểm không thẳng hàng.
Homography có 8 bậc tự do, cần tối thiểu 4 cặp điểm không thẳng hàng.

### 7.5. RANSAC

RANSAC robust với outlier:

1. Chọn ngẫu nhiên tập điểm tối thiểu.
2. Fit model.
3. Đếm inlier theo reprojection error.
4. Lặp nhiều lần.
5. Chọn model có nhiều inlier nhất và refine.

Ứng dụng:

- Estimate homography từ feature matching.
- Camera motion robust hơn chọn flow vector lớn nhất.
- Align bản vẽ scan với template.

### 7.6. Optical Flow

Optical Flow ước lượng chuyển động pixel giữa hai frame.

Lucas-Kanade giả định trong vùng nhỏ:

- Brightness constancy.
- Chuyển động nhỏ.
- Các pixel lân cận có chuyển động tương tự.

Pyramidal LK xử lý chuyển động lớn hơn bằng image pyramid.

Sparse Optical Flow theo dõi một số feature; Dense Optical Flow ước lượng
vector cho nhiều/mọi pixel.

### 7.7. Reprojection error

Sau khi estimate transform, chiếu điểm nguồn sang đích và tính khoảng cách
với ground truth. Mean/median reprojection error giúp đánh giá calibration.


# PHẦN 8. XỬ LÝ ẢNH CƠ BẢN CÓ THỂ BỊ HỎI

### 8.1. Color spaces

- RGB/BGR: trực quan nhưng trộn brightness với color.
- HSV: tách hue/saturation/value, thuận tiện threshold màu.
- Lab: gần perceptual uniform, khoảng cách màu có ý nghĩa hơn.
- Grayscale: giảm dữ liệu khi màu không quan trọng.

OpenCV đọc ảnh theo BGR mặc định, không phải RGB.

### 8.2. Thresholding

- Global threshold.
- Otsu tự chọn threshold từ histogram.
- Adaptive threshold phù hợp ánh sáng không đồng đều.

Ứng dụng bản vẽ scan: tách nét/text khỏi nền giấy bị bóng hoặc ố.

### 8.3. Morphology

- Erosion: co foreground, loại nhiễu nhỏ.
- Dilation: giãn foreground, nối nét đứt.
- Opening = erosion rồi dilation: loại nhiễu.
- Closing = dilation rồi erosion: lấp khe/nối nét.

Ứng dụng bản vẽ: nối đường tường bị đứt, loại chấm scan, làm sạch mask.

### 8.4. Edge và line detection

- Sobel: gradient X/Y.
- Canny: smoothing, gradient, non-max suppression, hysteresis threshold.
- Hough Line Transform: tìm đường thẳng trong không gian tham số.

Ứng dụng: tìm đường tường, grid, đường ống, cạnh cấu kiện.

### 8.5. Connected components và contour

- Connected components gán nhãn vùng foreground liên thông.
- Contour biểu diễn đường biên.
- Có thể lọc theo area, aspect ratio, hierarchy.

### 8.6. Filtering

- Gaussian blur: giảm Gaussian noise, làm mờ edge.
- Median blur: tốt với salt-and-pepper, giữ edge hơn.
- Bilateral filter: giữ edge nhưng tốn chi phí hơn.


# PHẦN 9. LIÊN HỆ VỚI COMPUTER VISION CHO CÔNG TRÌNH

### 9.1. PPE/safety monitoring

Bài toán:

- Phát hiện người, mũ, áo phản quang, dây an toàn.
- Kiểm tra quan hệ person-wears-helmet thay vì chỉ đếm helmet.
- Theo dõi người vào vùng nguy hiểm.

Liên hệ dự án:

- YOLO tương ứng detection PPE/person.
- ByteTrack tương ứng theo dõi công nhân.
- Polygon ROI tương ứng vùng nguy hiểm.
- Temporal smoothing giảm cảnh báo nhấp nháy.

Điểm cần lưu ý:

- Một helmet gần người không chắc thuộc người đó.
- Cần association theo bbox/keypoint/pose.
- Ưu tiên recall nhưng phải kiểm soát alert fatigue.
- Camera cao, occlusion và PPE nhỏ là thách thức.

### 9.2. Progress monitoring

- So ảnh hiện trường theo thời gian.
- Detect/segment cấu kiện đã thi công.
- Đăng ký ảnh với BIM hoặc ảnh chuẩn.
- Ước lượng phần trăm hoàn thành.

Liên hệ:

- Tracking/temporal reasoning.
- Homography/image registration.
- Segmentation và change detection.

### 9.3. Defect detection

- Crack, spalling, corrosion, water leakage.
- Detection cho vùng lỗi rời rạc.
- Segmentation phù hợp vết nứt mảnh và hình dạng bất quy tắc.
- Có thể đo length/width sau camera calibration và scale reference.

Metric ngoài mAP:

- Dice/IoU cho segmentation.
- Pixel recall cho vết nứt mảnh.
- Sai số chiều dài/chiều rộng.
- Recall theo defect severity.

### 9.4. Camera cố định và nhiều camera

- Cần calibration từng camera.
- Đồng bộ timestamp.
- Track ID xuyên camera cần Re-ID.
- Xử lý privacy và retention.
- Edge inference có thể giảm bandwidth/latency.


# PHẦN 10. COMPUTER VISION CHO BẢN VẼ KỸ THUẬT

### 10.1. Một pipeline bản vẽ tổng quát

PDF/CAD/scan đầu vào
    |
    +--> Nếu PDF vector: ưu tiên parse vector/text trực tiếp
    |
    +--> Nếu raster/scan: render ảnh DPI phù hợp
    |
    v
Deskew + denoise + contrast/binarization
    |
    v
Phân vùng title block / legend / drawing area
    |
    +--> OCR text và kích thước
    +--> Detect symbol
    +--> Segment wall/room/line
    +--> Extract line/graph connectivity
    |
    v
Ghép text-symbol-line bằng spatial relation
    |
    v
Chuẩn hóa tọa độ, scale và đơn vị
    |
    v
Rule validation / quantity takeoff / structured output
    |
    v
Human review + confidence + audit trail

### 10.2. Vì sao không nên rasterize PDF vector ngay lập tức?

PDF/CAD vector có thể đã chứa:

- Text thật.
- Path/line/curve.
- Layer.
- Tọa độ chính xác.
- Metadata.

Parse vector thường chính xác và nhẹ hơn OCR/CV. Raster CV nên dùng khi input
là scan hoặc cấu trúc vector không đáng tin. Pipeline tốt có nhánh theo loại input.

### 10.3. Thách thức ảnh bản vẽ rất lớn

Bản vẽ có thể 10.000-50.000 pixel mỗi chiều. Resize toàn ảnh về 640 sẽ làm
mất symbol/text nhỏ.

Giải pháp tiled inference:

1. Chia ảnh thành tile có overlap.
2. Infer từng tile.
3. Đổi tọa độ tile về global coordinate.
4. Merge detection vùng overlap bằng NMS/Soft-NMS/WBF.
5. Lưu tile ID để debug.

Trade-off:

- Tile nhỏ: giữ chi tiết nhưng mất context và tăng compute.
- Tile lớn: nhiều context nhưng tốn VRAM.
- Overlap giảm object bị cắt nhưng tạo duplicate.

### 10.4. Deskew và registration

Scan có thể bị xoay/lệch. Có thể:

- Dùng Hough line tìm góc dominant.
- Dùng keypoint matching.
- Dùng template/title block.
- Estimate affine/homography với RANSAC.

Registration cần cho:

- So sánh hai revision.
- Change detection.
- Overlay as-built và design.

### 10.5. OCR pipeline

OCR không chỉ là gọi một model. Pipeline thường gồm:

- Text detection: vùng nào có text.
- Orientation/rotation correction.
- Text recognition: đọc ký tự.
- Post-processing theo vocabulary/domain.
- Ghép text với symbol/line gần nhất.

Các khó khăn:

- Text nhỏ, xoay nhiều hướng.
- Ký hiệu gần giống chữ.
- Font kỹ thuật.
- Nét line đi xuyên text.
- Đơn vị và dấu thập phân.
- OCR đúng text nhưng gán sai đối tượng vẫn tạo lỗi nghiệp vụ.

Metric:

- Character Error Rate (CER).
- Word Error Rate (WER).
- Exact match.
- Detection precision/recall.
- End-to-end field accuracy.

### 10.6. Symbol detection

Thách thức:

- Nhiều class có hình gần giống.
- Symbol nhỏ và dày đặc.
- Rotation.
- Version/standard khác nhau.
- Class imbalance.

Cải tiến:

- Tiled inference.
- Rotation augmentation hoặc oriented bounding box.
- Hard-negative mining.
- Few-shot/metric learning cho symbol hiếm.
- Kết hợp legend của chính bản vẽ.
- Context: symbol nằm trên loại line nào, gần text nào.

### 10.7. Line và connectivity

Detection bbox không đủ để hiểu hệ thống đường ống/dây điện. Cần graph:

- Node: symbol, junction, endpoint, equipment.
- Edge: line/pipe/wire kết nối.
- Thuộc tính: type, size, direction, text label.

Pipeline khả dĩ:

- Segmentation line.
- Skeletonization.
- Detect junction/endpoints.
- Graph construction.
- Snap endpoint với symbol port.
- Rule-based validation.

### 10.8. Oriented bounding boxes

Với object xoay, bbox ngang chứa nhiều background. OBB biểu diễn center,
width, height và angle, phù hợp text/symbol xoay. Metric IoU và augmentation
phải hỗ trợ rotation.

### 10.9. Segmentation metric

    IoU = intersection / union
    Dice = 2*intersection / (pred_area + gt_area)

Với class rất nhỏ/mất cân bằng:

- Dice/Focal/Tversky loss có thể hữu ích.
- Pixel accuracy dễ gây hiểu nhầm vì background quá lớn.

### 10.10. Scale và đo lường trên bản vẽ

Không được đo pixel rồi gọi là mm nếu chưa xác định scale.

Scale có thể lấy từ:

- Metadata vector/CAD.
- Tỷ lệ ghi trong title block.
- Dimension line đã OCR.
- Một kích thước chuẩn/reference object.

Phải xử lý:

- Nhiều viewport có scale khác nhau.
- Scan bị stretch không đều.
- Đơn vị mm/cm/m/inch.
- Tỷ lệ ghi text có thể không còn đúng nếu PDF bị resize/in sai.

### 10.11. So sánh revision bản vẽ

Pipeline:

1. Chuẩn hóa page và DPI.
2. Register hai bản vẽ.
3. Mask title block/revision cloud nếu cần.
4. So sánh vector hoặc feature/raster.
5. Detect added/deleted/modified region.
6. Liên kết thay đổi với entity/text.
7. Human review.

Pixel diff thô dễ báo sai do anti-aliasing, scan noise hoặc lệch registration.

### 10.12. Human-in-the-loop

Trong công trình, lỗi có thể gây chi phí cao. Hệ thống nên:

- Trả confidence.
- Đánh dấu vùng không chắc chắn.
- Cho người dùng sửa kết quả.
- Lưu audit trail/model version.
- Dùng correction làm dữ liệu active learning.


# PHẦN 11. DATASET VÀ LABELING

### 11.1. Chia tập dữ liệu đúng

Không random split frame từ cùng video vào train và validation vì frame gần
nhau gần như giống nhau, gây data leakage. Nên split theo video/trận/camera.

Với công trình:

- Split theo site/project/building/camera/date.
- Với bản vẽ: split theo project/discipline/template/company.
- Test set phải đại diện domain triển khai thật.

### 11.2. Label quality

Cần annotation guideline:

- Khi object bị che bao nhiêu thì label?
- Bbox phần nhìn thấy hay bbox toàn object?
- Symbol bị cắt ở mép tile xử lý thế nào?
- Class hierarchy và ambiguous class.
- Ignore region.

Kiểm tra inter-annotator agreement và audit sample định kỳ.

### 11.3. Class imbalance

Giải pháp:

- Thu thập thêm class hiếm.
- Oversampling có kiểm soát.
- Class-aware sampling.
- Loss weighting/focal loss.
- Synthetic data.
- Hard-negative mining.
- Báo cáo metric per-class.

### 11.4. Data leakage

Ví dụ:

- Frame liền kề nằm cả train và val.
- Hai revision gần giống nằm ở hai split.
- Cùng template/title block khiến model nhớ project.
- Augmented copy của cùng ảnh lọt vào test.

### 11.5. Domain shift

- Camera/ánh sáng khác.
- Loại công trình khác.
- Font/standard bản vẽ khác.
- Scanner/DPI/noise khác.
- Đồng phục/PPE khác.

Giải pháp:

- Domain-diverse data.
- Augmentation phù hợp.
- Fine-tune theo site/domain.
- Monitor drift.
- Active learning.


# PHẦN 12. ĐÁNH GIÁ VÀ THỰC NGHIỆM

### 12.1. Không chỉ dùng một metric

Detection:

- Precision, recall, F1.
- AP/mAP.
- AP theo class và kích thước.
- Latency/FPS/memory.

Tracking:

- IDF1, HOTA, MOTA, ID switches.

Segmentation:

- IoU, Dice, per-class recall.

OCR:

- CER, WER, field accuracy.

Đo lường:

- MAE/RMSE theo đơn vị vật lý.
- Bias theo vị trí/góc camera.

Nghiệp vụ:

- Tỷ lệ bản vẽ cần human correction.
- Thời gian tiết kiệm.
- False alarm per hour/site.

### 12.2. Confusion matrix

- Hàng/cột phụ thuộc tool, phải đọc label.
- Diagonal là dự đoán đúng.
- Off-diagonal cho biết class nào bị nhầm.
- Background row/column thể hiện missed detection hoặc false positive.

### 12.3. Ablation study

Để chứng minh một module có ích:

- Baseline detector.
- + tracking.
- + camera compensation.
- + homography.
- So sánh metric tốc độ/trajectory ở từng cấu hình.

Với team assignment:

- Full bbox RGB.
- Top-half RGB.
- Top-half HSV/Lab.
- Multi-frame voting.

### 12.4. Error analysis

Nhóm lỗi theo nguyên nhân:

- Small object.
- Occlusion.
- Motion blur.
- Illumination.
- Similar classes.
- Edge of image/tile.
- Annotation issue.
- Domain shift.

Không chỉ nhìn một con số mAP; xem sample FP/FN để quyết định bước tiếp theo.


# PHẦN 13. PRODUCTION VÀ SYSTEM DESIGN

### 13.1. Pipeline production đề xuất cho dự án này

- CLI/API nhận input, output, model, device và config.
- Validate file/model/video metadata.
- Đọc video streaming/chunk, không load toàn bộ RAM.
- Truyền FPS thật xuyên suốt pipeline.
- Cache có hash của video/model/config.
- Logging có cấu trúc.
- Exception handling và status rõ ràng.
- Xuất JSON/CSV bên cạnh video.
- Test unit/integration/regression.
- Docker và lock dependency.
- CI lint/test/build.
- Model registry/versioning.
- Monitoring latency, drift và confidence.

### 13.2. Batch và real-time

Batch:

- Tối ưu throughput.
- Có thể chờ gom batch.
- Phù hợp xử lý bản vẽ hoặc video offline.

Real-time:

- Tối ưu latency.
- Có deadline theo FPS camera.
- Có thể skip frame, tracking giữa các detection.
- Cần backpressure khi inference chậm.

### 13.3. Tối ưu inference

- Mixed precision FP16.
- TensorRT/ONNX/OpenVINO tùy hardware.
- Batch size phù hợp.
- Decode video hiệu quả.
- Resize/letterbox đúng.
- Detect mỗi N frame và track giữa các frame.
- Quantization INT8 sau calibration, kiểm tra mất accuracy.
- Tiled inference chỉ ở ROI cần thiết.

### 13.4. Reproducibility

- requirements/lock file.
- Seed.
- Version dataset.
- Version model/config/code commit.
- Lưu train args và metric.
- Không phụ thuộc absolute Windows path như args.yaml hiện tại.

### 13.5. Model/data monitoring

- Input resolution/distribution.
- Confidence distribution.
- Prediction class frequency.
- Latency/GPU memory/error rate.
- Sampling prediction cho human review.
- Ground-truth delayed evaluation nếu có.
- Alert khi drift hoặc KPI giảm.

### 13.6. API output tốt

Không chỉ xuất video. Nên trả structured data:

{
  "video_id": "...",
  "model_version": "...",
  "fps": 25,
  "frames": [
    {
      "frame_index": 0,
      "timestamp_ms": 0,
      "objects": [
        {"track_id": 1, "class": "player", "bbox": [...],
         "confidence": 0.92, "team": 1, "speed_kph": 12.3}
      ]
    }
  ]
}

### 13.7. Bảo mật

- Không load pickle từ người dùng.
- Validate MIME/size của upload.
- Giới hạn tài nguyên và thời gian job.
- Scan dependency/model provenance.
- Xóa metadata/ẩn mặt nếu dữ liệu nhạy cảm.
- Phân quyền và audit log cho bản vẽ công trình.


# PHẦN 14. REVIEW TRUNG THỰC DỰ ÁN HIỆN TẠI

Điểm mạnh:

- Pipeline có nhiều giai đoạn và mục tiêu rõ.
- Module hóa theo trách nhiệm.
- Kết hợp DL và CV truyền thống.
- Có artifact training và metric.
- Có cache để rút ngắn vòng lặp thử nghiệm.
- Dùng foot point hợp lý với ground-plane homography.

Điểm cần sửa trước khi gọi là chuyên nghiệp:

- Thiếu requirements.txt/pyproject.toml.
- Thiếu model weights hoặc cơ chế download.
- Thiếu stubs/output directories khi chạy mới.
- Thiếu .gitignore.
- Commit .idea, video lớn và nhiều artifact.
- Không có test/CI/lint/formatter.
- FPS hard-code sai video mẫu.
- Đường dẫn và calibration hard-code.
- Edge case dễ crash.
- Cache pickle không version và có rủi ro bảo mật.
- README nói YOLOv8 nhưng train artifact nói YOLOv5x.
- Chưa có evaluation cho tracking, possession, speed/distance/team assignment.
- Chưa có CLI/config/logging.

Cách trả lời khi interviewer chỉ ra lỗi:

"Đúng, đây là hạn chế của phiên bản prototype. Nguyên nhân là em ưu tiên
chứng minh pipeline trước. Nếu chuẩn hóa lại, em sẽ đọc FPS từ metadata,
đưa parameter vào config/CLI, validate edge case, version cache theo hash
video-model-config, thêm test và khóa dependency. Em cũng sẽ sửa sự không
đồng nhất YOLOv5x/YOLOv8 trong tài liệu."


# PHẦN 15. CÂU HỎI PHỎNG VẤN VÀ TRẢ LỜI MẪU

**Q1. Tại sao cần tracking khi đã có YOLO?**

**A:** YOLO chỉ trả detection độc lập ở mỗi frame, không biết hai bbox qua hai
frame có phải cùng người. Tracking tạo identity và trajectory, cần thiết để
tính tốc độ, quãng đường, giữ nhãn đội và thống kê possession.

**Q2. Vì sao chọn ByteTrack?**

**A:** ByteTrack là tracking-by-detection có hiệu quả tốt và triển khai thuận
tiện. Nó association cả detection confidence cao và thấp, giúp cứu track khi
object bị che hoặc detector giảm confidence tạm thời.

**Q3. Vì sao conf của detector là 0.1?**

**A:** Threshold thấp giúp giữ recall và cung cấp detection score thấp cho logic
tracking. Tuy nhiên 0.1 hiện là tham số prototype; cần tune trên validation và
đánh giá trade-off false positive/false negative theo class.

**Q4. Tại sao dùng center cho bóng và foot point cho người?**

**A:** Center đại diện tốt cho vật thể nhỏ như bóng. Với người, điểm chân gần mặt
phẳng sân nên phù hợp để homography và đo khoảng cách; tâm bbox nằm trên thân.

**Q5. Nội suy bóng có giả định gì?**

**A:** Giả định tọa độ bbox thay đổi tương đối liên tục trong khoảng mất ngắn.
Nó không tốt nếu mất lâu, bóng đổi hướng mạnh hoặc detection trước/sau sai.

**Q6. Camera compensation hiện tại có chính xác không?**

**A:** Nó là xấp xỉ translation dựa trên sparse optical flow, hữu ích cho pan
camera nhưng chưa robust với zoom, rotation và outlier. Cải tiến là median
flow hoặc estimate affine/homography với RANSAC từ nhiều điểm nền.

**Q7. Homography có dùng được cho mọi điểm trên cầu thủ không?**

**A:** Không. Homography đúng cho các điểm trên cùng mặt phẳng sân. Vì vậy em dùng
foot point; biến đổi đầu hoặc toàn bbox như nằm trên sân sẽ gây sai.

**Q8. Tại sao cần bốn điểm?**

**A:** Homography 3x3 có 8 bậc tự do sau khi bỏ scale. Mỗi cặp điểm cung cấp hai
phương trình nên cần tối thiểu bốn cặp không thẳng hàng.

**Q9. Làm sao phân đội?**

**A:** K-Means lần một tách màu áo và nền trong nửa trên crop người; K-Means lần
hai gom màu đại diện của các player thành hai đội. Kết quả cache theo track ID.

**Q10. Nếu hai đội cùng màu gần giống nhau?**

**A:** RGB K-Means sẽ yếu. Em sẽ chuyển HSV/Lab, lấy màu nhiều frame, mask người,
majority vote và có thể dùng learned embedding/Re-ID kết hợp context.

**Q11. Possession có đáng tin không?**

**A:** Hiện là heuristic cầu thủ gần bóng nhất trong 70 pixel nên chỉ là ước lượng.
Cần distance sau homography, temporal smoothing, ball velocity/direction và
trạng thái unknown để đáng tin hơn.

**Q12. Tốc độ được tính ra sao?**

**A:** Dùng khoảng cách Euclidean giữa hai position_transformed cách nhau năm
frame, chia cho delta-frame/FPS để ra m/s rồi nhân 3.6 ra km/h. Distance được
cộng dồn theo track ID.

**Q13. Tại sao cửa sổ năm frame?**

**A:** Giảm nhiễu vị trí so với lấy hai frame liên tiếp. Nhưng window cần tune;
cửa sổ lớn mượt hơn nhưng làm giảm phản ứng với tăng/giảm tốc nhanh.

**Q14. Sai số tốc độ đến từ đâu?**

**A:** Detection jitter, ID switch, camera motion estimate, homography calibration,
FPS, foot point, lens distortion và giả định mặt phẳng. Đánh giá cần ground
truth và MAE/RMSE, không thể suy ra chỉ từ mAP detector.

**Q15. mAP@0.5 khác mAP@0.5:0.95?**

**A:** mAP@0.5 coi bbox đúng khi IoU đạt 0.5. mAP@0.5:0.95 trung bình nhiều ngưỡng
tới 0.95 nên nghiêm ngặt hơn về localization và thường thấp hơn.

**Q16. Precision hay recall quan trọng hơn?**

**A:** Tùy cost. Cảnh báo an toàn thường ưu tiên recall để tránh bỏ sót; tự động
bóc khối lượng cần precision cao để tránh ghi nhận sai. Em chọn threshold theo
metric nghiệp vụ chứ không mặc định một phía.

**Q17. Tại sao metric hiện tại chưa đủ?**

**A:** Repo có metric detector nhưng chưa có metric tracking, team classification,
possession, camera estimation và speed. Pipeline end-to-end cần đánh giá từng
module và KPI cuối, vì detector tốt chưa đảm bảo tốc độ đúng.

**Q18. Vì sao không load toàn video vào RAM ở production?**

**A:** Memory tăng tuyến tính theo số frame. Nên dùng generator/chunk, pipeline
producer-consumer hoặc streaming, chỉ giữ state cần cho tracking và window.

**Q19. Nếu triển khai real-time thì làm gì?**

**A:** Profile decode/preprocess/inference/postprocess; dùng FP16/TensorRT/ONNX,
batch nhỏ, detect mỗi N frame và track ở giữa, async decode, bounded queue và
frame dropping khi chậm. Đo p50/p95 latency chứ không chỉ FPS trung bình.

**Q20. Tại sao README YOLOv8 nhưng train là YOLOv5x?**

**A:** Đây là lỗi đồng bộ tài liệu. Artifact là bằng chứng nguồn đáng tin hơn và
cho thấy checkpoint nền yolov5x.pt. Em sẽ xác minh best.pt, sửa README và ghi
rõ version Ultralytics/model để reproducible.

**Q21. Với bản vẽ 20.000x20.000, bạn xử lý sao?**

**A:** Không resize toàn bộ về 640. Em chia tile overlap, infer từng tile, map bbox
về global coordinate rồi merge duplicate. Đồng thời giữ một thumbnail/global
branch để lấy context và ưu tiên parse vector nếu PDF/CAD có dữ liệu vector.

**Q22. Detection symbol bị duplicate ở tile overlap thì sao?**

**A:** Map về cùng hệ global rồi dùng class-aware NMS, Soft-NMS hoặc Weighted Box
Fusion. Cần tune IoU và xử lý symbol bị cắt ở biên tile.

**Q23. OCR bản vẽ cần gì ngoài recognition?**

**A:** Text detection, orientation, recognition, domain correction và quan trọng
nhất là association text với symbol/dimension/line. Metric end-to-end field
accuracy quan trọng hơn chỉ CER.

**Q24. Làm sao tìm tường hoặc đường ống?**

**A:** Có thể segmentation đường, morphology/skeletonization, tìm junction và tạo
graph. Hough phù hợp line thẳng đơn giản, nhưng bản vẽ phức tạp cần kết hợp
segmentation, vector parsing và rule về connectivity.

**Q25. So hai revision bản vẽ thế nào?**

**A:** Chuẩn hóa, registration bằng feature/homography RANSAC, sau đó diff ở mức
vector/entity hoặc raster đã align. Loại nhiễu anti-aliasing và liên kết vùng
thay đổi với entity/text để tạo kết quả có ý nghĩa nghiệp vụ.

**Q26. Khi nào dùng segmentation thay detection?**

**A:** Khi hình dạng/diện tích/biên chính xác quan trọng, ví dụ vết nứt, tường,
phòng. Detection phù hợp khi chỉ cần vị trí object và bbox như symbol/thiết bị.

**Q27. Làm sao biết model generalize sang công trình mới?**

**A:** Split test theo site/project chứ không random ảnh gần nhau; báo cáo metric
theo site/camera/điều kiện, chạy pilot unseen domain và monitor drift. Nếu giảm,
dùng active learning/fine-tune với dữ liệu đại diện.

**Q28. Nếu dữ liệu ít?**

**A:** Transfer learning, augmentation hợp domain, synthetic data, weak/self-
supervised pretraining, active learning, cross-validation theo group và ưu tiên
label các mẫu có uncertainty/diversity cao.

**Q29. Bạn debug model như thế nào?**

**A:** Đầu tiên tái hiện lỗi, phân tách lỗi data/preprocess/model/postprocess, xem
FP/FN theo nhóm, kiểm tra coordinate/resize/label mapping, chạy một sample qua
từng stage, so train-val-serving preprocessing và tạo regression test.

**Q30. Nếu model offline tốt nhưng production kém?**

**A:** Kiểm tra domain shift, data leakage, preprocessing mismatch, threshold/NMS,
model version, image compression/resolution và metric production. Lấy sample
production gán nhãn để đo thay vì dựa cảm giác.

**Q31. Làm sao thiết kế human review?**

**A:** Auto-accept prediction confidence cao và rule-consistent; đưa prediction
uncertain/conflict vào review queue; UI hiển thị crop/context; lưu correction,
model version và reviewer; dùng correction cho active learning.

**Q32. Bạn sẽ cải tiến repo này theo thứ tự nào?**

**A:** 

1. Làm clone-and-run: dependency, directory, model instructions.
2. Đọc FPS/metadata động và bỏ hard-code input/output.
3. Validate edge case và structured logging.
4. Unit/integration test.
5. Config/CLI và cache versioning.
6. Đánh giá từng module.
7. Camera motion robust + possession theo mét/thời gian.
8. Streaming/performance/packaging/CI.


# PHẦN 16. CÂU HỎI HÀNH VI GẮN VỚI DỰ ÁN

### 16.1. "Khó khăn lớn nhất là gì?"

Mẫu trả lời STAR:

Situation:
"Detection từng frame chưa đủ để tính chuyển động vì camera cũng di chuyển."

Task:
"Em cần tách tương đối chuyển động camera và đưa tọa độ về hệ có ý nghĩa."

Action:
"Em dùng feature tracking với Lucas-Kanade để estimate camera translation,
trừ vector này khỏi vị trí object, sau đó dùng homography từ bốn điểm sân để
đưa foot point sang mặt phẳng sân."

Result:
"Pipeline có thể hiển thị tốc độ/quãng đường thay vì chỉ bbox. Tuy nhiên em
nhận ra cần ground truth và calibration động để định lượng độ chính xác."

### 16.2. "Bạn đã đánh đổi gì?"

"Em chọn K-Means và heuristic possession để hoàn thành end-to-end prototype
nhanh, thay vì huấn luyện thêm model. Đổi lại độ ổn định với ánh sáng, áo giống
nhau và tình huống tranh bóng còn hạn chế. Nếu sản phẩm hóa, em sẽ dùng dữ
liệu nhiều frame, color space tốt hơn và temporal model/rule."

### 16.3. "Nếu làm lại từ đầu?"

"Em sẽ định nghĩa metric từng module trước, thiết kế config/data schema, split
dataset theo video để tránh leakage, lưu metadata FPS/calibration, viết test
cho geometry và edge case, rồi mới tối ưu model. Điều này giúp biết cải tiến
nào thực sự nâng KPI cuối."


# PHẦN 17. CÂU HỎI NÊN HỎI NGƯỢC CÔNG TY

- Input chính là PDF vector, CAD hay bản scan raster?
- Bài toán ưu tiên detection, segmentation, OCR hay graph extraction?
- Độ phân giải trung bình và lớn nhất của bản vẽ là bao nhiêu?
- Hệ thống chạy batch cloud, on-premise hay edge tại công trường?
- KPI kỹ thuật và KPI nghiệp vụ đang dùng là gì?
- Chi phí false positive và false negative bên nào lớn hơn?
- Công ty có annotation guideline và quy trình data versioning không?
- Có human review không, correction có quay lại active learning không?
- Model phải generalize nhiều tiêu chuẩn bản vẽ/quốc gia như thế nào?
- Team đang dùng framework và model serving stack nào?
- Khó khăn lớn nhất hiện tại là data, accuracy, latency hay integration?
- Cách phối hợp giữa CV engineer và kỹ sư xây dựng/BIM/CAD?


# PHẦN 18. CHECKLIST TRƯỚC PHỎNG VẤN

Phải thuộc:

[ ] Bốn class của detector.
[ ] Cấu trúc tracks.
[ ] Vì sao cần YOLO + ByteTrack.
[ ] Vì sao ball dùng interpolation.
[ ] Vì sao người dùng foot point.
[ ] Optical Flow đang làm gì và hạn chế gì.
[ ] Công thức homography và vì sao cần bốn điểm.
[ ] Công thức speed và đổi m/s sang km/h.
[ ] K-Means hai cấp phân đội như thế nào.
[ ] Possession chỉ là heuristic.
[ ] Precision, recall, IoU, mAP.
[ ] Metric train hiện có.
[ ] Sự không đồng nhất YOLOv8/YOLOv5x.
[ ] FPS video mẫu 25 nhưng code dùng 24.
[ ] Ba cải tiến ưu tiên.
[ ] Tiled inference cho bản vẽ lớn.
[ ] OCR detection-recognition-association.
[ ] Detection vs segmentation.
[ ] Registration/homography/RANSAC.
[ ] Data leakage và split theo project/video.

Thông tin nhanh để nhớ:

- Dataset: Roboflow, CC BY 4.0.
- Class: ball, goalkeeper, player, referee.
- Train artifact: yolov5x.pt.
- Epoch: 100.
- Image size: 640.
- Batch: 4.
- Epoch 100 precision: ~0.8985.
- Epoch 100 recall: ~0.7567.
- Epoch 100 mAP50: ~0.8380.
- Epoch 100 mAP50-95: ~0.5966.
- Video mẫu: 1920x1080, 25 FPS, 30 giây.
- Code speed/output: đang hard-code 24 FPS.
- Detection conf: 0.1.
- Detection batch: 20 frame.
- Speed window: 5 frame.
- Ball-player threshold: 70 pixel.


# PHẦN 19. KẾT LUẬN NGẮN ĐỂ CHỐT PHỎNG VẤN

"Dự án giúp em hiểu rằng một bài toán Computer Vision thực tế không kết thúc
ở bước model.predict. Phải quản lý tọa độ, thời gian, identity, calibration,
post-processing, metric và edge case. Dù domain bóng đá khác xây dựng, những
khối kỹ thuật em đã dùng như detection, tracking, image geometry, clustering,
registration và pipeline design có thể chuyển sang giám sát công trường. Với
bản vẽ, em hiểu cần bổ sung OCR, segmentation, tiled inference, vector parsing
và graph connectivity. Em cũng nhìn rõ những hạn chế prototype hiện tại và có
thứ tự cụ thể để đưa nó gần production hơn."

# PHẦN 20. PHÂN TÍCH ẢNH TRAIN7 VÀ SCRIPT TRÌNH BÀY

4 ảnh nên show với recruiter theo thứ tự từ trực quan đến phân tích sâu:

Thứ tự khuyên dùng:
val_batch1 labels vs pred → confusion_matrix_normalized → BoxPR_curve → results.png

Lý do thứ tự này: bắt đầu bằng ảnh dễ hiểu nhất để recruiter hình dung bài
toán, sau đó mới đi vào phân tích điểm yếu và metric.

## 20.1. val_batch1_labels.jpg vs val_batch1_pred.jpg

Ý nghĩa:
- Labels: ground truth do người annotate, không có confidence score.
- Pred: kết quả model dự đoán, có confidence score kèm theo.
- Đây là validation set, tức data model chưa từng thấy trong training.

Script nói:

"Đây là so sánh trực quan giữa ground truth và prediction trên validation
set. Em muốn show ảnh này trước vì metric số không thể hiện được bằng mắt.
Có thể thấy player và referee được detect khá chính xác về vị trí và class,
confidence hầu hết trên 0.8. Điểm đáng chú ý là bóng — một số frame có
'ball 0.4' với confidence rất thấp, và một số frame bóng hoàn toàn không
có detection. Đây là biểu hiện thực tế của vấn đề em sẽ phân tích ở ảnh tiếp."

Nếu bị hỏi:
- "Confidence 0.4 với bóng thấp vậy có dùng được không?"
  Trả lời: "Đó là lý do em đặt detection threshold 0.1 thấp để giữ recall,
  và bổ sung bước interpolate_ball_positions trong pipeline để bù các frame
  bóng bị miss. Đây là trade-off có chủ đích, không phải bỏ qua vấn đề."

## 20.2. confusion_matrix_normalized.png

Ý nghĩa:
- Hàng = predicted class, cột = true class.
- Đường chéo = tỷ lệ đúng của từng class.
- Ô background = bỏ sót (false negative) hoặc phát hiện nhầm (false positive).

Số liệu cụ thể:
- player:     0.95 → 5% bị bỏ sót hoặc nhầm
- goalkeeper: 0.85 → 15% lỗi
- referee:    0.85 → 15% lỗi
- ball:       0.20 → 80% bị predict thành background (bỏ sót)

Script nói:

"Đây là confusion matrix được normalize theo tỷ lệ. Em thấy đây là ảnh
quan trọng nhất khi phân tích kết quả vì nó cho thấy điều mà mAP tổng thể
che đi. Player đạt 95% và goalkeeper, referee đạt 85% — đều tốt. Nhưng
ball chỉ 20%, tức là 80% trường hợp model bỏ sót bóng, classify nhầm
thành background. Em đã identify được hai nguyên nhân: thứ nhất là class
imbalance nghiêm trọng — dataset có 12,228 mẫu player nhưng chỉ 519 mẫu
ball; thứ hai là bóng rất nhỏ trong ảnh, chỉ khoảng 1-2% kích thước frame
và di chuyển nhanh nên dễ bị motion blur. Nhận ra vấn đề này em đã thiết
kế pipeline có bước interpolate để bù các frame bóng bị miss."

Nếu bị hỏi:
- "Cách fix class imbalance đó?"
  Trả lời: "Oversampling có kiểm soát cho class ball, tăng loss weight
  riêng cho ball, augmentation phù hợp small object và motion blur, hoặc
  train một detector riêng cho bóng với image size lớn hơn 640."

## 20.3. BoxPR_curve.png — Precision-Recall Curve

Ý nghĩa:
- Mỗi đường là PR curve của một class.
- Diện tích dưới đường = AP của class đó.
- Đường xanh đậm là mean của tất cả class (mAP@0.5 = 0.832).
- Đường ball nằm rất thấp vì AP chỉ 0.426.

Số liệu cụ thể:
- goalkeeper: 0.986
- player:     0.985
- referee:    0.929
- ball:       0.426
- all:        0.832 mAP@0.5

Script nói:

"Đây là Precision-Recall curve, diện tích dưới từng đường chính là AP
của class đó. Player và goalkeeper gần như hoàn hảo — đường giữ precision
cao cho đến khi recall gần 1.0. Ball thì ngược lại, đường sụp rất sớm nên
AP chỉ 0.43. Điểm em muốn nhấn mạnh là: khi nhìn vào một con số tổng hợp
mAP 0.83, nó che đi vấn đề của một class cụ thể. Vì vậy em luôn phân tích
per-class thay vì chỉ nhìn con số trung bình. Đây cũng là lý do em không
nói 'model đạt 83% accuracy' vì mAP không phải accuracy."

Nếu bị hỏi:
- "mAP@0.5 khác mAP@0.5:0.95 thế nào?"
  Trả lời: "mAP@0.5 tính với IoU threshold 0.5, nghĩa là bbox predict phải
  overlap ít nhất 50% với ground truth. mAP@0.5:0.95 trung bình từ 0.5 đến
  0.95 nên nghiêm khắt hơn về độ chính xác localization và thường thấp hơn
  đáng kể, ở đây là ~0.60."

## 20.4. results.png — Biểu đồ quá trình training

Ý nghĩa:
- 10 biểu đồ con theo 100 epoch.
- Hàng trên: train loss và metric.
- Hàng dưới: val loss và mAP.
- Đường xanh = actual, đường cam = smoothed.

Điểm chính cần đọc:
- Cả train và val loss giảm song song → không overfit.
- mAP@0.5 đạt ~0.838 và vẫn đang có xu hướng tăng ở epoch 100.
- Recall (~0.757) thấp hơn precision (~0.899) → model hơi conservative.

Script nói:

"Đây là biểu đồ training 100 epoch. Hai điểm em muốn show: thứ nhất,
train loss và val loss đều giảm song song, val không tăng ngược chiều,
có nghĩa model học được mà không bị overfit. Thứ hai, mAP@0.5 ở cuối
khoảng 0.838 và đường xu hướng vẫn hơi dốc lên, nghĩa là nếu train thêm
thì metric có thể cải thiện. Tuy nhiên với mục tiêu prototype end-to-end
thì 100 epoch là đủ để chứng minh pipeline hoạt động. Điểm đáng chú ý
là recall thấp hơn precision một chút, nghĩa là model bỏ sót nhiều hơn
là detect nhầm — với bài toán tracking như này thì chấp nhận được vì
detection nhầm gây nhiễu pipeline nhiều hơn là bỏ sót."

Nếu bị hỏi:
- "Tại sao không train thêm epoch?"
  Trả lời: "Mục tiêu là prototype end-to-end pipeline, không phải tối ưu
  model. Thêm nữa, model best.pt được lưu theo best val mAP trong quá
  trình train, không nhất thiết phải là epoch cuối cùng."


# PHẦN 21. CÂU HỎI VỀ TRAINING PROCESS

**Q33. Tại sao chọn yolov5x mà không phải yolov5s, m, hay l?**

**A:** yolov5x là variant lớn nhất trong dòng YOLOv5, có độ chính xác cao hơn
nhưng chậm hơn. Với bài toán offline (không cần real-time) và muốn chứng
minh pipeline end-to-end, ưu tiên accuracy hơn speed là hợp lý. Nếu cần
inference nhanh hơn, có thể thử yolov5m hoặc yolov5l và so sánh metric.

**Q34. batch=4 nhỏ vậy có ảnh hưởng gì?**

**A:** Batch nhỏ thường do giới hạn VRAM. Batch nhỏ làm gradient noisy hơn,
training có thể kém ổn định hơn và cần learning rate điều chỉnh tương ứng.
Ultralytics có gradient accumulation để mô phỏng effective batch lớn hơn.
Với batch=4 và nbs=64 trong args.yaml, effective batch thực tế là 64.

**Q35. Tại sao thư mục tên là train7 chứ không phải train1?**

**A:** YOLO Ultralytics tự đặt tên thư mục output tăng dần: train, train2,
train3,... Tên train7 có nghĩa đã có ít nhất 6 lần chạy training trước đó,
có thể ở cùng máy hoặc thư mục đã bị xóa. Đây là artifact Windows path
ghi trong args.yaml cho thấy training chạy trên Windows.

**Q36. Dataset từ đâu, license là gì?**

**A:** Dataset từ Roboflow, tên football-players-detection, phiên bản 1, license
CC BY 4.0 nghĩa là có thể dùng tự do kể cả thương mại nếu ghi attribution.
Dataset có 4 class: ball, goalkeeper, player, referee. Tổng mẫu trong
training set gồm khoảng 12,228 player, 1,401 referee, 519 ball, 435 goalkeeper.

**Q37. Augmentation nào được dùng và tại sao?**

**A:** Theo args.yaml, các augmentation gồm:
- HSV shift (hsv_h=0.015, hsv_s=0.7, hsv_v=0.4): thay đổi màu sắc để
  model robust với ánh sáng và màu áo khác nhau.
- Translate (0.1) và Scale (0.5): thay đổi vị trí và kích thước object.
- Horizontal flip (fliplr=0.5): bóng đá đối xứng nên flip ngang hợp lý.
- Mosaic (1.0): ghép 4 ảnh thành 1, tăng diversity và context.
- Erasing (0.4): che ngẫu nhiên vùng ảnh để model robust với occlusion.

**Q38. Tại sao ball AP chỉ 0.43 dù đã train 100 epoch?**

**A:** Có 3 nguyên nhân chính:
1. Class imbalance: 519 ball vs 12,228 player, model bị bias về majority class.
2. Small object: bóng chỉ chiếm ~1-2% kích thước ảnh, sau resize về 640
   còn rất ít pixel để model học feature.
3. Motion blur và occlusion: bóng di chuyển nhanh và thường bị che.
Giải pháp là augment thêm mẫu ball, dùng focal loss với weight cao hơn cho
ball, tăng image size hoặc train detector riêng cho bóng.

**Q39. Khi nào nên dừng training, early stopping là gì?**

**A:** Early stopping dừng training khi val metric không cải thiện sau một số
epoch nhất định (patience). Trong config này patience=100 tức là sẽ chờ
100 epoch liên tiếp không cải thiện mới dừng, nên thực tế chạy đủ 100 epoch.
Model best.pt được lưu tại epoch có val mAP50-95 cao nhất, không nhất thiết
là epoch cuối. Epoch cuối được lưu thành last.pt.

**Q40. Pretrained=true có nghĩa gì?**

**A:** Model khởi tạo từ checkpoint yolov5x.pt đã được train trên COCO dataset
(80 class, hàng triệu ảnh). Thay vì train từ random weights, ta fine-tune
từ weights đã có feature tốt. Điều này giúp hội tụ nhanh hơn, cần ít data
hơn và thường cho accuracy tốt hơn, đặc biệt khi dataset nhỏ.


# PHẦN 22. CÂU HỎI BẪY THƯỜNG GẶP VÀ CÁCH TRẢ LỜI

Bẫy 1: "mAP 0.83 nghĩa là model đúng 83% đúng không?"

Sai. Đây là cách diễn giải phổ biến nhất nhưng hoàn toàn sai.

Trả lời đúng:
"Không ạ. mAP là mean Average Precision, tức là trung bình diện tích dưới
Precision-Recall curve qua các class. Nó không phải accuracy. Ví dụ model
có thể đúng 95% với player nhưng chỉ 43% với ball, và mAP 0.83 là con số
trung bình pha trộn hai giá trị đó. Accuracy theo nghĩa thông thường không
phải metric phù hợp cho detection vì background không có nhãn."

Bẫy 2: "Model này có dùng được real-time không?"

Trả lời đúng:
"Hiện tại chưa phù hợp real-time vì pipeline đọc toàn bộ video vào RAM
và xử lý offline. Để real-time cần dùng streaming frame-by-frame, giảm
batch size, tối ưu inference với TensorRT hoặc ONNX, và có thể detect
mỗi N frame rồi track ở giữa. Ngoài ra cần profile latency của từng
bước trong pipeline để biết bottleneck ở đâu."

Bẫy 3: "Tốc độ cầu thủ trong video có chính xác không?"

Trả lời đúng:
"Đây là ước lượng, không phải đo chính xác. Sai số đến từ nhiều nguồn
tích lũy: detection jitter từ bbox không hoàn toàn ổn định, ID switch
làm trajectory bị gán nhầm, camera motion estimate dùng sparse optical
flow chưa robust, homography hard-code cho một video cụ thể, và FPS
hard-code 24 trong khi video thực tế 25. Để đánh giá chính xác cần
ground truth GPS hoặc radar và tính MAE/RMSE. Em không thể khẳng định
độ chính xác tuyệt đối chỉ từ mAP của detector."

Bẫy 4: "K-Means phân đội chính xác không? Nếu cả hai đội mặc áo trắng thì sao?"

Trả lời đúng:
"K-Means màu áo là unsupervised heuristic, không đảm bảo đúng trong mọi
trường hợp. Nếu hai đội mặc màu gần nhau, hai cluster sẽ không tách được
rõ ràng. Giải pháp tốt hơn là chuyển sang HSV hoặc CIE Lab thay vì BGR
vì khoảng cách màu có ý nghĩa tri giác hơn, lấy màu đại diện từ nhiều
frame rồi majority vote thay vì chỉ frame đầu, và nếu cần thiết dùng
appearance embedding hoặc Re-ID kết hợp context sân."

Bẫy 5: "Optical Flow ước lượng camera chính xác không?"

Trả lời đúng:
"Chưa đủ robust. Cách hiện tại lấy feature có khoảng cách dịch chuyển
lớn nhất và gán đó là camera movement. Vấn đề là outlier hoặc feature
trên cầu thủ di chuyển nhanh có thể ảnh hưởng kết quả. Cách tốt hơn là
lấy median của nhiều flow vector sau khi lọc outlier, hoặc dùng RANSAC
để estimate affine transform từ nhiều điểm nền. Ngoài ra code chỉ mô hình
hóa translation X/Y, chưa xử lý zoom và rotation camera."

Bẫy 6: "Homography có áp dụng được cho mọi điểm trong ảnh không?"

Trả lời đúng:
"Không. Homography mô tả quan hệ projective giữa hai mặt phẳng, chỉ đúng
khi các điểm nằm trên cùng một mặt phẳng. Trong dự án, em dùng foot point
vì chân tiếp xúc mặt sân. Nếu áp dụng cho đầu hoặc toàn bbox như thể chúng
nằm trên mặt sân thì kết quả sẽ sai. Đây cũng là lý do cầu thủ cao hay thấp
có cùng foot point nhưng bbox center khác nhau đáng kể."

Bẫy 7: "File create_interview_deck.py trong repo để làm gì vậy?"

Trả lời đúng:
"Đây là script tạo slide PowerPoint phỏng vấn bằng python-pptx. Em viết nó
để chuẩn bị một bộ slide chuyên nghiệp trình bày hai dự án, giải thích kiến
trúc kỹ thuật và liên hệ với bài toán AEC. Script tự động hóa việc tạo
slide, layout và màu sắc hoàn toàn bằng code thay vì kéo thả thủ công. Nó
cũng có speaker notes chi tiết cho từng slide. Em để trong repo vì nó là
artifact của quá trình chuẩn bị, không phải phần pipeline chính."

Bẫy 8: "Tại sao possession được tính bằng khoảng cách pixel mà không phải
khoảng cách mét?"

Trả lời đúng:
"Đây là hạn chế của phiên bản hiện tại. Lý tưởng là đo khoảng cách sau
homography bằng mét thực để ngưỡng 70 pixel không thay đổi ý nghĩa khi
camera zoom hay đổi góc. Ngoài ra possession hiện tại không có temporal
smoothing nên có thể nhảy liên tục giữa các cầu thủ. Cải tiến đúng hướng
là dùng khoảng cách mét, yêu cầu cầu thủ gần bóng liên tục N frame và
thêm trạng thái loose ball khi không ai đủ gần."

Bẫy 9: "player_id 91 hard-code thành team 1 là gì vậy?"

Trả lời đúng:
"Đây là workaround tạm thời để fix lỗi phân loại thủ môn trong video cụ
thể đó. Track ID 91 trong video mẫu là thủ môn và K-Means màu áo phân sai
đội. Thay vì sửa đúng nguyên nhân gốc, code dùng hard-code để video output
trông đúng. Đây rõ ràng là nợ kỹ thuật cần loại bỏ trước khi dùng với
video khác, vì ID 91 trong video khác có thể là cầu thủ bất kỳ."

Bẫy 10: "Nếu em chạy code này trên video khác thì có hoạt động không?"

Trả lời đúng:
"Không đảm bảo vì có nhiều thứ hard-code cho video mẫu cụ thể: bốn điểm
calibration homography, mask optical flow theo độ phân giải 1920x1080, FPS
24, workaround ID 91, và đường dẫn input/output. Để chạy video khác cần
re-calibrate bốn điểm sân, kiểm tra độ phân giải, đọc FPS từ metadata
và bỏ workaround ID. Đây là lý do em gọi đây là prototype, không phải
generalized tool."


# HẾT TÀI LIỆU
