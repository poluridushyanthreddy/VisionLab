from werkzeug.utils import secure_filename
import uuid,os,shutil
def upload(file,folder):

    filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(folder,filename)
    file.save(filepath)
    return filepath,filename

def delete(filename1,folder):
    filepath=os.path.join(folder,filename1)
    if os.path.exists(filepath):
        os.remove(filepath)

def deletefolder(directory,foldername):
    filepath=os.path.join(directory,'pointclouds',foldername)
    if os.path.isdir(filepath):
        shutil.rmtree(filepath)
    
    