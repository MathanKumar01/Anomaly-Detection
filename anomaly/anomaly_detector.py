class AnomalyDetector:

    def __init__(self):

        self.speed_threshold = 4.0
        self.time_threshold = 300

    def detect(self, behaviors):

        alerts = []

        for person in behaviors:

            score = 0

            # Speed
            if person["speed"] > self.speed_threshold:
                score += 0.5

            # Staying too long
            if person["time"] > self.time_threshold:
                score += 0.3

            # Frequent direction changes
            if person["direction"] in ["LEFT", "RIGHT"]:
                score += 0.2

            # Decide status
            if score >= 0.7:
                status = "HIGH RISK"

            elif score >= 0.4:
                status = "MEDIUM RISK"

            else:
                status = "NORMAL"

            alerts.append({

                "track_id": person["track_id"],
                "score": round(score, 2),
                "status": status

            })

        return alerts