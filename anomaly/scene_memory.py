from collections import deque


class SceneMemory:

    def __init__(self,
                 max_history=300,
                 max_missing=60):

        # Frames to remember
        self.max_history = max_history

        # Frames allowed to disappear
        self.max_missing = max_missing

        # Memory for every tracked person
        self.memory = {}

        # Missing frame counter
        self.missing_frames = {}

    # ==========================================================
    # Update Scene Memory
    # ==========================================================

    def update(
    self,
    behaviors,
    trajectories,
    interactions,
    motion_results,
    crowd,
    decisions,
    frame_number
):

        # ---------------------------------------
        # Fast Lookup Dictionaries
        # ---------------------------------------

        trajectory_map = {
            t["track_id"]: t
            for t in trajectories
        }

        motion_map = {
            m["track_id"]: m
            for m in motion_results
        }

        decision_map = {
            d["track_id"]: d
            for d in decisions
        }

        interaction_map = {}

        for interaction in interactions:

            p1 = interaction["person1"]
            p2 = interaction["person2"]

            interaction_map.setdefault(p1, []).append(interaction)
            interaction_map.setdefault(p2, []).append(interaction)

        active_tracks = set()

        # ---------------------------------------
        # Update Every Person
        # ---------------------------------------

        for person in behaviors:
            # Ignore invalid IDs
            

            track_id = person["track_id"]
            
            if track_id is None or track_id < 0:
                continue
            active_tracks.add(track_id)

            # ---------------------------------------
            # Create Memory
            # ---------------------------------------

            if track_id not in self.memory:

                self.memory[track_id] = {

                    "positions":
                        deque(maxlen=self.max_history),

                    "speed":
                        deque(maxlen=self.max_history),

                    "acceleration":
                        deque(maxlen=self.max_history),

                    "direction":
                        deque(maxlen=self.max_history),

                    "direction_changed":
                        deque(maxlen=self.max_history),

                    "motion_score":
                        deque(maxlen=self.max_history),

                    "risk_score":
                        deque(maxlen=self.max_history),

                    "risk_status":
                        deque(maxlen=self.max_history),

                    "interaction_count":
                        deque(maxlen=self.max_history),

                    "trajectory_length":
                        deque(maxlen=self.max_history),

                    "direction_changes":
                        deque(maxlen=self.max_history),

                    "crowd_density":
                        deque(maxlen=self.max_history),

                    "scene_risk":
                        deque(maxlen=self.max_history),

                    "event_history":
                        deque(maxlen=self.max_history),

                    "timestamps":
                        deque(maxlen=self.max_history),

                    "first_seen": frame_number,

                    "last_seen": frame_number,

                }

                self.missing_frames[track_id] = 0

            # Person appeared again
            self.missing_frames[track_id] = 0
            person_memory = self.memory[track_id]
            person_memory["last_seen"] = frame_number
            

            motion = motion_map.get(track_id, {})

            decision = decision_map.get(track_id, {})

            trajectory = trajectory_map.get(track_id, {})

            # ---------------------------------------
            # Store Position
            # ---------------------------------------

            person_memory["positions"].append(
                (person["x"], person["y"])
            )

            # ---------------------------------------
            # Speed
            # ---------------------------------------

            speed = min(person["speed"], 15)

            person_memory["speed"].append(speed)

            # ---------------------------------------
            # Direction
            # ---------------------------------------

            person_memory["direction"].append(
                person["direction"]
            )

            # ---------------------------------------
            # Motion
            # ---------------------------------------

            motion_score = min(
            motion.get("motion_score", 0),
            50
            )

            person_memory["motion_score"].append(
            motion_score
)

            acceleration = max(
            min(motion.get("acceleration", 0), 10),
                -10
            )

            person_memory["acceleration"].append(acceleration)



            person_memory["direction_changed"].append(
                motion.get("direction_changed", False)
            )

            # ---------------------------------------
            # Decision
            # ---------------------------------------

            person_memory["risk_score"].append(
                decision.get("score", 0)
            )

            person_memory["risk_status"].append(
                decision.get("status", "NORMAL")
            )

            # ---------------------------------------
            # Crowd
            # ---------------------------------------

            person_memory["crowd_density"].append(
                crowd["crowd_density"]
            )

            person_memory["scene_risk"].append(
                crowd["scene_risk"]
            )

            # ---------------------------------------
            # Trajectory
            # ---------------------------------------

            person_memory["trajectory_length"].append(
                trajectory.get(
                    "trajectory_length",
                    0
                )
            )

            person_memory["direction_changes"].append(
                trajectory.get(
                    "direction_changes",
                    0
                )
            )

            # ---------------------------------------
            # Interactions
            # ---------------------------------------

            person_memory["interaction_count"].append(

                len(
                    interaction_map.get(
                        track_id,
                        []
                    )
                )
            )

            # ---------------------------------------
            # Placeholder Event
            # ---------------------------------------

            person_memory["event_history"].append(
                "UNKNOWN"
            )

            # ---------------------------------------
            # Timestamp
            # ---------------------------------------

            person_memory["timestamps"].append(
    frame_number
)

        # ---------------------------------------
        # Missing Tracks
        # ---------------------------------------

        for track_id in list(self.memory.keys()):

            if track_id not in active_tracks:

                self.missing_frames[track_id] += 1

                if self.missing_frames[track_id] > self.max_missing:

                    del self.memory[track_id]

                    del self.missing_frames[track_id]

        return self.get_scene_state()
        # ==========================================================
    # Scene State
    # ==========================================================

    def get_scene_state(self):

        scene = []

        for track_id, history in self.memory.items():
            if track_id < 0:
                continue

            speeds = list(history["speed"])
            motions = list(history["motion_score"])
            risks = list(history["risk_score"])
            accelerations = list(history["acceleration"])

            scene.append({

                "track_id": track_id,

                "history_length":
                    len(history["timestamps"]),

                "first_seen":
    history["first_seen"],

"last_seen":
    history["last_seen"],

"time_in_scene":
    history["last_seen"] -
    history["first_seen"],

                "current_position":
                    history["positions"][-1]
                    if history["positions"] else None,

                "current_speed":
                    round(speeds[-1], 2)
                    if speeds else 0,

                "average_speed":
                    round(
                        sum(speeds) / len(speeds),
                        2
                    ) if speeds else 0,

                "max_speed":
                    round(max(speeds), 2)
                    if speeds else 0,

                "current_acceleration":
                    round(accelerations[-1], 2)
                    if accelerations else 0,

                "average_acceleration":
                    round(
                        sum(accelerations) /
                        len(accelerations),
                        2
                    ) if accelerations else 0,

                "current_motion":
                    round(motions[-1], 2)
                    if motions else 0,

                "max_motion":
                    round(max(motions), 2)
                    if motions else 0,

                "risk_score":
                    risks[-1]
                    if risks else 0,

                "current_risk":
                    history["risk_status"][-1]
                    if history["risk_status"] else "NORMAL",

                "interaction_count":
                    history["interaction_count"][-1]
                    if history["interaction_count"] else 0,

                "trajectory_length":
                    history["trajectory_length"][-1]
                    if history["trajectory_length"] else 0,

                "direction":
                    history["direction"][-1]
                    if history["direction"] else "UNKNOWN",

                "current_direction_changes":
                    history["direction_changes"][-1]
                    if history["direction_changes"] else 0,

                "direction_changes":
                    history["direction_changes"][-1]
                    if history["direction_changes"] else 0,

                "crowd_density":
                    history["crowd_density"][-1]
                    if history["crowd_density"] else "LOW",

                "scene_risk":
                    history["scene_risk"][-1]
                    if history["scene_risk"] else "NORMAL",

                "last_event":
                    history["event_history"][-1]
                    if history["event_history"] else "UNKNOWN"

            })

        return scene

    # ==========================================================
    # Get One Person
    # ==========================================================

    def get_person(self, track_id):

        return self.memory.get(track_id, None)

    # ==========================================================
    # Get History
    # ==========================================================

    def get_history(self, track_id):

        if track_id not in self.memory:
            return None

        return self.memory[track_id]

    # ==========================================================
    # Get Entire Scene
    # ==========================================================

    def get_scene(self):

        return self.memory

    # ==========================================================
    # Scene Summary
    # ==========================================================

    def get_scene_summary(self):

        people = len(self.memory)

        high_risk = 0
        critical = 0

        avg_speed = []

        for history in self.memory.values():

            if history["risk_status"]:

                status = history["risk_status"][-1]

                if status == "HIGH RISK":
                    high_risk += 1

                elif status == "CRITICAL":
                    critical += 1

            if history["speed"]:

                avg_speed.append(history["speed"][-1])

        return {

            "people_count": people,

            "high_risk_people": high_risk,

            "critical_people": critical,

            "average_speed":
                round(
                    sum(avg_speed) / len(avg_speed),
                    2
                ) if avg_speed else 0
        }

    # ==========================================================
    # Update Event History
    # ==========================================================

    def update_event(self, track_id, event):

        if track_id not in self.memory:
            return

        self.memory[track_id]["event_history"].append(event)

    # ==========================================================
    # Clear Memory
    # ==========================================================

    def clear(self):

        self.memory.clear()
        self.missing_frames.clear()