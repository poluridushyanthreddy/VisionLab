from ultralytics import YOLO
import os,time
model = YOLO("yolov8n-seg.pt")

def segment(imagepath,folder):
    start=time.time()
    results = model(imagepath,save=True,project=folder,name='predictions',exist_ok=True)
    end=time.time()
    # Build actual saved prediction filename
    input_name = os.path.basename(results[0].path)
    name_without_ext = os.path.splitext(input_name)[0]

    inf_time=(end-start)*1000
    return f"{name_without_ext}.jpg",f"{inf_time:.2f} ms"