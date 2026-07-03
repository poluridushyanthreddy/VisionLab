from services import yolo,dlv3

MODELS = {
    "YOLO": {
        "task": "Segmentation",
        "function": yolo.segment
    },

    "DeepLabV3": {
        "task": "Segmentation",
        "function": dlv3.segment
    },

    "Yolo-Detection": {
        "task": "Detection",
        "function": yolo.detect
    },
    "PointCloud": {
        "task": "PointCloud",
        "function": yolo.pointcloud
    }
}