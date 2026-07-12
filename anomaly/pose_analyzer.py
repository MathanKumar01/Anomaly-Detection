import numpy as np


class PoseAnalyzer:

    def __init__(self):
        pass

    def analyze(self, pose_results):

        poses = []

        # ---------------------------------------
        # No pose results
        # ---------------------------------------

        if len(pose_results) == 0:
            return poses

        result = pose_results[0]

        # ---------------------------------------
        # No keypoints
        # ---------------------------------------

        if result.keypoints is None:
            return poses

        try:
            keypoints = result.keypoints.xy.cpu().numpy()
        except Exception:
            return poses

        # ---------------------------------------
        # Analyze each detected person
        # ---------------------------------------

        for person_id, person in enumerate(keypoints):

            # Skip empty detections
            if person is None:
                continue

            if len(person) == 0:
                continue

            # Must contain all 17 keypoints
            if person.shape[0] < 17:
                continue

            # Skip if keypoints contain NaN
            if np.isnan(person).any():
                continue

            pose = "UNKNOWN"

            # -----------------------------
            # Keypoints
            # -----------------------------

            left_shoulder = person[5]
            right_shoulder = person[6]

            left_hip = person[11]
            right_hip = person[12]

            left_knee = person[13]
            right_knee = person[14]

            left_ankle = person[15]
            right_ankle = person[16]

            # -----------------------------
            # Average Y Positions
            # -----------------------------

            shoulder_y = (
                left_shoulder[1] +
                right_shoulder[1]
            ) / 2

            hip_y = (
                left_hip[1] +
                right_hip[1]
            ) / 2

            knee_y = (
                left_knee[1] +
                right_knee[1]
            ) / 2

            ankle_y = (
                left_ankle[1] +
                right_ankle[1]
            ) / 2

            # -----------------------------
            # Pose Rules
            # -----------------------------

            # Standing
            if shoulder_y < hip_y < knee_y < ankle_y:
                pose = "STANDING"

            # Sitting
            elif abs(hip_y - knee_y) < 30:
                pose = "SITTING"

            # Lying
            elif abs(shoulder_y - hip_y) < 20:
                pose = "LYING"

            else:
                pose = "UNKNOWN"

            poses.append({

                "person_id": person_id,

                "pose": pose,

                "shoulder_y": round(float(shoulder_y), 2),

                "hip_y": round(float(hip_y), 2),

                "knee_y": round(float(knee_y), 2),

                "ankle_y": round(float(ankle_y), 2)

            })

        return poses