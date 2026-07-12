class IncidentTimeline:

    def __init__(self):

        # Timeline for each person
        self.timeline = {}

        # Last recorded event
        self.last_event = {}

        # Last frame the person was seen
        self.last_seen = {}

    # =====================================================
    # Update Timeline
    # =====================================================

    def update(
        self,
        frame_number,
        behaviors,
        decisions,
        events,
        highest_threat
    ):

        active_tracks = set()

        # -----------------------------------------
        # New Persons
        # -----------------------------------------

        for person in behaviors:

            track_id = person["track_id"]

            active_tracks.add(track_id)

            self.last_seen[track_id] = frame_number

            if track_id not in self.timeline:

                self.timeline[track_id] = []

                self.timeline[track_id].append({

                    "frame": frame_number,

                    "event": "ENTERED SCENE"

                })

                self.last_event[track_id] = "ENTERED SCENE"

        # -----------------------------------------
        # Decision Engine
        # -----------------------------------------

        for decision in decisions:

            track_id = decision["track_id"]

            if track_id not in active_tracks:
                continue

            status = decision["status"]

            if status == "NORMAL":
                continue

            if self.last_event.get(track_id) != status:

                self.timeline[track_id].append({

                    "frame": frame_number,

                    "event": status

                })

                self.last_event[track_id] = status

        # -----------------------------------------
        # Event Reasoner
        # -----------------------------------------

        for event in events:

            if event["track_id"] == "SCENE":
                continue

            track_id = event["track_id"]

            if track_id not in active_tracks:
                continue

            event_name = event["event"]

            if event_name == "NORMAL":
                continue

            if self.last_event.get(track_id) != event_name:

                self.timeline[track_id].append({

                    "frame": frame_number,

                    "event": event_name

                })

                self.last_event[track_id] = event_name

        # -----------------------------------------
        # Highest Threat
        # -----------------------------------------

        if highest_threat is not None:

            track_id = highest_threat["track_id"]

            # Ignore scene events
            if track_id != "SCENE":

                if track_id not in self.timeline:

                    self.timeline[track_id] = []

                threat = "HIGHEST THREAT"

                if self.last_event.get(track_id) != threat:

                    self.timeline[track_id].append({

                        "frame": frame_number,

                        "event": threat

                    })

                    self.last_event[track_id] = threat

        # -----------------------------------------
        # Left Scene
        # -----------------------------------------

        remove_tracks = []

        for track_id in list(self.last_seen.keys()):

            if track_id in active_tracks:
                continue

            # Not seen for 30 frames
            if frame_number - self.last_seen[track_id] > 30:

                if self.last_event.get(track_id) != "LEFT SCENE":

                    self.timeline[track_id].append({

                        "frame": frame_number,

                        "event": "LEFT SCENE"

                    })

                    self.last_event[track_id] = "LEFT SCENE"

                remove_tracks.append(track_id)

        # Remove inactive tracks
        for track_id in remove_tracks:

            del self.last_seen[track_id]

        return self.timeline

    # =====================================================
    # Print Timeline
    # =====================================================

    def print_timeline(self):

        print("\n========== INCIDENT TIMELINE ==========")

        for track_id in sorted(self.timeline.keys()):

            history = self.timeline[track_id]

            # Skip if only ENTERED SCENE exists
            if len(history) == 1 and history[0]["event"] == "ENTERED SCENE":
                continue

            print("--------------------------------")

            print(f"Track ID : {track_id}")

            for item in history:

                print(
                    f"Frame {item['frame']} : {item['event']}"
                )