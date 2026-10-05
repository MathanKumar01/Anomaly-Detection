class EventReasoner:

    def __init__(self):
        pass

    def analyze(self, scene_state, crowd, fall_results=None):

        events = []
        fall_map = {}

        if fall_results:
            for f in fall_results:
                if f.get("fall_detected"):
                    fall_map[f["track_id"]] = f

        for person in scene_state:

            track_id = person["track_id"]
            event = "NORMAL"
            confidence = 0.50

            speed = person.get("current_speed", 0)
            motion = person.get("current_motion", 0)
            risk = person.get("current_risk", "NORMAL")
            interactions = person.get("interaction_count", 0)
            direction_changes = person.get(
                "current_direction_changes",
                person.get("direction_changes", 0)
            )

            # -----------------------------
            # Specific Checks (High Priority)
            # -----------------------------
            # 1. Fall Detection
            if track_id in fall_map:
                event = "FALL ACCIDENT"
                confidence = 0.95

            # 2. Fight Detection (Checked before generic High Risk)
            elif (
                (motion >= 12 and interactions >= 1 and direction_changes >= 2)
                or (risk in ["HIGH RISK", "CRITICAL"] and interactions >= 1 and motion >= 10)
            ):
                event = "FIGHT"
                confidence = 0.92

            # 3. Running / Fleeing
            elif speed >= 5.0 and motion >= 7.0:
                event = "RUNNING"
                confidence = 0.85

            # 4. Critical Event (Non-fight extreme danger)
            elif risk == "CRITICAL":
                event = "CRITICAL EVENT"
                confidence = 0.90

            # 5. High Risk Event
            elif risk == "HIGH RISK":
                event = "HIGH RISK EVENT"
                confidence = 0.85

            # 6. Suspicious Behavior
            elif risk == "SUSPICIOUS":
                event = "SUSPICIOUS"
                confidence = 0.70

            events.append({
                "track_id": track_id,
                "event": event,
                "confidence": round(confidence, 2)
            })

        # -----------------------------
        # Scene-Level Events: Crowd Panic
        # -----------------------------
        if (
            crowd.get("people_count", 0) >= 4
            and crowd.get("scene_risk") in ["HIGH RISK", "SUSPICIOUS"]
        ):
            events.append({
                "track_id": "SCENE",
                "event": "CROWD PANIC",
                "confidence": 0.90
            })

        return events