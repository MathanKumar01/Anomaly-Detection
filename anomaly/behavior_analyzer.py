import math


class BehaviorAnalyzer:

    def __init__(self, max_missing=60):

        self.previous_positions = {}
        self.time_in_scene = {}
        self.missing_frames = {}
        self.max_missing = max_missing

    def analyze(self, features):

        behaviors = []
        active_tracks = set()

        for obj in features:

            if obj["object"] != "person":
                continue

            track_id = obj["track_id"]
            if track_id is None or track_id < 0:
                continue

            active_tracks.add(track_id)
            self.missing_frames[track_id] = 0

            x = obj["center_x"]
            y = obj["center_y"]

            speed = 0
            direction = "STILL"

            # Count how long the person stays in the scene
            if track_id not in self.time_in_scene:
                self.time_in_scene[track_id] = 1
            else:
                self.time_in_scene[track_id] += 1

            # Calculate movement
            if track_id in self.previous_positions:

                prev_x, prev_y = self.previous_positions[track_id]

                dx = x - prev_x
                dy = y - prev_y

                speed = math.sqrt(dx**2 + dy**2)

                # Direction
                if abs(dx) > abs(dy):

                    if dx > 0:
                        direction = "RIGHT"
                    else:
                        direction = "LEFT"

                else:

                    if dy > 0:
                        direction = "DOWN"
                    else:
                        direction = "UP"

            self.previous_positions[track_id] = (x, y)

            behaviors.append({

                "track_id": track_id,

                "x": x,

                "y": y,

                "speed": round(speed, 2),

                "direction": direction,

                "time": self.time_in_scene[track_id]

            })

        # Prune inactive tracks
        for track_id in list(self.previous_positions.keys()):
            if track_id not in active_tracks:
                self.missing_frames[track_id] = self.missing_frames.get(track_id, 0) + 1
                if self.missing_frames[track_id] > self.max_missing:
                    self.previous_positions.pop(track_id, None)
                    self.time_in_scene.pop(track_id, None)
                    self.missing_frames.pop(track_id, None)

        return behaviors