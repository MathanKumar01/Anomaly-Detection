import math


class CrowdAnalyzer:

    def __init__(self):

        self.close_distance = 100

    def analyze(self, behaviors):

        people_count = len(behaviors)

        if people_count == 0:

            return {
                "people_count": 0,
                "close_pairs": 0,
                "crowd_density": "Empty",
                "scene_risk": "NORMAL"
            }

        close_pairs = 0

        for i in range(len(behaviors)):

            for j in range(i + 1, len(behaviors)):

                x1 = behaviors[i]["x"]
                y1 = behaviors[i]["y"]

                x2 = behaviors[j]["x"]
                y2 = behaviors[j]["y"]

                distance = math.sqrt(
                    (x1 - x2) ** 2 +
                    (y1 - y2) ** 2
                )

                if distance < self.close_distance:

                    close_pairs += 1

        # --------------------------
        # Crowd Density
        # --------------------------

        if people_count <= 2:

            density = "LOW"

        elif people_count <= 5:

            density = "MEDIUM"

        else:

            density = "HIGH"

        # --------------------------
        # Scene Risk
        # --------------------------

        if density == "HIGH" and close_pairs >= 5:

            scene = "HIGH RISK"

        elif density == "MEDIUM" and close_pairs >= 2:

            scene = "SUSPICIOUS"

        else:

            scene = "NORMAL"

        return {

            "people_count": people_count,

            "close_pairs": close_pairs,

            "crowd_density": density,

            "scene_risk": scene

        }