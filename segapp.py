from flask import Flask, render_template, request, redirect, url_for,flash
import os,secrets
from services.model_registry import MODELS
from utils import file_upload
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import InputRequired,Length,ValidationError,Email,EqualTo
from flask_wtf import CSRFProtect,FlaskForm
from flask_login import UserMixin,LoginManager,login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

segapp = Flask(__name__)
segapp.config['SQLALCHEMY_DATABASE_URI']='sqlite:///test.db'#database of type sqlite
segapp.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
db=SQLAlchemy(segapp)
csrf = CSRFProtect(segapp)

login_manager = LoginManager()
login_manager.init_app(segapp)
login_manager.login_view = "login"  # redirects here if @login_required blocks an anon user
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Upload folder
segapp.config['UPLOAD_FOLDER'] = os.path.join(segapp.root_path,'static')
upload_folder=segapp.config['UPLOAD_FOLDER']

segapp.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
MAX_FILE_SIZE = 10 * 1024 * 1024

def file_too_big(file_storage):
    """Check a single uploaded file's size without loading it fully into memory."""
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0) 
    return size > MAX_FILE_SIZE

#Supported image formats
extensions={'.avif','.jpeg','.webp','.png', '.jpg', '.bmp', '.jpeg2000', '.dng', '.tiff', '.heif', '.mpo', '.jp2', '.tif', '.heic'}
st_folders=['images','images/predictions','images/original','images/depth','pointclouds']
# Create folders if not present
for i in st_folders:
    folder = os.path.join(upload_folder,i)
    os.makedirs(folder, exist_ok=True)

class IVPlatform(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    model_cat= db.Column(db.String(50), nullable=False)
    model_name= db.Column(db.String(50), nullable=False)
    original=db.Column(db.String(200),nullable=False)
    depth=db.Column(db.String(200),nullable=True)
    output=db.Column(db.String(200),nullable=False)
    folder=db.Column(db.String(200),nullable=True)
    inf_time= db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return '<Entry %r>' % self.id

class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20),unique=True,nullable=False)
    email=db.Column(db.String(100),unique=True,nullable=False)
    password_hash=db.Column(db.String(255),nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow,nullable=False)
    last_login=db.Column(db.DateTime)
    predictions=db.relationship("IVPlatform",backref="user",lazy=True)

class SignUpForm(FlaskForm):
    username = StringField("Username",validators=[InputRequired(), Length(min=6, max=20)])
    email = StringField("Email",validators=[InputRequired(), Email()])

    password = PasswordField("Password",validators=[InputRequired(), Length(min=8)])

    confirm_password = PasswordField(
    "Confirm Password",
    validators=[InputRequired(), EqualTo("password", message="Passwords must match.")]
)

    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username already exists.")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered.")

class LoginForm(FlaskForm):
    identifier = StringField("Username or Email",validators=[InputRequired()])
    password = PasswordField("Password",validators=[InputRequired()])

    submit = SubmitField("Login")
    

# Home page
@segapp.route("/")
def index():
    return render_template("index.html")

@segapp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
 
    form = SignUpForm()
 
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
        )
        db.session.add(user)
        db.session.commit()
 
        flash("Account created. Please log in.")
        return redirect(url_for("login"))
 
    return render_template("signup.html", form=form)

@segapp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
 
    form = LoginForm()
 
    if form.validate_on_submit():
        identifier = form.identifier.data
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
 
        if user and check_password_hash(user.password_hash, form.password.data):
            user.last_login = datetime.utcnow()
            db.session.commit()
 
            login_user(user)
            return redirect(url_for("index"))
 
        flash("Invalid username/email or password.")
 
    return render_template("login.html", form=form)

@segapp.route('/Segmentation')
def segmentation():
    return render_template('task.html',title="Segmentation",
    models={"YOLO": "Yolo",
    "DeepLabV3": "DeeplabV3"})

@segapp.route('/pointcloud')
@login_required
def pointcloud():
    return render_template('pointcloud.html',title="PointCloud",
    models={"PointCloud": "Yolo",})

@segapp.route('/detection')
def detection():
    return render_template('task.html',title="Detection",
    models={"Yolo-Detection": "Yolo"})

# Display page
@segapp.route('/display/<original>/<path:output>/<time_taken>')
def display(original, output,time_taken):
    task = IVPlatform.query.filter_by(original=original, output=output).first()
 
    if task is not None:
        if not current_user.is_authenticated or current_user.id != task.user_id:
            return "Not found", 404
 
    return render_template('display.html', original=original, output=output, time_taken=time_taken)
# Upload route
@segapp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        model = request.form.get("model")
        if model not in MODELS:
            flash("Invalid model selected.")
            return redirect(request.referrer or url_for('segmentation'))
 
        file = request.files['image']
        if file.filename == '':
            flash("No file selected.")
            return redirect(request.referrer or url_for('segmentation'))
 
        extension = os.path.splitext(file.filename)[1]
        if extension not in extensions:
            flash("Unsupported file format.")
            return redirect(request.referrer or url_for('segmentation'))
 
        if file_too_big(file):
            flash("File too large. Max size is 10 MB.")
            return redirect(request.referrer or url_for('segmentation'))
 
        filepath, filename = file_upload.upload(file, os.path.join(upload_folder, 'images', 'original'))
        output_filename, time_taken = MODELS[model]["function"](filepath, os.path.join(upload_folder, 'images'))
 
        # Only persist to DB if the user is logged in
        if current_user.is_authenticated:
            task = IVPlatform(
                user_id=current_user.id,
                model_cat=MODELS[model]["task"],
                model_name=model,
                original=filename,
                output=output_filename,
                inf_time=time_taken,
            )
            db.session.add(task)
            db.session.commit()
 
        return redirect(url_for('display', original=filename, output=output_filename, time_taken=time_taken))

@segapp.route('/cloudupload', methods=['GET', 'POST'])
def cloud():
    if request.method == 'POST':
        model = request.form.get("model")
        if model not in MODELS:
            flash("Invalid model selected.")
            return redirect(request.referrer or url_for('pointcloud'))
 
        file1 = request.files['image']
        file2 = request.files['depth_image']
        if file1.filename == '' or file2.filename == '':
            flash("Please select both an image and a depth image.")
            return redirect(request.referrer or url_for('pointcloud'))
 
        extension1 = os.path.splitext(file1.filename)[1]
        extension2 = os.path.splitext(file2.filename)[1]
        for ext in [extension1, extension2]:
            if ext not in extensions:
                flash("Unsupported file format.")
                return redirect(request.referrer or url_for('pointcloud'))
 
        if file_too_big(file1) or file_too_big(file2):
            flash("File too large. Max size is 10 MB per file.")
            return redirect(request.referrer or url_for('pointcloud'))
 
        filepath2, filename2 = file_upload.upload(file2, os.path.join(upload_folder, 'images', 'depth'))
        filepath1, filename1 = file_upload.upload(file1, os.path.join(upload_folder, 'images', 'original'))
        output_filename, time_taken, folder = MODELS[model]["function"](
            filepath1, filepath2, os.path.join(upload_folder, 'images')
        )
 
        if current_user.is_authenticated:
            task = IVPlatform(
                user_id=current_user.id,
                model_cat=MODELS[model]["task"],
                model_name=model,
                depth=filename2,
                original=filename1,
                output=output_filename,
                inf_time=time_taken,
                folder=folder,
            )
            db.session.add(task)
            db.session.commit()
 
        return redirect(url_for('display', original=filename1, output=output_filename, time_taken=time_taken))
    

@segapp.route('/delete/<int:id>')
@login_required
def delete(id):
    res_delete=IVPlatform.query.filter_by(id=id,user_id=current_user.id).first_or_404()
    if res_delete.depth:
        file_upload.delete(res_delete.depth,os.path.join(upload_folder,'images','depth'))
        file_upload.deletefolder(upload_folder,res_delete.folder)

    file_upload.delete(res_delete.original,os.path.join(upload_folder,'images','original'))
    file_upload.delete(res_delete.output,os.path.join(upload_folder,'images','predictions'))

    db.session.delete(res_delete)
    db.session.commit()
    return redirect('/results')

@segapp.route('/deleteptcloud/<int:id>/<path:filename>')
@login_required
def deleteptcloud(id, filename):
    task = IVPlatform.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    folder = os.path.join(upload_folder, 'pointclouds', task.folder)
    target = os.path.abspath(os.path.join(folder, filename))

    if not target.startswith(os.path.abspath(folder) + os.sep):
        return "Invalid file path", 400

    if os.path.exists(target):
        os.remove(target)

    return redirect(f'/objectviewer/{id}')

@segapp.route('/results')
@login_required
def result():
    category=request.args.get("category")
    if category:
        allresults=IVPlatform.query.filter_by(user_id=current_user.id,model_cat=category).order_by(IVPlatform.date_created.desc()).all()
    else:
        allresults=IVPlatform.query.filter_by(user_id=current_user.id).order_by(IVPlatform.date_created.desc()).all()
    return render_template('results.html',allresults=allresults)

@segapp.route('/objectviewer/<int:id>')
@login_required
def viewer(id):
    task=IVPlatform.query.filter_by(user_id=current_user.id,id=id).first_or_404()
    folder=os.path.join(upload_folder,'pointclouds',task.folder)
    pointclouds = []

    for file in sorted(os.listdir(folder)):
        if file.endswith(".ply"):
            pointclouds.append({
                "name": file,
                "url": f"/static/pointclouds/{task.folder}/{file}"    })
    return render_template('object-viewer.html',files=pointclouds,id=id)

@segapp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@segapp.errorhandler(413)
def file_too_large(e):
    flash("File too large.")
    return redirect(request.referrer or url_for('index')), 413

if __name__ == "__main__":    
    segapp.run(debug=True)