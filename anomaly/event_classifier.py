class EventClassifier:

    def __init__(self):
        pass

    def classify(
        self,
        decisions,
        crowd,
        fall_results,
        interactions,
        motion_results
    ):

        events = []

        for decision in decisions:

            track_id = decision["track_id"]

            event = "NORMAL"

            # ----------------------------
            # Default Values
            # ----------------------------

            risk = decision["score"]

            status = decision["status"]

            fall = False

            motion_score = 0

            close_people = 0

            # ----------------------------
            # Motion
            # ----------------------------

            for motion in motion_results:

                if motion["track_id"] == track_id:

                    motion_score = motion["motion_score"]

            # ----------------------------
            # Fall Detection
            # ----------------------------

            for result in fall_results:

                if result["track_id"] == track_id:

                    fall = result["fall_detected"]

            # ----------------------------
            # Interaction
            # ----------------------------

            for interaction in interactions:

                if interaction["status"] == "Close":

                    if (
                        interaction["person1"] == track_id or
                        interaction["person2"] == track_id
                    ):

                        close_people += 1

            # ----------------------------
            # Event Rules
            # ----------------------------

            if fall:

                event = "FALL ACCIDENT"

            elif (

                motion_score > 8 and

                close_people >= 1 and

                crowd["scene_risk"] == "HIGH RISK"

            ):

                event = "FIGHT"

            elif (

                crowd["crowd_density"] == "HIGH"

            ):

                event = "CROWD"

            elif status == "SUSPICIOUS":

                event = "SUSPICIOUS"

            events.append({

                "track_id": track_id,

                "event": event

            })

        return events