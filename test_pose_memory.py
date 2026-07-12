from anomaly.pose_memory import PoseMemory

memory = PoseMemory()

poses = [

    "STANDING",
    "STANDING",
    "SITTING",
    "STANDING",
    "STANDING",
    "LYING",
    "LYING",
    "LYING",
    "LYING",
    "LYING"

]

for pose in poses:

    result = memory.update(
        track_id=1,
        pose=pose
    )

    print(result)