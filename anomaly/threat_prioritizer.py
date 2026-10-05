class ThreatPrioritizer:

    def __init__(self):

        self.priority_table = {
            "CRITICAL EVENT": 1,
            "FALL ACCIDENT": 2,
            "FIGHT": 3,
            "HIGH RISK EVENT": 4,
            "CROWD PANIC": 5,
            "ACCIDENT": 6,
            "RUNNING": 7,
            "SUSPICIOUS": 8,
            "NORMAL": 9
        }

    # ==========================================
    # Find Highest Priority Event
    # ==========================================

    def analyze(self, events):

        if not events:
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