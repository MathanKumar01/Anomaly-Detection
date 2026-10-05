from collections import defaultdict, deque
from collections import Counter


class PoseMemory:

    def __init__(self, history_size=10, max_missing=60):

        # Store pose history for each person
        self.pose_history = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        self.missing_frames = defaultdict(int)
        self.max_missing = max_missing

    def update(self, track_id, pose):

        self.missing_frames[track_id] = 0

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

    def prune_stale_tracks(self, active_track_ids):
        for track_id in list(self.pose_history.keys()):
            if track_id not in active_track_ids:
                self.missing_frames[track_id] += 1
                if self.missing_frames[track_id] > self.max_missing:
                    del self.pose_history[track_id]
                    del self.missing_frames[track_id]