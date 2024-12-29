import json
from flask import (
    Flask,
    flash,
    render_template,
    request,
    redirect,
    send_from_directory,
    session,
    jsonify,
    Response,
)
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_bcrypt import Bcrypt
import subprocess
import os
import tempfile
import cv2
import asyncio
from flask import Flask, render_template, url_for
from flask_migrate import Migrate
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from flask import Flask, render_template, redirect, url_for
from sqlalchemy import desc
import base64


# Path to the shared file for detected objects
detected_objects_file = os.path.join(tempfile.gettempdir(), "detected_objects.json")

# from object.object import set_stop_signal
from object2.object2 import ObjectDetection

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///ums.sqlite"  # Adjust your database URI
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "65b0b774279de460f1cc5c92"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config["final_detected_images"] = "./final_detected_images"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
Session(app)

login_manager = LoginManager(app)
login_manager.login_view = 'userIndex'

process = None  # Global variable to manage the scanning subprocess
final_detected_objects = []  # Store the results of object detection

camera_obj = None

# User Class
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255), nullable=False)
    lname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    # edu = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)
    
    # removed scanned objects column
    # scanned_objects = db.Column(db.Text, nullable=True)  # New field

    def __repr__(self):
        return f'User("{self.id}", "{self.fname}", "{self.lname}", "{self.email}", "{self.edu}", "{self.username}", "{self.status}")'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Admin Class
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'Admin("{self.username}", "{self.id}")'

    
# Session Class
class BatchSession(db.Model):
    batch_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    bean_type = db.Column(db.String(255), nullable=False)
    farm = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key referencing user.id

    user = db.relationship('User', backref='batch_sessions', lazy=True)

    def __repr__(self):
        return f'BatchSession("{self.batch_id}", "{self.title}")'
    
# Defects Class
class DefectsDetected(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_number = db.Column(db.Integer, nullable=False)
    date_scanned = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    defectsDetected = db.Column(db.JSON, nullable=False)
    scanned_image = db.Column(db.String(255), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch_session.batch_id'), nullable=False)  # Foreign key

    # Define relationship to BatchSession
    batch = db.relationship('BatchSession', backref='defects_detected', lazy=True)


    def __repr__(self):
        return f'DefectsDetected("{self.id}", "{self.batch_id}")'
    


# with app.app_context():
#     # DefectsDetected.query.filter(id!=1).delete()
#     # db.session.commit()
    
#     dummy = open("dummy_count.txt", "r")

#     for line in dummy:
#         scan_number, defects_detected, batch_id, scanned_image = line.strip().split("-")
#         defects = DefectsDetected(scan_number=int(scan_number), defectsDetected=json.loads(defects_detected), batch_id=int(batch_id), scanned_image=scanned_image)
        
#         db.session.add(defects)

#     db.session.commit()


# =====truncate table=====
# def clear_table(model):
#     with app.app_context():
#         db.session.query(model).delete()
#         db.session.commit()
        
# clear_table(User)  # Replace with your model class
# clear_table(DefectsDetected)  # Replace with your model class
# clear_table(BatchSession)  # Replace with your model class
    
# =====truncate table end=====

        
# Main index
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/user/dashboard")
    return render_template("index.html", title="")


# Admin login
@app.route("/admin/", methods=["POST", "GET"])
def adminIndex():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "" and password == "":
            flash("Please fill all the fields", "danger")
            return redirect("/admin/")
        else:
            admins = Admin.query.filter_by(username=username).first()
            if admins and bcrypt.check_password_hash(admins.password, password):
                session["admin_id"] = admins.id
                session["admin_name"] = admins.username
                flash("Login Successfully", "success")
                return redirect("/admin/dashboard")
            else:
                flash("Invalid Username and Password", "danger")
                return redirect("/admin/")
    else:
        return render_template("admin/index.html", title="Admin Login")


# Admin Dashboard
@app.route("/admin/dashboard")
def adminDashboard():
    if not session.get("admin_id"):
        return redirect("/admin/")
    totalUser = User.query.count()
    totalApprove = User.query.filter_by(status=1).count()
    NotTotalApprove = User.query.filter_by(status=0).count()
    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard",
        totalUser=totalUser,
        totalApprove=totalApprove,
        NotTotalApprove=NotTotalApprove,
    )


# Admin get all users
@app.route("/admin/get-all-user", methods=["POST", "GET"])
def adminGetAllUser():
    if not session.get("admin_id"):
        return redirect("/admin/")
    if request.method == "POST":
        search = request.form.get("search")
        users = User.query.filter(User.username.like("%" + search + "%")).all()
        return render_template("admin/all-user.html", title="Approve User", users=users)
    else:
        users = User.query.all()
        return render_template("admin/all-user.html", title="Approve User", users=users)


@app.route("/admin/approve-user/<int:id>")
def adminApprove(id):
    if not session.get("admin_id"):
        return redirect("/admin/")
    User.query.filter_by(id=id).update(dict(status=1))
    db.session.commit()
    flash("Approve Successfully", "success")
    return redirect("/admin/get-all-user")


# Change admin password
@app.route("/admin/change-admin-password", methods=["POST", "GET"])
def adminChangePassword():
    admin = Admin.query.get(1)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "" or password == "":
            flash("Please fill the field", "danger")
            return redirect("/admin/change-admin-password")
        else:
            Admin.query.filter_by(username=username).update(
                dict(password=bcrypt.generate_password_hash(password, 10))
            )
            db.session.commit()
            flash("Admin Password updated successfully", "success")
            return redirect("/admin/change-admin-password")
    else:
        return render_template(
            "admin/admin-change-password.html",
            title="Admin Change Password",
            admin=admin,
        )


# Admin logout
@app.route("/admin/logout")
def adminLogout():
    if not session.get("admin_id"):
        return redirect("/admin/")
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    return redirect("/")


# ------------------------- User Area ----------------------------

# User login
@app.route("/user/", methods=["POST", "GET"])
def userIndex():
    if current_user.is_authenticated:
        return redirect("/user/dashboard")
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            if user.status == 0:
                flash("Your Account is not approved by Admin", "danger")
                return redirect("/user/")
            else:
                login_user(user)
                flash("Login Successfully", "success")
                return redirect("/user/dashboard")
        else:
            flash("Invalid Email and Password", "danger")
            return redirect("/user/")
    
    return render_template("user/index.html", title="User Login")


# User Register
@app.route("/user/signup", methods=["POST", "GET"])
def userSignup():
    if session.get("user_id"):
        return redirect("/user/dashboard")
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        if (
            fname == ""
            or lname == ""
            or email == ""
            or password == ""
            or username == ""
        ):
            flash("Please fill all the fields", "danger")
            return redirect("/user/signup")
        else:
            is_email = User.query.filter_by(email=email).first()
            if is_email:
                flash("Email already exists", "danger")
                return redirect("/user/signup")
            else:
                hash_password = bcrypt.generate_password_hash(password, 10)
                user = User(
                    fname=fname,
                    lname=lname,
                    email=email,
                    password=hash_password,
                    username=username,
                )
                db.session.add(user)
                db.session.commit()
                flash(
                    "Account Created Successfully! Admin will approve your account in 10 to 30 minutes",
                    "success",
                )
                return redirect("/user/")
    else:
        return render_template("user/signup.html", title="User Signup")


# Route to handle image scanning
@app.route("/scan", methods=["GET", "POST"])
@login_required
def scan_page():
    if request.method == "POST":
        session_name = request.form.get("input_session_name")
        farm = request.form.get("input_farm")
        bean_type = request.form.get("input_bean_type")
        user_Id = current_user.id
       
        newBatchSession = BatchSession(title=session_name, farm=farm, bean_type=bean_type, user_id=user_Id)
        db.session.add(newBatchSession)
        db.session.commit()
        
        AddednewBatchSession = BatchSession.query.order_by(BatchSession.batch_id.desc()).first()
        newId = AddednewBatchSession.batch_id
        newTitle = AddednewBatchSession.title
        
        return redirect(url_for("batch_scan_page", id=newId, title=newTitle))
   
    return render_template("user/scan.html")

@app.route("/scan/<int:id>/<string:title>", methods=["GET", "POST"])
@login_required
def batch_scan_page(id, title):
    batch_used = BatchSession.query.get(id)
    title_used = batch_used.title 
    farm_used = batch_used.farm
    bean_used = batch_used.bean_type
    last_scan = DefectsDetected.query.filter(DefectsDetected.batch_id == id).order_by(DefectsDetected.scan_number.desc()).first()
    
    if last_scan:
        last_scan_number = last_scan.scan_number
    else:
        last_scan_number = 0
    
    scan_number = last_scan_number + 1
    
    objects = {
        "title_used":title_used,
        "batch_used":batch_used,
        "farm_used":farm_used,
        "bean_used":bean_used,
        "last_scan":scan_number,
        }
    
    if request.method == "POST":
        # ======save frame
        final_annotated_image = camera_obj.get_last_frame()
        path = "./static/final_detected_images"
        if not os.path.exists(path):
            os.makedirs(path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_name = f"{current_user.id}_{timestamp}_image.jpg"  # Change extension to .png if needed

        # Full path to save the frame
        save_path = os.path.join(path, frame_name)
        # ======save frame
        
        # last_scan = BatchSession.query.order_by(BatchSession.scan_number.desc()).first()
        
        defects_detected = request.form.getlist("defect")
        defects_array = {}
        
        if "defects_count" in request.form:
            defects_count = request.form.getlist("defects_count")
            defects_count = list(map(int, defects_count))
            
            for index, defect in enumerate(defects_detected):
                # insert in dict
                defects_array[defect] = defects_count[index]
        
        if not len(defects_array) > 0:
            defects_array = {"none": "none"}
            
            
        newScan = DefectsDetected(
            scan_number=scan_number,
            defectsDetected=defects_array,
            scanned_image=frame_name,
            batch_id = id,
            
        )
        # save frame
        cv2.imwrite(save_path, final_annotated_image)
        db.session.add(newScan)
        db.session.commit()
        
        message="Data had been added"
        return render_template("user/scan2.html", message=message,objects=objects)
        
    return render_template("user/scan2.html", objects=objects)


# ---------------- Object Detection Integration -----------------




# =============================== LIVE VIDEO ==================================================================
@app.route("/check_camera")
def check_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Release the camera if it was not opened
        cap.release()
        # Raise an error and return JSON or render an error page
        return jsonify({"error": "Camera not detected. Please check your device and permissions."})
    cap.release()
    return jsonify({"success": "Camera not detected. Please check your device and permissions."})

@app.route("/video_feed")
def video_feed():    
    start = cv2.VideoCapture(0)
    if not start.isOpened():
        # Release the camera if it was not opened
        start.release()
        # Raise an error and return JSON or render an error page
        return jsonify({"error": "Camera not detected. Please check your device and permissions."})
    
    return Response(
        gen(start), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

def gen(camera):
    global camera_obj
    camera_obj = ObjectDetection(camera)
    camera_obj.start()
    try:
        while True:
            frame = camera_obj.get_frames()
            if frame:
                yield (
                    b"--frame\r\n" b"Content-Type: image/png\r\n\r\n" + frame + b"\r\n"
                )
            else:
                break
    except Exception as err:
        print(err)
        print("NO CAMEREA DETECETED")
        return jsonify(error="no camera detected")
    finally:
        print("CLOSING")
        camera_obj.stop()
        
@app.route("/stop_object_py")
def stop_object_py():
    global camera_obj
    try:
        captured_frame = camera_obj.get_last_frame()
        print("SUCCESS UPDATING FRAME FILE")       
        
        _, buffer = cv2.imencode('.jpg', captured_frame)
        # Convert to Base64
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify(success=True, message="Scanning", captured_frame=frame_b64)
    except Exception as e:
        return jsonify(success=False, message=str(e))
    
@app.route("/get_defects")
def get_defects():
    global camera_obj
    defects = camera_obj.defects
    html = render_template('user/partials/defect_result.html', defects=defects)
    return jsonify({
        "success":True,
        "html":html
    })
    
@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Save the file path to the database
        # Example: INSERT INTO images_table (image_path) VALUES (file_path)
        
        return "Image uploaded successfully!"
    return "No file provided!"

# LIVE VIDEO=========== END============================================





# =============================== END CV ===============================


# User dashboard
@app.route("/user/dashboard")
@login_required
def userDashboard():
    # if not session.get("user_id"):
    #     return redirect("/user/")
    
    # user_id = session.get("user_id")

    user_id = current_user.id
    user_batch_sessions = BatchSession.query.filter(BatchSession.user_id==user_id).order_by(BatchSession.batch_id.desc()).all()
    
    return render_template("user/dashboard.html", objects=user_batch_sessions)

@app.route("/user/dashboard/view/<int:id>/<string:title>")
@login_required
def view_scans(id, title):
    batch = BatchSession.query.get(id)
    scan_lists = batch.defects_detected
            
    scan_lists = DefectsDetected.query.filter(DefectsDetected.batch_id == batch.batch_id).order_by(DefectsDetected.scan_number.desc()).all()
    return render_template("user/view_scans.html", scan_lists=scan_lists, batch=batch)

@app.route("/user/dashboard/view/<int:id>/<string:title>/summary")
@login_required
def view_summary(id, title):
    batch_id = id
    batch_title = title
    
    all_defects = DefectsDetected.query.filter(DefectsDetected.batch_id == batch_id).all()
    
    primary_defects_name = [
        "full black",
        "full sour",
        "dried cherry",
        "fungus",
        "foreign matter",
        "severe insect Damage"
        ]
    
    equivalent_values = {
        "full black":1
        ,"full sour":1
        ,"dried cherry":1
        ,"fungus":1
        ,"foreign matter":1
        ,"severe insect Damage":5
        ,"partial black":3
        ,"partial sour":3
        ,"parchment":5
        ,"floater":5
        ,"immature":5
        ,"withered":5
        ,"shell":5
        ,"broken":5
        ,"husk":5,
        "slight insect damage":10}
    
    defects_list_sum = {}
    if all_defects:
        for defects in all_defects:
            defects_detected = defects.defectsDetected
            for key, value in defects_detected.items():
                if key in defects_list_sum:
                    defects_list_sum[key] += value
                    
                else:
                    # divide = defects_list_sum[key] // equivalent_values[key]
                    defects_list_sum[key] = value
                    
    # equivalent full defect values
    full_defects_count = 0
    for key in defects_list_sum:    
        divide = defects_list_sum[key] // equivalent_values[key]
        defects_list_sum[key] = defects_list_sum[key], divide
    
    
    # separate primary defects
    primary_defects_list = {}
    keys_to_delete = []
    for key in defects_list_sum:
        if key in primary_defects_name:
            primary_defects_list[key] = defects_list_sum[key]
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del defects_list_sum[key]
        
    objects = {
        "batch_id":batch_id,
        "batch_title":batch_title, 
        "defects_list_sum":defects_list_sum,
        "primary_defects_list":primary_defects_list
    }
    
    return render_template("user/view_summary.html", objects=objects)
    
# def view_summary_overall(id):
#     batch_id = id
#     primary_defects_name = [
#         {"partial black":"full black"},
#         {"partial sour","full sour"},
#         {"dried cherry"},   
#         {:"fungus"},
#         {:"foreign matter"},
#         {:"Severe Insect Damage"}
#         ]
    
#     print()

@app.route("/delete-batch/<int:batch_id>")
def delete_batch(batch_id):
    batch_selected = BatchSession.query.get(batch_id)
    b = batch_selected.defects_detected
    
    for data in b:       
        file_path = './static/final_detected_images/'+ data.scanned_image
        if os.path.exists(file_path):
            os.remove(file_path)
            db.session.delete(data)
            
    db.session.delete(batch_selected)
    db.session.commit()
    
    return redirect(url_for('userDashboard'))



@app.route("/delete-scan/<int:scan_id>")
def delete_scan(scan_id):
    # Retrieve the DefectsDetected object by ID
    defect = DefectsDetected.query.get(scan_id)
    
    if defect:
        file_path = './static/final_detected_images/'+ defect.scanned_image
        if os.path.exists(file_path):
            os.remove(file_path)
        
            # Delete the defect from the database
            db.session.delete(defect)
            db.session.commit()
            
            batch = BatchSession.query.get(defect.batch_id)
            scan_lists = batch.defects_detected
            for index,scan in enumerate(scan_lists):
                scan.scan_number = index + 1
                db.session.commit()
                
            scan_lists = DefectsDetected.query.filter(DefectsDetected.batch_id == batch.batch_id).order_by(DefectsDetected.scan_number.desc()).all()
        
            return render_template("user/partials/view_scans_update.html", scan_lists=scan_lists, batch=batch)    
        
        batch = BatchSession.query.get(defect.batch_id)
        scan_lists = batch.defects_detected
        scan_lists = DefectsDetected.query.filter(DefectsDetected.batch_id == batch.batch_id).order_by(DefectsDetected.scan_number.desc()).all()
        
    return render_template("user/partials/view_scans_update.html", scan_lists=scan_lists, batch=batch)

    
    # return redirect("url_for('userDashboard')")
    # return render_template("user/view_scans.html")

# User logout
@app.route("/user/logout")
@login_required
def userLogout():
    logout_user()
    return redirect("/")

# User change password
@app.route("/user/change-password", methods=["POST", "GET"])
@login_required
def userChangePassword():
    if not session.get("user_id"):
        return redirect("/user/")
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == "" or password == "":
            flash("Please fill the field", "danger")
            return redirect("/user/change-password")
        else:
            users = User.query.filter_by(email=email).first()
            if users:
                hash_password = bcrypt.generate_password_hash(password, 10)
                User.query.filter_by(email=email).update(dict(password=hash_password))
                db.session.commit()
                flash("Password Changed Successfully", "success")
                return redirect("/user/change-password")
            else:
                flash("Invalid Email", "danger")
                return redirect("/user/change-password")
    else:
        return render_template("user/change-password.html", title="Change Password")


if __name__ == "__main__":
    app.run(debug=True)
