import numpy as np


class PoseAnalyzer:

    def __init__(self):
        pass

    def analyze(self, pose_results):

        poses = []

        if len(pose_results) == 0:
            return poses

        result = pose_results[0]

        if result.keypoints is None:
            return poses

        try:
            keypoints = result.keypoints.xy.cpu().numpy()
        except Exception:
            return poses

        # Track IDs if model.track() was used on pose model
        ids = None
        if hasattr(result, "boxes") and result.boxes is not None and result.boxes.id is not None:
            ids = result.boxes.id.int().cpu().tolist()

        for person_idx, person in enumerate(keypoints):

            if person is None or len(person) == 0 or person.shape[0] < 17:
                continue

            if np.isnan(person).any():
                continue

            # Check if keypoints are non-zero (detected)
            valid_pts = person[person[:, 0] > 0]
            if len(valid_pts) < 6:
                continue

            left_shoulder = person[5]
            right_shoulder = person[6]

            left_hip = person[11]
            right_hip = person[12]

            left_knee = person[13]
            right_knee = person[14]

            left_ankle = person[15]
            right_ankle = person[16]

            # Average positions
            shoulder_y = (left_shoulder[1] + right_shoulder[1]) / 2.0
            shoulder_x = (left_shoulder[0] + right_shoulder[0]) / 2.0

            hip_y = (left_hip[1] + right_hip[1]) / 2.0
            hip_x = (left_hip[0] + right_hip[0]) / 2.0

            knee_y = (left_knee[1] + right_knee[1]) / 2.0
            ankle_y = (left_ankle[1] + right_ankle[1]) / 2.0

            min_y = np.min(valid_pts[:, 1])
            max_y = np.max(valid_pts[:, 1])
            min_x = np.min(valid_pts[:, 0])
            max_x = np.max(valid_pts[:, 0])

            body_h = max(max_y - min_y, 1.0)
            body_w = max(max_x - min_x, 1.0)
            aspect_ratio = body_w / body_h

            dx = abs(hip_x - shoulder_x)
            dy = abs(hip_y - shoulder_y)
            torso_angle_deg = float(np.degrees(np.arctan2(dy, dx + 1e-5)))

            # -----------------------------
            # Scale-Invariant Pose Classification
            # -----------------------------
            # If torso is nearly horizontal or width dominates height -> LYING
            if torso_angle_deg < 35.0 or (aspect_ratio > 1.25 and dy < 0.3 * body_w):
                pose = "LYING"
            # If hips and knees are close in vertical height -> SITTING
            elif shoulder_y < hip_y and abs(hip_y - knee_y) < (0.15 * body_h):
                pose = "SITTING"
            # If vertical hierarchy holds -> STANDING
            elif shoulder_y < hip_y:
                pose = "STANDING"
            else:
                pose = "UNKNOWN"

            track_id = ids[person_idx] if (ids and person_idx < len(ids)) else person_idx

            poses.append({
                "person_id": person_idx,
                "track_id": track_id,
                "pose": pose,
                "torso_angle": round(torso_angle_deg, 1),
                "aspect_ratio": round(aspect_ratio, 2),
                "center_x": round(float((min_x + max_x) / 2.0), 2),
                "center_y": round(float((min_y + max_y) / 2.0), 2),
                "shoulder_y": round(float(shoulder_y), 2),
                "hip_y": round(float(hip_y), 2),
                "knee_y": round(float(knee_y), 2),
                "ankle_y": round(float(ankle_y), 2)
            })

        return poses