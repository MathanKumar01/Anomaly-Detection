from collections import defaultdict, deque


class RiskSmoother:

    CRITICAL_THRESHOLD = 70
    HIGH_RISK_THRESHOLD = 45
    SUSPICIOUS_THRESHOLD = 20

    def __init__(self, window_size=20, max_missing=60):

        # Number of frames used for smoothing
        self.window_size = window_size
        self.max_missing = max_missing

        # Store recent scores for every track
        self.score_history = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self.missing_frames = defaultdict(int)

    # ==========================================
    # Smooth Risk Scores
    # ==========================================

    def smooth(self, decisions):

        smoothed_decisions = []
        active_tracks = set()

        for decision in decisions:

            track_id = decision["track_id"]
            if track_id is not None and track_id >= 0:
                active_tracks.add(track_id)
                self.missing_frames[track_id] = 0

            score = decision["score"]

            # Store score history
            self.score_history[track_id].append(score)

            history = self.score_history[track_id]

            average_score = sum(history) / len(history)

            # ------------------------------------
            # Stable Decision (Synchronized with DecisionEngine)
            # ------------------------------------

            if average_score >= self.CRITICAL_THRESHOLD:

                status = "CRITICAL"

            elif average_score >= self.HIGH_RISK_THRESHOLD:

                status = "HIGH RISK"

            elif average_score >= self.SUSPICIOUS_THRESHOLD:

                status = "SUSPICIOUS"

            else:

                status = "NORMAL"

            smoothed = decision.copy()

            smoothed["raw_score"] = score

            smoothed["score"] = round(average_score, 2)

            smoothed["status"] = status

            smoothed_decisions.append(smoothed)

        # Clean up stale tracks
        for track_id in list(self.score_history.keys()):
            if track_id not in active_tracks:
                self.missing_frames[track_id] += 1
                if self.missing_frames[track_id] > self.max_missing:
                    del self.score_history[track_id]
                    del self.missing_frames[track_id]

        return smoothed_decisions