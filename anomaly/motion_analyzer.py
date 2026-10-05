class MotionAnalyzer:

    def __init__(self, max_missing=60):

        self.previous_speed = {}
        self.previous_direction = {}
        self.missing_frames = {}
        self.max_missing = max_missing

    def analyze(self, behaviors):

        motion_results = []
        active_tracks = set()

        for person in behaviors:

            track_id = person["track_id"]
            if track_id is None or track_id < 0:
                continue

            active_tracks.add(track_id)
            self.missing_frames[track_id] = 0

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
                "speed": round(speed, 2),
                "acceleration": round(acceleration, 2),
                "direction_changed": direction_changed,
                "motion_score": round(motion_score, 2)
            })

        # Prune inactive tracks
        for track_id in list(self.previous_speed.keys()):
            if track_id not in active_tracks:
                self.missing_frames[track_id] = self.missing_frames.get(track_id, 0) + 1
                if self.missing_frames[track_id] > self.max_missing:
                    self.previous_speed.pop(track_id, None)
                    self.previous_direction.pop(track_id, None)
                    self.missing_frames.pop(track_id, None)

        return motion_results