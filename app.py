import os
import math

# Fix OpenMP conflict if running multiple torch/cv2 instances on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2

from config import (
    VIDEO_PATH,
    YOLO_MODEL,
    POSE_MODEL,
    CONFIDENCE,
    ENABLE_POSE,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)

from utils.video_loader import VideoLoader
from detector.object_detector import ObjectDetector
from detector.pose_detector import PoseDetector

from anomaly.feature_extractor import FeatureExtractor
from anomaly.behavior_analyzer import BehaviorAnalyzer
from anomaly.trajectory_analyzer import TrajectoryAnalyzer
from anomaly.interaction_analyzer import InteractionAnalyzer
from anomaly.motion_analyzer import MotionAnalyzer
from anomaly.decision_engine import DecisionEngine
from anomaly.risk_smoother import RiskSmoother
from anomaly.crowd_analyzer import CrowdAnalyzer
from anomaly.scene_memory import SceneMemory
from anomaly.pose_analyzer import PoseAnalyzer
from anomaly.pose_memory import PoseMemory
from anomaly.fall_detector import FallDetector
from anomaly.event_reasoner import EventReasoner
from anomaly.threat_prioritizer import ThreatPrioritizer
from anomaly.incident_timeline import IncidentTimeline
from anomaly.event_state_manager import EventStateManager
from alerts.telegram_alert import TelegramAlert


def main():
    # ==========================================
    # Initialize Modules
    # ==========================================
    print(f"[INFO] Loading video: {VIDEO_PATH}")
    video = VideoLoader(VIDEO_PATH)

    print(f"[INFO] Loading YOLO detector: {YOLO_MODEL}")
    detector = ObjectDetector(YOLO_MODEL)

    pose_detector = None
    pose_analyzer = None
    pose_memory = None
    fall_detector = None

    if ENABLE_POSE:
        print(f"[INFO] Loading YOLO Pose model: {POSE_MODEL}")
        pose_detector = PoseDetector(POSE_MODEL)
        pose_analyzer = PoseAnalyzer()
        pose_memory = PoseMemory()
        fall_detector = FallDetector()

    extractor = FeatureExtractor()
    behavior_analyzer = BehaviorAnalyzer()
    trajectory_analyzer = TrajectoryAnalyzer(max_points=30)
    interaction_analyzer = InteractionAnalyzer()
    motion_analyzer = MotionAnalyzer()
    decision_engine = DecisionEngine()
    risk_smoother = RiskSmoother(window_size=20)
    crowd_analyzer = CrowdAnalyzer()
    scene_memory = SceneMemory(max_history=300)
    event_reasoner = EventReasoner()
    threat_prioritizer = ThreatPrioritizer()
    timeline = IncidentTimeline()
    event_state_manager = EventStateManager(end_threshold=20)
    telegram_alert = TelegramAlert.from_config(
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
    )

    # ==========================================
    # Display Window
    # ==========================================
    window_name = "AI Surveillance & Anomaly Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, DISPLAY_WIDTH, DISPLAY_HEIGHT)

    frame_number = 0

    # ==========================================
    # Main Processing Loop
    # ==========================================
    while True:
        ret, frame = video.read()
        if not ret:
            print("[INFO] Video stream ended or no frame received.")
            break

        frame_number += 1

        # -----------------------------
        # Object Detection & Tracking
        # -----------------------------
        results = detector.detect(frame)
        annotated_frame = results[0].plot(line_width=1, font_size=10)

        # -----------------------------
        # Feature Extraction
        # -----------------------------
        features = extractor.extract(results, detector.model)

        # -----------------------------
        # Behavior Analysis
        # -----------------------------
        behaviors = behavior_analyzer.analyze(features)
        active_track_ids = [p["track_id"] for p in behaviors if p["track_id"] >= 0]

        # -----------------------------
        # Pose & Fall Detection (Optional)
        # -----------------------------
        fall_results = []
        person_poses = {}

        if ENABLE_POSE and len(behaviors) > 0:
            pose_results = pose_detector.detect(frame)
            raw_poses = pose_analyzer.analyze(pose_results)

            # Match raw pose to tracked person by spatial proximity
            for person in behaviors:
                track_id = person["track_id"]
                if track_id < 0:
                    continue

                best_pose = "UNKNOWN"
                min_dist = float("inf")

                for p_pose in raw_poses:
                    dist = math.hypot(
                        person["x"] - p_pose["center_x"],
                        person["y"] - p_pose["center_y"]
                    )
                    if dist < min_dist and dist < 120:  # Max 120px threshold
                        min_dist = dist
                        best_pose = p_pose["pose"]

                # Smooth pose with memory
                stable_info = pose_memory.update(track_id, best_pose)
                stable_pose = stable_info["stable_pose"]
                person_poses[track_id] = stable_pose

                # Check fall condition
                fall_info = fall_detector.update(track_id, stable_pose)
                fall_results.append(fall_info)

            # Prune departed tracks
            fall_detector.prune_stale_tracks(active_track_ids)
            pose_memory.prune_stale_tracks(active_track_ids)

        # -----------------------------
        # Trajectory Analysis
        # -----------------------------
        trajectories = trajectory_analyzer.update(behaviors)

        # -----------------------------
        # Interaction Analysis
        # -----------------------------
        interactions = interaction_analyzer.analyze(behaviors)

        # -----------------------------
        # Motion Analysis
        # -----------------------------
        motion_results = motion_analyzer.analyze(behaviors)

        # -----------------------------
        # Crowd Analysis
        # -----------------------------
        crowd = crowd_analyzer.analyze(behaviors)

        # -----------------------------
        # Decision Engine & Risk Smoothing
        # -----------------------------
        raw_decisions = decision_engine.evaluate(
            behaviors,
            trajectories,
            interactions,
            motion_results,
            crowd
        )
        decisions = risk_smoother.smooth(raw_decisions)

        # -----------------------------
        # Scene Memory
        # -----------------------------
        scene_state = scene_memory.update(
            behaviors,
            trajectories,
            interactions,
            motion_results,
            crowd,
            decisions,
            frame_number
        )

        # -----------------------------
        # Event Reasoning & State Tracking
        # -----------------------------
        events = event_reasoner.analyze(scene_state, crowd, fall_results=fall_results)
        state_events = event_state_manager.update(frame_number, events)
        highest_threat = threat_prioritizer.analyze(events)

        if telegram_alert:
            for state_event in state_events:
                if state_event["state"] != "STARTED":
                    continue

                event_name = state_event["event"]
                matching_event = next(
                    event for event in events
                    if event["track_id"] == state_event["track_id"]
                    and event["event"] == event_name
                )
                try:
                    sent = telegram_alert.send(
                        event_name,
                        state_event["track_id"],
                        matching_event["confidence"],
                        frame_number,
                    )
                    if not sent:
                        print("[INFO] Telegram alert skipped: one-message limit reached.")
                except Exception as error:
                    print(f"[ERROR] Could not send Telegram alert: {error}")

        timeline_data = timeline.update(
            frame_number,
            behaviors,
            decisions,
            events,
            highest_threat
        )

        # -----------------------------
        # Visual Annotations
        # -----------------------------
        # Draw Trajectories
        for traj in trajectories:
            points = traj["trajectory"]
            for i in range(1, len(points)):
                p1 = (int(points[i - 1][0]), int(points[i - 1][1]))
                p2 = (int(points[i][0]), int(points[i][1]))
                cv2.line(annotated_frame, p1, p2, (255, 120, 0), 2)

        # Draw Pose Labels above tracked individuals
        if ENABLE_POSE:
            for person in behaviors:
                tid = person["track_id"]
                if tid in person_poses and person_poses[tid] != "UNKNOWN":
                    pose_str = person_poses[tid]
                    p_color = (0, 0, 255) if pose_str == "LYING" else (0, 255, 0)
                    cv2.putText(
                        annotated_frame,
                        f"Pose: {pose_str}",
                        (int(person["x"] - 30), int(person["y"] - 35)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45,
                        p_color,
                        1
                    )

        # HUD Overlay Banner. Size it from the actual text so long scene/event
        # names stay inside the panel instead of being clipped.
        risk_color = (0, 255, 0) if crowd["scene_risk"] == "NORMAL" else (0, 0, 255)
        hud_lines = [
            (f"People Count: {crowd['people_count']}", (255, 255, 255)),
            (f"Crowd Density: {crowd['crowd_density']}", (255, 255, 0)),
            (f"Scene Risk: {crowd['scene_risk']}", risk_color),
        ]

        if highest_threat and highest_threat["event"] != "NORMAL":
            threat_color = (0, 0, 255) if highest_threat["priority"] <= 3 else (0, 165, 255)
            hud_lines.append((f"Alert: {highest_threat['event']}", threat_color))
            hud_lines.append((f"Track ID: {highest_threat['track_id']}", threat_color))
        else:
            hud_lines.append(("Status: MONITORING (NORMAL)", (0, 255, 0)))

        hud_font = 0.45
        hud_thickness = 1
        hud_padding = 6
        max_text_width = max(
            cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, hud_font, hud_thickness)[0][0]
            for text, _ in hud_lines
        )
        frame_height, frame_width = annotated_frame.shape[:2]
        hud_width = min(max_text_width + hud_padding * 2, frame_width - 20)
        hud_height = 8 + len(hud_lines) * 20

        hud_overlay = annotated_frame.copy()
        cv2.rectangle(hud_overlay, (10, 10), (hud_width, hud_height), (30, 30, 30), -1)
        cv2.addWeighted(hud_overlay, 0.88, annotated_frame, 0.12, 0, annotated_frame)
        cv2.rectangle(annotated_frame, (10, 10), (hud_width, hud_height), (100, 100, 100), 1)

        for line_index, (text, color) in enumerate(hud_lines):
            cv2.putText(
                annotated_frame,
                text,
                (20, 25 + line_index * 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                hud_font,
                color,
                hud_thickness,
            )

        # -----------------------------
        # Console Diagnostics (Every 30 Frames)
        # -----------------------------
        if frame_number % 30 == 0:
            print("\n===================================")
            print(f"Frame : {frame_number}")

            if len(behaviors) == 0:
                print("No Person Detected")
            else:
                print("\n========== CROWD ANALYSIS ==========")
                print(f"People Count : {crowd['people_count']}")
                print(f"Close Pairs  : {crowd['close_pairs']}")
                print(f"Crowd Density: {crowd['crowd_density']}")
                print(f"Scene Risk   : {crowd['scene_risk']}")

                print("\n========== PERSON ANALYSIS ==========")
                for person in behaviors:
                    tid = person["track_id"]
                    print(f"--- Person ID : {tid} ---")
                    print(f"Position : ({person['x']}, {person['y']}) | Speed : {person['speed']} | Dir : {person['direction']}")

                    for decision in decisions:
                        if decision["track_id"] == tid:
                            print(f"Risk Score : {decision['score']} | Status : {decision['status']}")

                    if ENABLE_POSE and tid in person_poses:
                        print(f"Stable Pose : {person_poses[tid]}")

                if interactions:
                    print("\n========== INTERACTIONS ==========")
                    for interaction in interactions:
                        print(f"Person {interaction['person1']} <-> Person {interaction['person2']} | Dist : {interaction['distance']} | Status : {interaction['status']}")

                if highest_threat:
                    print("\n========== HIGHEST THREAT ==========")
                    print(f"Track ID   : {highest_threat['track_id']}")
                    print(f"Event      : {highest_threat['event']}")
                    print(f"Priority   : {highest_threat['priority']}")
                    print(f"Confidence : {highest_threat['confidence']}")

                event_state_manager.print_active_events()
                event_state_manager.print_completed_events()

        # -----------------------------
        # Display Video
        # -----------------------------
        display = cv2.resize(annotated_frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        cv2.imshow(window_name, display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Quit key 'q' pressed by user.")
            break

    video.release()
    cv2.destroyAllWindows()
    print("[INFO] Surveillance pipeline terminated cleanly.")


if __name__ == "__main__":
    main()