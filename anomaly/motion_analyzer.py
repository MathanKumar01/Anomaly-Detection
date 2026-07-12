import math

class MotionAnalyzer:

    def __init__(self):

        self.previous_speed = {}
        self.previous_direction = {}

    def analyze(self, behaviors):

        motion_results = []

        for person in behaviors:

            track_id = person["track_id"]

            speed = person["speed"]

            direction = person["direction"]

            # --------------------
            # Acceleration
            # --------------------

            acceleration = 0

            if track_id in self.previous_speed:

                acceleration = speed - self.previous_speed[track_id]

            self.previous_speed[track_id] = speed

            # --------------------
            # Direction Change
            # --------------------

            direction_changed = False

            if track_id in self.previous_direction:

                if self.previous_direction[track_id] != direction:
                    direction_changed = True

            self.previous_direction[track_id] = direction

            # --------------------
            # Motion Intensity
            # --------------------

            motion_score = abs(speed) + abs(acceleration)

            motion_results.append({

                "track_id": track_id,

                "speed": round(speed,2),

                "acceleration": round(acceleration,2),

                "direction_changed": direction_changed,

                "motion_score": round(motion_score,2)

            })

        return motion_results