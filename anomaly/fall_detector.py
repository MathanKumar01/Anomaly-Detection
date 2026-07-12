from collections import defaultdict, deque


class FallDetector:

    def __init__(self, history_size=15):

        # Pose history for every tracked person
        self.pose_history = defaultdict(
            lambda: deque(maxlen=history_size)
        )

    def update(self, track_id, stable_pose):

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

        # Need enough history
        if len(history) < 6:
            return result

        # -----------------------------
        # Check Transition
        # -----------------------------

        if (

            "STANDING" in history[:3]

            and

            history[-3:] == [
                "LYING",
                "LYING",
                "LYING"
            ]

        ):

            result["fall_detected"] = True

            result["reason"] = "PERSON FELL"

        return result