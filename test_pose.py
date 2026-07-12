import cv2

from detector.pose_detector import PoseDetector
from anomaly.pose_analyzer import PoseAnalyzer

cap = cv2.VideoCapture(
    r"C:\projects\anamoly_detection\dataset\Assault018_x264.mp4"
)

pose_detector = PoseDetector()
pose_analyzer = PoseAnalyzer()

frame_number = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    results = pose_detector.detect(frame)

    poses = pose_analyzer.analyze(results)

    print(f"\nFrame : {frame_number}")

    if len(poses) == 0:
        print("No valid pose detected")

    else:

        for pose in poses:

            print(
                f"Person {pose['person_id']} : {pose['pose']}"
            )

    annotated = results[0].plot()

    cv2.imshow("YOLO Pose", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()