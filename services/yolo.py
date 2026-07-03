from ultralytics import YOLO
import os,time,cv2
import open3d as o3d,numpy as np
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



def pointcloud(rgb_path,depth_path,folder):
    rgb = cv2.imread(rgb_path)
    depth = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)

    if rgb is None or depth is None:
        raise Exception("Error loading images")

    if len(depth.shape) == 3:
        depth = depth[:, :, 0]

    h, w = depth.shape

    start = time.perf_counter()

    results = model(rgb_path,save=True,project=folder,name='predictions',exist_ok=True)


    inference_time = (time.perf_counter() - start) * 1000

    if results[0].masks is None:
        raise Exception("No objects detected")

    input_name = os.path.basename(results[0].path)
    name_without_ext = os.path.splitext(input_name)[0]
    save_folder = os.path.join("static", "pointclouds", name_without_ext)
    os.makedirs(save_folder, exist_ok=True)

    fx, fy = 525, 525
    cx, cy = w / 2, h / 2

    masks = results[0].masks.data.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy().astype(int)
    names = results[0].names
    for idx, mask in enumerate(masks):

        mask = mask > 0.5
        mask = cv2.resize(mask.astype(np.uint8), (w, h))

        points = []
        colors = []

        for v in range(h):
            for u in range(w):

                if not mask[v, u]:
                    continue

                z = depth[v, u] / 1000.0

                if z <= 0:
                    continue

                x = (u - cx) * z / fx
                y = (v - cy) * z / fy

                points.append([x, y, z])
                colors.append(rgb[v, u] / 255.0)

        if len(points) == 0:
            continue

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(points))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors))

        pcd, _ = pcd.remove_statistical_outlier(
            nb_neighbors=20,
            std_ratio=2.0
        )
        class_name=names[classes[idx]]
        o3d.io.write_point_cloud(
            os.path.join(save_folder, f"{idx}_{class_name}.ply"),
            pcd
        )

    return f'{name_without_ext}.jpg', inference_time, name_without_ext