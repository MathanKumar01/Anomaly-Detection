class EventStateManager:

    def __init__(self, end_threshold=20):

        self.active_events = {}
        self.completed_events = []
        self.end_threshold = end_threshold

    # ======================================================
    # Update
    # ======================================================

    def update(self, frame_number, events):

        output_events = []

        current_tracks = set()

        # ---------------------------------------------
        # Process Current Events
        # ---------------------------------------------

        for event in events:

            track_id = event["track_id"]
            event_name = event["event"]

            # Ignore Scene Events
            if track_id == "SCENE":
                continue

            current_tracks.add(track_id)

            # ---------------------------------------------
            # NORMAL -> END EVENT
            # ---------------------------------------------

            if event_name == "NORMAL":

                if track_id in self.active_events:

                    active = self.active_events[track_id]

                    output_events.append({

                        "track_id": track_id,

                        "event": active["event"],

                        "state": "ENDED",

                        "frame": frame_number

                    })

                    self.completed_events.append({

                        "track_id": track_id,

                        "event": active["event"],

                        "start": active["start_frame"],

                        "end": frame_number,

                        "duration": frame_number - active["start_frame"]

                    })

                    del self.active_events[track_id]

                continue

            # ---------------------------------------------
            # NEW EVENT
            # ---------------------------------------------

            if track_id not in self.active_events:

                self.active_events[track_id] = {

                    "event": event_name,

                    "start_frame": frame_number,

                    "last_seen": frame_number,

                    "duration": 0

                }

                output_events.append({

                    "track_id": track_id,

                    "event": event_name,

                    "state": "STARTED",

                    "frame": frame_number

                })

                continue

            active = self.active_events[track_id]

            # ---------------------------------------------
            # SAME EVENT
            # ---------------------------------------------

            if active["event"] == event_name:

                active["last_seen"] = frame_number

                active["duration"] = (

                    frame_number - active["start_frame"]

                )

                output_events.append({

                    "track_id": track_id,

                    "event": event_name,

                    "state": "ACTIVE",

                    "frame": frame_number

                })

            # ---------------------------------------------
            # EVENT CHANGED
            # ---------------------------------------------

            else:

                output_events.append({

                    "track_id": track_id,

                    "event": active["event"],

                    "state": "ENDED",

                    "frame": frame_number

                })

                self.completed_events.append({

                    "track_id": track_id,

                    "event": active["event"],

                    "start": active["start_frame"],

                    "end": frame_number,

                    "duration": frame_number - active["start_frame"]

                })

                self.active_events[track_id] = {

                    "event": event_name,

                    "start_frame": frame_number,

                    "last_seen": frame_number,

                    "duration": 0

                }

                output_events.append({

                    "track_id": track_id,

                    "event": event_name,

                    "state": "STARTED",

                    "frame": frame_number

                })

        # ---------------------------------------------
        # Remove Lost Tracks
        # ---------------------------------------------

        remove_tracks = []

        for track_id, active in self.active_events.items():

            if track_id in current_tracks:
                continue

            if frame_number - active["last_seen"] >= self.end_threshold:

                output_events.append({

                    "track_id": track_id,

                    "event": active["event"],

                    "state": "ENDED",

                    "frame": frame_number

                })

                self.completed_events.append({

                    "track_id": track_id,

                    "event": active["event"],

                    "start": active["start_frame"],

                    "end": frame_number,

                    "duration": frame_number - active["start_frame"]

                })

                remove_tracks.append(track_id)

        for track_id in remove_tracks:

            del self.active_events[track_id]

        return output_events

    # ======================================================
    # Active Events
    # ======================================================

    def print_active_events(self):

        print("\n========== ACTIVE EVENTS ==========")

        if len(self.active_events) == 0:

            print("No Active Events")

            return

        for track_id, event in self.active_events.items():

            print("--------------------------------")

            print(f"Track ID : {track_id}")

            print(f"Event    : {event['event']}")

            print(f"Started  : {event['start_frame']}")

            print(f"Duration : {event['duration']} Frames")

    # ======================================================
    # Completed Events
    # ======================================================

    def print_completed_events(self):

        print("\n========== COMPLETED EVENTS ==========")

        if len(self.completed_events) == 0:

            print("No Completed Events")

            return

        for event in self.completed_events:

            print("--------------------------------")

            print(f"Track ID : {event['track_id']}")

            print(f"Event    : {event['event']}")

            print(f"Start    : {event['start']}")

            print(f"End      : {event['end']}")

            print(f"Duration : {event['duration']} Frames")