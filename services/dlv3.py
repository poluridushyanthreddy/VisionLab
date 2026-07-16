import os
import time
import cv2
import torch
import numpy as np
from PIL import Image
from torchvision import models, transforms

model = models.segmentation.deeplabv3_resnet101(weights="DEFAULT")
model.eval()

VOC_CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair",
    "cow", "diningtable", "dog", "horse", "motorbike",
    "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"
]

COLORS = {
    1: (255, 0, 0),
    2: (0, 255, 0),
    3: (0, 0, 255),
    4: (255, 255, 0),
    5: (255, 0, 255),
    6: (0, 255, 255),
    7: (128, 0, 255),
    8: (255, 128, 0),
    9: (0, 128, 255),
    10: (128, 255, 0),
    11: (255, 0, 128),
    12: (0, 255, 128),
    13: (128, 128, 255),
    14: (255, 128, 128),
    15: (128, 255, 128),
    16: (200, 100, 0),
    17: (100, 200, 0),
    18: (0, 100, 200),
    19: (200, 0, 100),
    20: (100, 0, 200)
}

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def segment(imagepath, folder):
    image = Image.open(imagepath).convert("RGB")
    image_np = np.array(image)

    input_tensor = transform(image).unsqueeze(0)

    start = time.time()

    with torch.no_grad():
        output = model(input_tensor)["out"][0]

    end = time.time()

    prediction = output.argmax(0).cpu().numpy()

    overlay = image_np.copy()

    alpha = 0.5

    detected_classes = np.unique(prediction)
    detected_classes = detected_classes[detected_classes != 0]

    for cls in detected_classes:

        mask = prediction == cls

        color = np.array(COLORS.get(cls, (0, 255, 0)))

        overlay[mask] = (
            alpha * color +
            (1 - alpha) * overlay[mask]
        ).astype(np.uint8)

        ys, xs = np.where(mask)

        if len(xs) == 0:
            continue

        x1, x2 = xs.min(), xs.max()
        y1, y2 = ys.min(), ys.max()

        cv2.rectangle(
            overlay,
            (x1, y1),
            (x2, y2),
            tuple(int(c) for c in color),
            2
        )

        cv2.rectangle(
            overlay,
            (x1, max(0, y1 - 25)),
            (x1 + 140, y1),
            tuple(int(c) for c in color),
            -1
        )

        cv2.putText(
            overlay,
            VOC_CLASSES[cls],
            (x1 + 5, y1 - 7),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

    save_dir = os.path.join(folder, "predictions")
    os.makedirs(save_dir, exist_ok=True)

    input_name = os.path.basename(imagepath)
    name_without_ext = os.path.splitext(input_name)[0]

    output_filename = f"{name_without_ext}.jpg"
    output_path = os.path.join(save_dir, output_filename)

    cv2.imwrite(
        output_path,
        cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    )

    inference_time = (end - start) * 1000

    return output_filename, f"{inference_time:.2f} ms"