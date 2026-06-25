from ultralytics import YOLO
import os,time
model = YOLO("yolov8n-seg.pt")
model_det=YOLO("yolov8n.pt")

def segment(imagepath,folder):
    start=time.perf_counter()
    results = model(imagepath,save=True,project=folder,name='predictions',exist_ok=True)
    end=time.perf_counter()
    # Build actual saved prediction filename
    input_name = os.path.basename(results[0].path)
    name_without_ext = os.path.splitext(input_name)[0]

    inf_time=(end-start)*1000
    return f"{name_without_ext}.jpg",f"{inf_time:.2f} ms"

def detect(imagepath,folder):
    start=time.perf_counter()
    results = model_det(imagepath,save=True,project=folder,name='predictions',exist_ok=True)
    end=time.perf_counter()

    input_name = os.path.basename(results[0].path)
    name_without_ext = os.path.splitext(input_name)[0]

    inf_time=(end-start)*1000
    return f"{name_without_ext}.jpg",f"{inf_time:.2f} ms"