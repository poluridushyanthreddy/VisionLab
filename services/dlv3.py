import os,time
import cv2
import torch
import numpy as np
from PIL import Image
from torchvision import models, transforms

model = models.segmentation.deeplabv3_resnet101(weights="DEFAULT")
model.eval()

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def segment(imagepath, folder):
    image = Image.open(imagepath).convert("RGB")
    input_tensor = transform(image).unsqueeze(0)

    start=time.time()

    with torch.no_grad():
        output = model(input_tensor)["out"][0]
    
    end=time.time()

    prediction = output.argmax(0).cpu().numpy()
    mask = prediction != 0

    image_np = np.array(image)
    segmented = image_np.copy()
    segmented[~mask] = 0

    save_dir = os.path.join(folder, "predictions")
    os.makedirs(save_dir, exist_ok=True)

    input_name = os.path.basename(imagepath)
    name_without_ext = os.path.splitext(input_name)[0]

    output_filename = f"{name_without_ext}.jpg"
    output_path = os.path.join(save_dir, output_filename)

    cv2.imwrite(output_path,cv2.cvtColor(segmented, cv2.COLOR_RGB2BGR))
    inf_time=(end-start)*1000

    return output_filename,f"{inf_time:.2f} ms"