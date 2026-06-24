from werkzeug.utils import secure_filename
import uuid,os
def upload(file,folder):

    filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(folder,filename)
    file.save(filepath)
    return filepath,filename

def delete(filename1,filename2,folder):
    filepath=os.path.join(folder,filename1)
    os.remove(filepath)
    filepath=os.path.join(folder,'predictions',filename2)
    os.remove(filepath)