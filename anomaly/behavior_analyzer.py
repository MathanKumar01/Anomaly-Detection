import math

class BehaviorAnalyzer:

    def __init__(self):

        self.previous_positions = {}
        self.time_in_scene = {}

    def analyze(self, features):

        behaviors = []

        for obj in features:

            if obj["object"] != "person":
                continue

            track_id = obj["track_id"]

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

                "speed": round(speed,2),

                "direction": direction,

                "time": self.time_in_scene[track_id]

            })

        return behaviors