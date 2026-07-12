class ThreatPrioritizer:

    def __init__(self):

        self.priority_table = {

            "CRITICAL EVENT": 1,

            "FIGHT": 2,

            "HIGH RISK EVENT": 3,

            "CROWD PANIC": 4,

            "ACCIDENT": 5,

            "RUNNING": 6,

            "SUSPICIOUS": 7,

            "NORMAL": 8

        }

    # ==========================================
    # Find Highest Priority Event
    # ==========================================

    def analyze(self, events):

        if len(events) == 0:

            return None

        highest = None

        highest_priority = 999

        for event in events:

            priority = self.priority_table.get(
                event["event"],
                999
            )

            if priority < highest_priority:

                highest_priority = priority

                highest = {

                    "track_id": event["track_id"],

                    "event": event["event"],

                    "confidence": event["confidence"],

                    "priority": priority

                }

        return highest