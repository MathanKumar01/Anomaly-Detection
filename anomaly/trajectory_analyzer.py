from collections import defaultdict

class TrajectoryAnalyzer:

    def __init__(self, max_points=30):

        self.max_points = max_points
        self.trajectories = defaultdict(list)

    def update(self, behaviors):

        trajectory_info = []

        for person in behaviors:

            track_id = person["track_id"]

            point = (person["x"], person["y"])

            self.trajectories[track_id].append(point)

            # Keep only the last N points
            if len(self.trajectories[track_id]) > self.max_points:
                self.trajectories[track_id].pop(0)

            direction_changes = self._count_direction_changes(
                self.trajectories[track_id]
            )

            trajectory_info.append({

                "track_id": track_id,

                "trajectory": self.trajectories[track_id],

                "trajectory_length": len(self.trajectories[track_id]),

                "direction_changes": direction_changes

            })

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