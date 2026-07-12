from collections import defaultdict, deque


class RiskSmoother:

    def __init__(self, window_size=20):

        # Number of frames used for smoothing
        self.window_size = window_size

        # Store recent scores for every track
        self.score_history = defaultdict(
            lambda: deque(maxlen=window_size)
        )

    # ==========================================
    # Smooth Risk Scores
    # ==========================================

    def smooth(self, decisions):

        smoothed_decisions = []

        for decision in decisions:

            track_id = decision["track_id"]

            score = decision["score"]

            # Store score history
            self.score_history[track_id].append(score)

            history = self.score_history[track_id]

            average_score = sum(history) / len(history)

            # ------------------------------------
            # Stable Decision
            # ------------------------------------

            if average_score >= 80:

                status = "CRITICAL"

            elif average_score >= 60:

                status = "HIGH RISK"

            elif average_score >= 30:

                status = "SUSPICIOUS"

            else:

                status = "NORMAL"

            smoothed = decision.copy()

            smoothed["raw_score"] = score

            smoothed["score"] = round(average_score, 2)

            smoothed["status"] = status

            smoothed_decisions.append(smoothed)

        return smoothed_decisions