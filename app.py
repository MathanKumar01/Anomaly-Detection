import os

# Fix OpenMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2

from config import VIDEO_PATH, YOLO_MODEL

from utils.video_loader import VideoLoader
from detector.object_detector import ObjectDetector

from anomaly.feature_extractor import FeatureExtractor
from anomaly.behavior_analyzer import BehaviorAnalyzer
from anomaly.trajectory_analyzer import TrajectoryAnalyzer
from anomaly.interaction_analyzer import InteractionAnalyzer
from anomaly.motion_analyzer import MotionAnalyzer
from anomaly.decision_engine import DecisionEngine
from anomaly.crowd_analyzer import CrowdAnalyzer
from anomaly.scene_memory import SceneMemory
from anomaly.event_reasoner import EventReasoner
from anomaly.threat_prioritizer import ThreatPrioritizer
from anomaly.incident_timeline import IncidentTimeline

from anomaly.risk_smoother import RiskSmoother
from anomaly.event_state_manager import EventStateManager
# ==========================================
# Initialize Modules
# ==========================================

video = VideoLoader(r"C:\projects\anamoly_detection\dataset\Assault011_x264.mp4")

detector = ObjectDetector(YOLO_MODEL)

extractor = FeatureExtractor()

behavior_analyzer = BehaviorAnalyzer()

trajectory_analyzer = TrajectoryAnalyzer()

interaction_analyzer = InteractionAnalyzer()

motion_analyzer = MotionAnalyzer()

decision_engine = DecisionEngine()

crowd_analyzer = CrowdAnalyzer()


scene_memory = SceneMemory(max_history=300)

event_reasoner = EventReasoner()

threat_prioritizer = ThreatPrioritizer()

timeline = IncidentTimeline()

risk_smoother = RiskSmoother(window_size=20)
event_state_manager = EventStateManager(end_threshold=20)
# ==========================================
# Window
# ==========================================

cv2.namedWindow("AI Surveillance", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AI Surveillance", 1280, 720)

frame_number = 0

# ==========================================
# Main Loop
# ==========================================

while True:

    ret, frame = video.read()

    if not ret:
        break

    frame_number += 1

    # -----------------------------
    # Object Detection
    # -----------------------------

    results = detector.detect(frame)

    # Draw YOLO detections
    annotated_frame = results[0].plot()

    # -----------------------------
    # Feature Extraction
    # -----------------------------

    features = extractor.extract(results, detector.model)

    # -----------------------------
    # Behavior Analysis
    # -----------------------------

    behaviors = behavior_analyzer.analyze(features)

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
    # Decision Engine
    # -----------------------------

    decisions = decision_engine.evaluate(
        behaviors,
        trajectories,
        interactions,
        motion_results,
        crowd
        )

    decisions = risk_smoother.smooth(decisions)

    scene_state = scene_memory.update(
    behaviors,
    trajectories,
    interactions,
    motion_results,
    crowd,
    decisions,
    frame_number
)
    
    events = event_reasoner.analyze(
    scene_state,
    crowd
)
    state_events = event_state_manager.update(
    frame_number,
    events
)
    
    highest_threat = threat_prioritizer.analyze(events)

    timeline_data = timeline.update(
    frame_number,
    behaviors,
    decisions,
    events,
    highest_threat
)
    # -----------------------------
    # Draw Trajectory
    # -----------------------------

    for traj in trajectories:

        points = traj["trajectory"]

        for i in range(1, len(points)):

            p1 = (int(points[i - 1][0]), int(points[i - 1][1]))
            p2 = (int(points[i][0]), int(points[i][1]))

            cv2.line(
                annotated_frame,
                p1,
                p2,
                (255, 0, 0),
                2
            )

    # -----------------------------
    # Print Every 30 Frames
    # -----------------------------

       # -----------------------------
    # Print Every 30 Frames
    # -----------------------------

    if frame_number % 30 == 0:

        print("\n===================================")
        print(f"Frame : {frame_number}")

        if len(behaviors) == 0:

            print("No Person Detected")

        else:

            # -----------------------------
            # Crowd Analysis
            # -----------------------------

            print("\n========== CROWD ANALYSIS ==========")
            print(f"People Count : {crowd['people_count']}")
            print(f"Close Pairs  : {crowd['close_pairs']}")
            print(f"Crowd Density: {crowd['crowd_density']}")
            print(f"Scene Risk   : {crowd['scene_risk']}")

            # -----------------------------
            # Person Analysis
            # -----------------------------

            for person in behaviors:

                print("--------------------------------")

                print(f"Person ID : {person['track_id']}")
                print(f"Position : ({person['x']}, {person['y']})")
                print(f"Speed : {person['speed']}")
                print(f"Direction : {person['direction']}")
                print(f"Time : {person['time']} Frames")

                for traj in trajectories:

                    if traj["track_id"] == person["track_id"]:

                        print(f"Trajectory Points : {traj['trajectory_length']}")

                for motion in motion_results:

                    if motion["track_id"] == person["track_id"]:

                        print(f"Acceleration : {motion['acceleration']}")
                        print(f"Direction Changed : {motion['direction_changed']}")
                        print(f"Motion Score : {motion['motion_score']}")

                for decision in decisions:

                    if decision["track_id"] == person["track_id"]:

                        print(f"Risk Score : {decision['score']}")
                        print(f"Decision   : {decision['status']}")

            # -----------------------------
            # Interaction Analysis
            # -----------------------------

            print("\n========== INTERACTIONS ==========")

            if len(interactions) == 0:

                print("No Interaction")

            else:

                for interaction in interactions:

                    print(
                        f"Person {interaction['person1']} <-> "
                        f"Person {interaction['person2']} | "
                        f"Distance : {interaction['distance']} | "
                        f"Status : {interaction['status']}"
                    )

            # -----------------------------
            # Scene Memory
            # -----------------------------

            print("\n========== SCENE MEMORY ==========")

            if len(scene_state) == 0:

                print("Scene Memory Empty")

            else:

                for memory in scene_state:

                    print("--------------------------------")

                    print(f"Person ID         : {memory['track_id']}")
                    print(f"History Length    : {memory['history_length']}")
                    print(f"Current Position  : {memory['current_position']}")
                    print(f"Current Speed     : {memory['current_speed']}")
                    print(f"Average Speed     : {memory['average_speed']}")
                    print(f"Current Motion    : {memory['current_motion']}")
                    print(f"Maximum Motion    : {memory['max_motion']}")
                    print(f"Risk Score        : {memory['risk_score']}")
                    print(f"Current Risk      : {memory['current_risk']}")
                    print(f"Interaction Count : {memory['interaction_count']}")
                    print(f"Trajectory Length : {memory['trajectory_length']}")

                         # -----------------------------
            # Event Reasoner
            # -----------------------------

            print("\n========== EVENT REASONER ==========")

            if len(events) == 0:

                print("No Events")

            else:

                for event in events:

                    print("--------------------------------")

                    print(f"Track ID   : {event['track_id']}")
                    print(f"Event      : {event['event']}")
                    print(f"Confidence : {event['confidence']}")

            print("\n========== THREAT PRIORITIZER ==========")

            if highest_threat is None:

                print("No Threat")

            else:

                print(f"Track ID   : {highest_threat['track_id']}")
                print(f"Event      : {highest_threat['event']}")
                print(f"Priority   : {highest_threat['priority']}")
                print(f"Confidence : {highest_threat['confidence']}")

            timeline.print_timeline()

            event_state_manager.print_active_events()

            event_state_manager.print_completed_events()
    # -----------------------------
    # Display
    # -----------------------------

    cv2.putText(
        annotated_frame,
        f"People : {crowd['people_count']}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Density : {crowd['crowd_density']}",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Scene : {crowd['scene_risk']}",
        (20, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2
    )

    display = cv2.resize(
        annotated_frame,
        (1280, 720)
    )

    cv2.imshow(
        "AI Surveillance",
        display
    )

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()