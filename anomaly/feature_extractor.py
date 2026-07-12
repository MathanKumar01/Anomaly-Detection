class FeatureExtractor:

    def __init__(self):
        pass

    def extract(self, results, model):

        features = []

        boxes = results[0].boxes

        if boxes is None:
            return features

        # Check if tracking IDs exist
        ids = None
        if boxes.id is not None:
            ids = boxes.id.int().cpu().tolist()

        for i, box in enumerate(boxes):

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            width = x2 - x1
            height = y2 - y1

            # Get tracking ID
            track_id = ids[i] if ids else -1

            features.append({

                "track_id": track_id,

                "object": model.names[cls],

                "confidence": round(conf, 2),

                "center_x": round(center_x, 2),

                "center_y": round(center_y, 2),

                "width": round(width, 2),

                "height": round(height, 2)

            })

        return features