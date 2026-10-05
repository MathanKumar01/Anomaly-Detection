from collections import defaultdict, deque


class TrajectoryAnalyzer:

    def __init__(self, max_points=30, max_missing=60):

        self.max_points = max_points
        self.max_missing = max_missing
        self.trajectories = defaultdict(lambda: deque(maxlen=max_points))
        self.missing_frames = defaultdict(int)

    def update(self, behaviors):

        trajectory_info = []
        active_tracks = set()

        for person in behaviors:

            track_id = person["track_id"]
            if track_id is None or track_id < 0:
                continue

            active_tracks.add(track_id)
            self.missing_frames[track_id] = 0

            point = (person["x"], person["y"])
            self.trajectories[track_id].append(point)

            pts_list = list(self.trajectories[track_id])
            direction_changes = self._count_direction_changes(pts_list)

            trajectory_info.append({
                "track_id": track_id,
                "trajectory": pts_list,
                "trajectory_length": len(pts_list),
                "direction_changes": direction_changes
            })

        # Prune inactive tracks
        for track_id in list(self.trajectories.keys()):
            if track_id not in active_tracks:
                self.missing_frames[track_id] += 1
                if self.missing_frames[track_id] > self.max_missing:
                    del self.trajectories[track_id]
                    del self.missing_frames[track_id]

        return trajectory_info

    def _count_direction_changes(self, points):

        if len(points) < 3:
            return 0

        directions = []

        for index in range(1, len(points)):

            prev_x, prev_y = points[index - 1]
            curr_x, curr_y = points[index]

            dx = curr_x - prev_x
            dy = curr_y - prev_y

            if abs(dx) > abs(dy):
                directions.append("RIGHT" if dx > 0 else "LEFT")
            else:
                directions.append("DOWN" if dy > 0 else "UP")

        changes = 0

        for index in range(1, len(directions)):
            if directions[index] != directions[index - 1]:
                changes += 1

        return changes