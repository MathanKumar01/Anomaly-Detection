from collections import defaultdict, deque


class FallDetector:

    def __init__(self, history_size=15, max_missing=60):

        # Pose history for every tracked person
        self.pose_history = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        self.missing_frames = defaultdict(int)
        self.max_missing = max_missing

    def update(self, track_id, stable_pose):

        self.missing_frames[track_id] = 0

        # Save latest stable pose
        self.pose_history[track_id].append(stable_pose)

        history = list(self.pose_history[track_id])

        # Default output
        result = {
            "track_id": track_id,
            "fall_detected": False,
            "reason": "NORMAL",
            "history": history
        }

        # Need enough history (at least 4 frames)
        if len(history) < 4:
            return result

        # -----------------------------
        # Check Transition (Upright to Lying)
        # -----------------------------
        has_upright_prior = any(p in ["STANDING", "SITTING"] for p in history[:-2])
        is_currently_lying = len(history) >= 2 and all(p == "LYING" for p in history[-2:])

        if has_upright_prior and is_currently_lying:
            result["fall_detected"] = True
            result["reason"] = "PERSON FELL"

        return result

    def prune_stale_tracks(self, active_track_ids):
        for track_id in list(self.pose_history.keys()):
            if track_id not in active_track_ids:
                self.missing_frames[track_id] += 1
                if self.missing_frames[track_id] > self.max_missing:
                    del self.pose_history[track_id]
                    del self.missing_frames[track_id]