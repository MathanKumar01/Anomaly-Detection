import math

class InteractionAnalyzer:

    def __init__(self):

        self.distance_threshold = 80

    def analyze(self, behaviors):

        interactions = []

        for i in range(len(behaviors)):

            for j in range(i + 1, len(behaviors)):

                p1 = behaviors[i]
                p2 = behaviors[j]

                distance = math.sqrt(
                    (p1["x"] - p2["x"]) ** 2 +
                    (p1["y"] - p2["y"]) ** 2
                )

                status = "Far"

                if distance < self.distance_threshold:
                    status = "Close"

                interactions.append({

                    "person1": p1["track_id"],

                    "person2": p2["track_id"],

                    "distance": round(distance,2),

                    "status": status

                })

        return interactions