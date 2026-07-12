from collections import defaultdict, deque
from collections import Counter


class PoseMemory:

    def __init__(self, history_size=10):

        # Store pose history for each person
        self.pose_history = defaultdict(
            lambda: deque(maxlen=history_size)
        )

    def update(self, track_id, pose):

        # Add new pose
        self.pose_history[track_id].append(pose)

        history = list(self.pose_history[track_id])

        # Majority Vote
        counter = Counter(history)

        stable_pose = counter.most_common(1)[0][0]

        return {

            "track_id": track_id,

            "history": history,

            "stable_pose": stable_pose

        }