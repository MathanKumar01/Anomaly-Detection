"""
Decision Engine (Redesigned)
=============================

DESIGN PRINCIPLE
-----------------
Person-level risk must depend ONLY on that person's own behavior:
    - Speed
    - Motion intensity
    - Acceleration (aggressive movement)
    - Rapid direction changes
    - Close interaction, but ONLY when combined with aggressive movement

Scene-level signals (Crowd Density, Scene Risk, Number of People) are
DELIBERATELY EXCLUDED from this engine. They do not get added to any
individual's score. They belong in the Event Reasoner / SceneEventAnalyzer,
where they should be combined with the *aggregated* per-person risk output
(e.g. "how many CRITICAL people are there right now?") to detect
scene-level events like Crowd Panic, Fight, Riot, or Accident.

This keeps the two concerns cleanly separated:
    Decision Engine   -> "Is THIS person behaving dangerously?"
    Event Reasoner     -> "Is something dangerous happening in the SCENE?"

All thresholds below are constants at the top of the file so you can
calibrate them against real footage without touching the logic.
"""


class DecisionEngine:

    # =========================================================
    # TUNABLE THRESHOLDS
    # (Adjust these against real data - the logic itself
    #  should not need to change.)
    # =========================================================

    # --- Motion score (violent / erratic motion) : max 25 pts ---
    MOTION_HIGH = 10
    MOTION_MED = 6
    MOTION_LOW = 3
    MOTION_HIGH_PTS = 25
    MOTION_MED_PTS = 15
    MOTION_LOW_PTS = 8

    # --- Speed : max 20 pts ---
    SPEED_HIGH = 8      # running fast / fleeing
    SPEED_MED = 5       # running
    SPEED_LOW = 3       # jogging / brisk walk
    SPEED_WALK = 1      # normal walking (barely counts)
    SPEED_HIGH_PTS = 20
    SPEED_MED_PTS = 15
    SPEED_LOW_PTS = 10
    SPEED_WALK_PTS = 2

    # --- Acceleration / aggressive movement : max 20 pts ---
    ACCEL_HIGH = 5
    ACCEL_MED = 3
    ACCEL_LOW = 1
    ACCEL_HIGH_PTS = 20
    ACCEL_MED_PTS = 12
    ACCEL_LOW_PTS = 5

    # --- Rapid direction changes : max 15 pts ---
    # Expects trajectory-level data such as "direction_changes"
    # (number of sharp heading reversals in a recent window).
    DIR_CHANGE_HIGH = 5
    DIR_CHANGE_MED = 3
    DIR_CHANGE_LOW = 1
    DIR_CHANGE_HIGH_PTS = 15
    DIR_CHANGE_MED_PTS = 8
    DIR_CHANGE_LOW_PTS = 3

    # --- Close interaction, ONLY when combined with aggression : max 20 pts ---
    # A person standing close to someone else while calm contributes 0.
    # Close interaction only matters once the person is already
    # behaving aggressively (fast, accelerating, or high motion score).
    AGGRESSION_SPEED_GATE = 3
    AGGRESSION_ACCEL_GATE = 3
    AGGRESSION_MOTION_GATE = 6

    CLOSE_HIGH_PTS = 20   # 3+ close interactions while aggressive
    CLOSE_MED_PTS = 12    # 2 close interactions while aggressive
    CLOSE_LOW_PTS = 6     # 1 close interaction while aggressive

    # --- Final status thresholds (max possible score = 100) ---
    CRITICAL_THRESHOLD = 70
    HIGH_RISK_THRESHOLD = 45
    SUSPICIOUS_THRESHOLD = 20

    def __init__(self):
        pass

    # =========================================================
    # PUBLIC API
    # =========================================================

    def evaluate(self, behaviors, trajectories, interactions, motion_results, crowd):
        """
        Returns a list of PERSON-LEVEL risk decisions.

        NOTE: `crowd` is intentionally accepted but NOT used here.
        It is scene-level context and should be passed directly to the
        Event Reasoner / SceneEventAnalyzer, not blended into individual
        scores. It's kept as a parameter only so callers don't need to
        change the pipeline signature; feel free to drop it once the
        Event Reasoner takes crowd data directly.
        """

        decisions = []

        for person in behaviors:
            track_id = person["track_id"]

            speed, acceleration, motion_score = self._get_motion_features(track_id, motion_results)
            trajectory_length, direction_changes = self._get_trajectory_features(track_id, trajectories)
            close_count = self._get_close_interaction_count(track_id, interactions)

            score, breakdown = self._score_person(
                speed, acceleration, motion_score, direction_changes, close_count
            )

            status = self._classify(score)

            decisions.append({
                "track_id": track_id,
                "score": score,
                "status": status,
                "speed": round(speed, 2),
                "acceleration": round(acceleration, 2),
                "motion_score": round(motion_score, 2),
                "direction_changes": direction_changes,
                "close_interactions": close_count,
                "trajectory": trajectory_length,   # kept for display only, NOT scored
                "breakdown": breakdown,             # useful for debugging/tuning
            })

        return decisions

    # =========================================================
    # FEATURE EXTRACTION
    # =========================================================

    def _get_motion_features(self, track_id, motion_results):
        for motion in motion_results:
            if motion["track_id"] == track_id:
                speed = motion.get("speed", 0)
                acceleration = abs(motion.get("acceleration", 0))
                motion_score = motion.get("motion_score", 0)
                return speed, acceleration, motion_score
        return 0, 0, 0

    def _get_trajectory_features(self, track_id, trajectories):
        for traj in trajectories:
            if traj["track_id"] == track_id:
                trajectory_length = traj.get("trajectory_length", 0)
                # direction_changes is optional - depends on whether your
                # Trajectory Analyzer emits it yet. Defaults to 0 if absent.
                direction_changes = traj.get("direction_changes", 0)
                return trajectory_length, direction_changes
        return 0, 0

    def _get_close_interaction_count(self, track_id, interactions):
        close_count = 0
        for interaction in interactions:
            if interaction["status"] != "Close":
                continue
            if interaction["person1"] == track_id or interaction["person2"] == track_id:
                close_count += 1
        return close_count

    # =========================================================
    # SCORING
    # =========================================================

    def _score_person(self, speed, acceleration, motion_score, direction_changes, close_count):
        breakdown = {}

        # --- Motion score ---
        if motion_score >= self.MOTION_HIGH:
            pts = self.MOTION_HIGH_PTS
        elif motion_score >= self.MOTION_MED:
            pts = self.MOTION_MED_PTS
        elif motion_score >= self.MOTION_LOW:
            pts = self.MOTION_LOW_PTS
        else:
            pts = 0
        breakdown["motion"] = pts

        # --- Speed ---
        if speed >= self.SPEED_HIGH:
            pts = self.SPEED_HIGH_PTS
        elif speed >= self.SPEED_MED:
            pts = self.SPEED_MED_PTS
        elif speed >= self.SPEED_LOW:
            pts = self.SPEED_LOW_PTS
        elif speed >= self.SPEED_WALK:
            pts = self.SPEED_WALK_PTS
        else:
            pts = 0
        breakdown["speed"] = pts

        # --- Acceleration ---
        if acceleration >= self.ACCEL_HIGH:
            pts = self.ACCEL_HIGH_PTS
        elif acceleration >= self.ACCEL_MED:
            pts = self.ACCEL_MED_PTS
        elif acceleration >= self.ACCEL_LOW:
            pts = self.ACCEL_LOW_PTS
        else:
            pts = 0
        breakdown["acceleration"] = pts

        # --- Rapid direction changes ---
        if direction_changes >= self.DIR_CHANGE_HIGH:
            pts = self.DIR_CHANGE_HIGH_PTS
        elif direction_changes >= self.DIR_CHANGE_MED:
            pts = self.DIR_CHANGE_MED_PTS
        elif direction_changes >= self.DIR_CHANGE_LOW:
            pts = self.DIR_CHANGE_LOW_PTS
        else:
            pts = 0
        breakdown["direction_changes"] = pts

        # --- Close interaction, gated behind aggression ---
        is_aggressive = (
            speed >= self.AGGRESSION_SPEED_GATE
            or acceleration >= self.AGGRESSION_ACCEL_GATE
            or motion_score >= self.AGGRESSION_MOTION_GATE
        )

        if is_aggressive and close_count >= 3:
            pts = self.CLOSE_HIGH_PTS
        elif is_aggressive and close_count == 2:
            pts = self.CLOSE_MED_PTS
        elif is_aggressive and close_count == 1:
            pts = self.CLOSE_LOW_PTS
        else:
            pts = 0  # calm + close = not risky by itself
        breakdown["close_interaction"] = pts

        total = sum(breakdown.values())
        return total, breakdown

    def _classify(self, score):
        if score >= self.CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif score >= self.HIGH_RISK_THRESHOLD:
            return "HIGH RISK"
        elif score >= self.SUSPICIOUS_THRESHOLD:
            return "SUSPICIOUS"
        else:
            return "NORMAL"


class SceneEventAnalyzer:
    """
    Scene-level reasoning, separated out of the Decision Engine.

    This is where Crowd Density, Scene Risk, and Number of People belong.
    It consumes the PERSON-LEVEL decisions (from DecisionEngine) plus the
    raw scene context, and reasons about scene-level events.

    This is a starting skeleton - wire it into your Event Reasoner stage
    and expand the rules to match your actual event taxonomy
    (Crowd Panic, Fight, Riot, Accident, etc).
    """

    # Fraction of the ACTIVE crowd that must be moving fast before we'll
    # call it a panic. "A few busy stalls" is not "everyone is fleeing."
    PANIC_SPEED_THRESHOLD = 3.0
    PANIC_FRACTION_REQUIRED = 0.4   # 40%+ of currently-tracked people

    def __init__(self):
        pass

    def analyze(self, person_decisions, crowd, active_track_ids=None):
        """
        active_track_ids: track_ids that were ACTUALLY detected in the
        current frame (i.e. present in `behaviors` this frame). This is
        how we avoid counting stale Scene Memory entries as live risk.
        If not provided, all person_decisions are treated as active
        (backwards-compatible, but you should pass this in).
        """

        # --- Drop anyone not confirmed in THIS frame ---
        if active_track_ids is not None:
            confirmed = [d for d in person_decisions if d["track_id"] in active_track_ids]
            stale = [d for d in person_decisions if d["track_id"] not in active_track_ids]
        else:
            confirmed = person_decisions
            stale = []

        high_risk_count = sum(1 for d in confirmed if d["status"] in ("HIGH RISK", "CRITICAL"))
        critical_count = sum(1 for d in confirmed if d["status"] == "CRITICAL")

        events = []

        # Multiple aggressive people, confirmed live this frame
        # -> possible Fight / Riot.
        if critical_count >= 2 and crowd.get("crowd_density") == "HIGH":
            events.append("RIOT_SUSPECTED")
        elif critical_count >= 1 and high_risk_count >= 2:
            events.append("FIGHT_SUSPECTED")

        # Crowd Panic: requires ACTUAL evidence that a large share of the
        # confirmed crowd is moving fast right now - not just that the
        # scene is crowded or previously flagged risky. A dense but mostly
        # stationary crowd (people standing around) must NOT trigger this.
        if confirmed:
            fast_movers = sum(1 for d in confirmed if d["speed"] >= self.PANIC_SPEED_THRESHOLD)
            fast_fraction = fast_movers / len(confirmed)
        else:
            fast_fraction = 0.0

        if (
            crowd.get("crowd_density") == "HIGH"
            and fast_fraction >= self.PANIC_FRACTION_REQUIRED
        ):
            events.append("CROWD_PANIC_SUSPECTED")

        return {
            "events": events,
            "high_risk_count": high_risk_count,
            "critical_count": critical_count,
            "confirmed_count": len(confirmed),
            "stale_ignored_count": len(stale),
            "stale_ignored_ids": [d["track_id"] for d in stale],
            "fast_mover_fraction": round(fast_fraction, 2),
            "crowd_density": crowd.get("crowd_density"),
            "scene_risk": crowd.get("scene_risk"),
        }