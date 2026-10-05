import math
import os
import tempfile

# Fix the Windows OpenMP conflict before importing cv2, torch, or Ultralytics.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import cv2
import streamlit as st

from anomaly.behavior_analyzer import BehaviorAnalyzer
from anomaly.crowd_analyzer import CrowdAnalyzer
from anomaly.decision_engine import DecisionEngine
from anomaly.event_reasoner import EventReasoner
from anomaly.event_state_manager import EventStateManager
from anomaly.fall_detector import FallDetector
from anomaly.feature_extractor import FeatureExtractor
from anomaly.interaction_analyzer import InteractionAnalyzer
from anomaly.motion_analyzer import MotionAnalyzer
from anomaly.pose_analyzer import PoseAnalyzer
from anomaly.pose_memory import PoseMemory
from anomaly.risk_smoother import RiskSmoother
from anomaly.scene_memory import SceneMemory
from anomaly.threat_prioritizer import ThreatPrioritizer
from anomaly.trajectory_analyzer import TrajectoryAnalyzer
from alerts.telegram_alert import TelegramAlert
from config import (
    POSE_MODEL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from detector.object_detector import ObjectDetector
from detector.pose_detector import PoseDetector


st.set_page_config(page_title="Anomaly Detection", page_icon="&#128065;", layout="wide")


def create_pipeline(model_path, enable_pose, enable_telegram):
    return {
        "detector": ObjectDetector(model_path),
        "pose_detector": PoseDetector(POSE_MODEL) if enable_pose else None,
        "pose_analyzer": PoseAnalyzer() if enable_pose else None,
        "pose_memory": PoseMemory() if enable_pose else None,
        "fall_detector": FallDetector() if enable_pose else None,
        "extractor": FeatureExtractor(),
        "behavior": BehaviorAnalyzer(),
        "trajectory": TrajectoryAnalyzer(max_points=30),
        "interaction": InteractionAnalyzer(),
        "motion": MotionAnalyzer(),
        "decision": DecisionEngine(),
        "risk": RiskSmoother(window_size=20),
        "crowd": CrowdAnalyzer(),
        "scene": SceneMemory(max_history=300),
        "reasoner": EventReasoner(),
        "prioritizer": ThreatPrioritizer(),
        "states": EventStateManager(end_threshold=20),
        "telegram": TelegramAlert.from_config(
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHAT_ID,
        ) if enable_telegram else None,
    }


def process_frame(frame, pipeline, frame_number, enable_pose):
    detector = pipeline["detector"]
    results = detector.detect(frame)
    annotated = frame.copy()
    for box in results[0].boxes:
        x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
        class_id = int(box.cls[0])
        color = (40, 220, 80) if detector.model.names[class_id] == "person" else (170, 170, 170)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 1)
    features = pipeline["extractor"].extract(results, detector.model)
    behaviors = pipeline["behavior"].analyze(features)
    active_ids = [person["track_id"] for person in behaviors if person["track_id"] >= 0]

    fall_results = []
    poses = {}
    if enable_pose and behaviors:
        raw_poses = pipeline["pose_analyzer"].analyze(pipeline["pose_detector"].detect(frame))
        for person in behaviors:
            track_id = person["track_id"]
            if track_id < 0:
                continue
            best_pose = "UNKNOWN"
            nearest = float("inf")
            for raw_pose in raw_poses:
                distance = math.hypot(
                    person["x"] - raw_pose["center_x"],
                    person["y"] - raw_pose["center_y"],
                )
                if distance < nearest and distance < 120:
                    nearest = distance
                    best_pose = raw_pose["pose"]
            stable = pipeline["pose_memory"].update(track_id, best_pose)
            poses[track_id] = stable["stable_pose"]
            fall_results.append(pipeline["fall_detector"].update(track_id, poses[track_id]))
        pipeline["fall_detector"].prune_stale_tracks(active_ids)
        pipeline["pose_memory"].prune_stale_tracks(active_ids)

    trajectories = pipeline["trajectory"].update(behaviors)
    interactions = pipeline["interaction"].analyze(behaviors)
    motion = pipeline["motion"].analyze(behaviors)
    crowd = pipeline["crowd"].analyze(behaviors)
    decisions = pipeline["risk"].smooth(
        pipeline["decision"].evaluate(behaviors, trajectories, interactions, motion, crowd)
    )
    scene = pipeline["scene"].update(
        behaviors, trajectories, interactions, motion, crowd, decisions, frame_number
    )
    events = pipeline["reasoner"].analyze(scene, crowd, fall_results=fall_results)
    state_events = pipeline["states"].update(frame_number, events)
    highest_threat = pipeline["prioritizer"].analyze(events)

    for state_event in state_events:
        if state_event["state"] != "STARTED" or pipeline["telegram"] is None:
            continue
        matching = next(
            (event for event in events
             if event["track_id"] == state_event["track_id"]
             and event["event"] == state_event["event"]),
            None,
        )
        if matching:
            pipeline["telegram"].send(
                matching["event"],
                matching["track_id"],
                matching["confidence"],
                frame_number,
            )

    return cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), crowd, highest_threat, state_events


def main():
    st.markdown("# Anomaly Detection Monitor")
    st.caption("Upload a surveillance video to run detection, anomaly reasoning, and alerts.")

    with st.sidebar:
        st.header("Controls")
        model_path = st.text_input("Model path", value="yolo11n.pt")
        st.caption("Confidence is configured in config.py for the desktop pipeline.")
        enable_pose = st.checkbox("Enable pose and fall detection", value=True)
        enable_telegram = st.checkbox("Enable Telegram alerts", value=False)
        frame_step = st.slider("Process every Nth frame", 1, 30, 5)
        uploaded_video = st.file_uploader("Surveillance video", type=["mp4", "avi", "mov", "mkv"])

    if not uploaded_video:
        st.info("Choose a video from the sidebar to start monitoring.")
        return
    if not os.path.exists(model_path):
        st.error(f"Model not found: {model_path}")
        return

    if st.button("Start analysis", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as video_file:
            video_file.write(uploaded_video.getbuffer())
            video_path = video_file.name

        pipeline = create_pipeline(model_path, enable_pose, enable_telegram)
        capture = cv2.VideoCapture(video_path)
        frame_slot = st.empty()
        progress = st.progress(0)
        status = st.empty()
        alert_slot = st.empty()
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        frame_number = 0
        processed_frames = 0
        max_people = 0
        latest_threat = None
        telegram_sent = False

        while True:
            success, frame = capture.read()
            if not success:
                break
            frame_number += 1
            if frame_number % frame_step != 0:
                continue
            annotated, crowd, threat, state_events = process_frame(
                frame, pipeline, frame_number, enable_pose
            )
            frame_slot.image(annotated, channels="RGB", use_column_width=True)
            processed_frames += 1
            max_people = max(max_people, crowd["people_count"])
            latest_threat = threat or latest_threat
            if any(event["state"] == "STARTED" for event in state_events):
                telegram_sent = telegram_sent or pipeline["telegram"] is not None
            if threat and threat["event"] != "NORMAL":
                alert_slot.warning(
                    f"Anomaly: {threat['event']} | Track: {threat['track_id']} | "
                    f"Confidence: {threat['confidence']:.0%}"
                )
            progress.progress(min(frame_number / total_frames, 1.0))
            status.write(f"Processed frame {frame_number:,} of {total_frames:,}")

        capture.release()
        os.unlink(video_path)
        st.success("Analysis complete")
        one, two, three = st.columns(3)
        one.metric("Frames analyzed", f"{processed_frames:,}")
        two.metric("Peak people detected", max_people)
        three.metric("Latest event", latest_threat["event"] if latest_threat else "NORMAL")
        if pipeline["telegram"] is None:
            st.info(
                "Telegram disabled: configure TELEGRAM_BOT_TOKEN and "
                "TELEGRAM_CHAT_ID before starting Streamlit."
            )
        elif telegram_sent:
            st.success("Anomaly alert processing was triggered. Check Telegram.")


if __name__ == "__main__":
    main()
