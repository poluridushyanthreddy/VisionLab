from flask import Flask, render_template, request, redirect, url_for
import os
from services.model_registry import MODELS
from utils import file_upload
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

segapp = Flask(__name__)
segapp.config['SQLALCHEMY_DATABASE_URI']='sqlite:///test.db'#database of type sqlite
db=SQLAlchemy(segapp)
# Upload folder
segapp.config['UPLOAD_FOLDER'] = os.path.join(segapp.root_path,'static','images')

#Supported image formats
extensions={'.avif','.jpeg','.webp','.png', '.jpg', '.bmp', '.jpeg2000', '.dng', '.tiff', '.heif', '.mpo', '.jp2', '.tif', '.heic'}

# Create folders if not present
os.makedirs(segapp.config['UPLOAD_FOLDER'], exist_ok=True)
prediction_folder = os.path.join(segapp.config['UPLOAD_FOLDER'],'predictions')
os.makedirs(prediction_folder, exist_ok=True)

class IVPlatform(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    model_cat= db.Column(db.String(50), nullable=False)
    model_name= db.Column(db.String(50), nullable=False)
    original=db.Column(db.String(200),nullable=False)
    segmented=db.Column(db.String(200),nullable=False)
    inf_time= db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return '<Entry %r>' % self.id

# Home page
@segapp.route('/')
def index():
    return render_template('index.html')

@segapp.route('/detection')
def detection():
    return render_template('detection.html')

# Display page
@segapp.route('/display/<original>/<path:segmented>/<time_taken>')
def display(original, segmented,time_taken):

    return render_template('display.html',original=original,segmented=segmented,time_taken=time_taken)

# Upload route
@segapp.route('/upload', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':
        model=request.form.get("model")
        if model not in MODELS: return "Invalid Model"
        file = request.files['image']
        if file.filename == '':
           return "No file selected"
        extension=os.path.splitext(file.filename)[1]

        if extension not in extensions:return "Unsupported File Format"
        filepath,filename=file_upload.upload(file,segapp.config['UPLOAD_FOLDER'])
        segmented_filename,time_taken=MODELS[model]["function"](filepath,segapp.config['UPLOAD_FOLDER'])

        task=IVPlatform(model_cat=MODELS[model]["task"],
                        model_name=model,
                        original=filename,
                        segmented=segmented_filename,
                        inf_time=time_taken)
        db.session.add(task)
        db.session.commit()

        return redirect(url_for('display',original=filename,segmented=f'predictions/{segmented_filename}',time_taken=time_taken))

@segapp.route('/delete/<int:id>')
def delete(id):
    res_delete=IVPlatform.query.filter_by(id=id).first_or_404()
    file_upload.delete(res_delete.original,res_delete.segmented,segapp.config['UPLOAD_FOLDER'])
    db.session.delete(res_delete)
    db.session.commit()
    return redirect('/results')

@segapp.route('/results')
def result():
    allresults=IVPlatform.query.order_by(IVPlatform.date_created.desc()).all()#learn't this in sqlbolt tutorial
    return render_template('results.html',allresults=allresults)

if __name__ == "__main__":
    segapp.run(debug=True)