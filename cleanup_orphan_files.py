"""
Cleans up files/folders left behind by anonymous users who never signed up
to save their result. Anything NOT referenced in IVPlatform, and older than
GRACE_PERIOD_HOURS, gets removed.

The age check matters: a fresh anon upload has no DB row yet either (that's
the whole point), so without a grace period this would delete files while
someone's still actively looking at their result.

Run via cron:
    0 * * * *  cd /home/dushyant/VisionLab && /home/dushyant/VisionLab/venv/bin/python cleanup_orphans.py
"""

import os
import shutil
import time

GRACE_PERIOD_HOURS = 6
GRACE_PERIOD_SECONDS = GRACE_PERIOD_HOURS * 3600


def _is_old_enough(path):
    return (time.time() - os.path.getmtime(path)) > GRACE_PERIOD_SECONDS


def cleanup_orphans():
    from segapp import segapp, db, IVPlatform, upload_folder

    with segapp.app_context():
        referenced_originals = set()
        referenced_outputs = set()
        referenced_depths = set()
        referenced_folders = set()

        for row in IVPlatform.query.all():
            if row.original:
                referenced_originals.add(row.original)
            if row.output:
                referenced_outputs.add(row.output)
            if row.depth:
                referenced_depths.add(row.depth)
            if row.folder:
                referenced_folders.add(row.folder)

        removed = {"original": 0, "predictions": 0, "depth": 0, "pointclouds": 0}

        flat_dirs = [
            (os.path.join(upload_folder, 'images', 'original'), referenced_originals, "original"),
            (os.path.join(upload_folder, 'images', 'predictions'), referenced_outputs, "predictions"),
            (os.path.join(upload_folder, 'images', 'depth'), referenced_depths, "depth"),
        ]

        for folder_path, referenced_set, label in flat_dirs:
            if not os.path.isdir(folder_path):
                continue
            for filename in os.listdir(folder_path):
                full_path = os.path.join(folder_path, filename)
                if not os.path.isfile(full_path):
                    continue
                if filename in referenced_set:
                    continue
                if not _is_old_enough(full_path):
                    continue
                os.remove(full_path)
                removed[label] += 1

        pc_root = os.path.join(upload_folder, 'pointclouds')
        if os.path.isdir(pc_root):
            for foldername in os.listdir(pc_root):
                full_path = os.path.join(pc_root, foldername)
                if not os.path.isdir(full_path):
                    continue
                if foldername in referenced_folders:
                    continue
                if not _is_old_enough(full_path):
                    continue
                shutil.rmtree(full_path)
                removed["pointclouds"] += 1

        return removed


if __name__ == "__main__":
    result = cleanup_orphans()
    print(f"Cleanup complete: {result}")