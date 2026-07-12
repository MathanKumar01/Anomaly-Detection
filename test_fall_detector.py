from anomaly.fall_detector import FallDetector

fall = FallDetector()

poses = [

    "STANDING",

    "STANDING",

    "STANDING",

    "FALLING",

    "LYING",

    "LYING",

    "LYING",

    "LYING"

]

for pose in poses:

    result = fall.update(

        track_id=1,

        stable_pose=pose

    )

    print(result)