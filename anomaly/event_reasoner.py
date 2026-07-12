class EventReasoner:

    def __init__(self):
        pass

    def analyze(self, scene_state, crowd):

        events = []

        for person in scene_state:

            event = "NORMAL"
            confidence = 0.50

            speed = person["current_speed"]
            motion = person["current_motion"]
            risk = person["current_risk"]
            interactions = person["interaction_count"]
            direction_changes = person.get(
                "current_direction_changes",
                person.get("direction_changes", 0)
            )

            # -----------------------------
            # High Risk / Critical
            # -----------------------------
            if risk in ["HIGH RISK", "CRITICAL"]:
                event = "HIGH RISK EVENT"
                confidence = 0.95

            # -----------------------------
            # Fight
            # -----------------------------
            elif (
                motion > 15
                and interactions >= 1
                and direction_changes >= 3
            ):
                event = "FIGHT"
                confidence = 0.90

            # -----------------------------
            # Suspicious
            # -----------------------------
            elif risk == "SUSPICIOUS":
                event = "SUSPICIOUS"
                confidence = 0.75

            # -----------------------------
            # Running
            # -----------------------------
            elif speed > 5 and motion > 8:
                event = "RUNNING"
                confidence = 0.80

            events.append({

                "track_id": person["track_id"],

                "event": event,

                "confidence": round(confidence, 2)

            })

        # -----------------------------
        # Crowd Panic
        # -----------------------------

        if (
            crowd["people_count"] >= 5
            and crowd["scene_risk"] != "NORMAL"
        ):

            events.append({

                "track_id": "SCENE",

                "event": "CROWD PANIC",

                "confidence": 0.95

            })

        return events