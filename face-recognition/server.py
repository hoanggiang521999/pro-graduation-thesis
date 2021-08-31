import cv2
import tensorflow as tf
import os
from imutils.video import WebcamVideoStream  # For more performant non-blocking multi-threaded OpenCV Web Camera Stream
from scipy.misc import imread
from lib.mtcnn import detect_face  # for MTCNN face detection
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from waitress import serve
from utils import (
    load_model,
    get_face,
    get_faces_live,
    forward_pass,
    save_embedding,
    load_embeddings,
    identify_face,
    allowed_file,
    remove_file_extension,
    save_image,
    hms_to_seconds
)
from flask_cors import CORS
import mysql.connector
import time
import datetime
import numpy as np
import requests

app = Flask(__name__)
CORS(app, support_credentials=True)
app.secret_key = os.urandom(24)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
uploads_path = os.path.join(APP_ROOT, 'uploads')
embeddings_path = os.path.join(APP_ROOT, 'embeddings')
allowed_set = {'png', 'jpg', 'jpeg'}  # allowed image formats for upload

FILE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

DATABASE_USER = 'root'
DATABASE_PASSWORD = '123456'
DATABASE_HOST = 'localhost'
DATABASE_PORT = '3306'
DATABASE_NAME = 'timekeeping-manager'


def database_connection():
    return mysql.connector.connect(user=DATABASE_USER,
                                   password=DATABASE_PASSWORD,
                                   host=DATABASE_HOST,
                                   port=DATABASE_PORT,
                                   database=DATABASE_NAME)


@app.route('/upload', methods=['POST', 'GET'])
def get_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template(
                template_name_or_list="warning.html",
                status="No 'file' field in POST request!"
            )
        file = request.files['file']
        filename = file.filename

        if filename == "":
            return render_template(
                template_name_or_list="warning.html",
                status="No selected file!"
            )

        if file and allowed_file(filename=filename, allowed_set=allowed_set):
            filename = secure_filename(filename=filename)
            # Read image file as numpy array of RGB dimension
            img = imread(name=file, mode='RGB')

            # Detect and crop a 160 x 160 image containing a human face in the image file
            img = get_face(
                img=img,
                pnet=pnet,
                rnet=rnet,
                onet=onet,
                image_size=image_size
            )
            # If a human face is detected
            if img is not None:
                embedding = forward_pass(
                    img=img,
                    session=facenet_persistent_session,
                    images_placeholder=images_placeholder,
                    embeddings=embeddings,
                    phase_train_placeholder=phase_train_placeholder,
                    image_size=image_size
                )
                # Save cropped face image to 'uploads/' folder
                save_image(img=img, filename=filename, uploads_path=uploads_path)

                # Remove file extension from image filename for numpy file storage being based on image filename
                filename = remove_file_extension(filename=filename)

                # Save embedding to 'embeddings/' folder
                save_embedding(
                    embedding=embedding,
                    filename=filename,
                    embeddings_path=embeddings_path
                )

                return render_template(
                    template_name_or_list="upload_result.html",
                    status="Image uploaded and embedded successfully!"
                )
            else:
                return render_template(
                    template_name_or_list="upload_result.html",
                    status="Image upload was unsuccessful! No human face was detected!"
                )
    else:
        return render_template(
            template_name_or_list="warning.html",
            status="POST HTTP method required!"
        )


@app.route('/predictImage', methods=['POST', 'GET'])
def predict_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template(
                template_name_or_list="warning.html",
                status="No 'file' field in POST request!"
            )
        file = request.files['file']
        filename = file.filename
        if filename == "":
            return render_template(
                template_name_or_list="warning.html",
                status="No selected file!"
            )
        if file and allowed_file(filename=filename, allowed_set=allowed_set):
            # Read image file as numpy array of RGB dimension
            img = imread(name=file, mode='RGB')
            # Detect and crop a 160 x 160 image containing a human face in the image file
            img = get_face(
                img=img,
                pnet=pnet,
                rnet=rnet,
                onet=onet,
                image_size=image_size
            )
            # If a human face is detected
            if img is not None:
                embedding = forward_pass(
                    img=img,
                    session=facenet_persistent_session,
                    images_placeholder=images_placeholder,
                    embeddings=embeddings,
                    phase_train_placeholder=phase_train_placeholder,
                    image_size=image_size
                )
                embedding_dict = load_embeddings()
                if embedding_dict:
                    # Compare euclidean distance between this embedding and the embeddings in 'embeddings/'
                    identity = identify_face(
                        embedding=embedding,
                        embedding_dict=embedding_dict
                    )
                    return render_template(
                        template_name_or_list='predict_result.html',
                        identity=identity
                    )
                else:
                    return render_template(
                        template_name_or_list='predict_result.html',
                        identity="No embedding files detected! Please upload image files for embedding!"
                    )
            else:
                return render_template(
                    template_name_or_list='predict_result.html',
                    identity="Operation was unsuccessful! No human face was detected!"
                )
    else:
        return render_template(
            template_name_or_list="warning.html",
            status="POST HTTP method required!"
        )


@app.route("/live", methods=['GET'])
def face_detect_live():
    embedding_dict = load_embeddings()
    if embedding_dict:
        try:
            # Start non-blocking multi-threaded OpenCV video stream
            cap = WebcamVideoStream(src=0).start()

            while True:
                frame_orig = cap.read()  # Read frame

                # Resize frame to half its size for faster computation
                frame = cv2.resize(src=frame_orig, dsize=(0, 0), fx=0.5, fy=0.5)

                # Convert the image from BGR color (which OpenCV uses) to RGB color
                frame = frame[:, :, ::-1]

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                if frame.size > 0:
                    faces, rects = get_faces_live(
                        img=frame,
                        pnet=pnet,
                        rnet=rnet,
                        onet=onet,
                        image_size=image_size
                    )
                    # If there are human faces detected
                    if faces:
                        # * ---------- Initial JSON to EXPORT --------- *
                        json_to_export = {}
                        for i in range(len(faces)):
                            face_img = faces[i]
                            rect = rects[i]
                            # Scale coordinates of face locations by the resize ratio
                            rect = [coordinate * 2 for coordinate in rect]
                            face_embedding = forward_pass(
                                img=face_img,
                                session=facenet_persistent_session,
                                images_placeholder=images_placeholder,
                                embeddings=embeddings,
                                phase_train_placeholder=phase_train_placeholder,
                                image_size=image_size
                            )
                            # Compare euclidean distance between this embedding and the embeddings in 'embeddings/'
                            identity = identify_face(
                                embedding=face_embedding,
                                embedding_dict=embedding_dict
                            )
                            if identity != 'Unknown':
                                str_show = 'Id: ' + identity
                            else:
                                str_show = 'Unknown'
                            json_to_export['employeeCode'] = identity
                            json_to_export['hour'] = \
                                f'{time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}'
                            json_to_export['date'] = \
                                f'{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday}'
                            json_to_export['picture_array'] = frame.tolist()
                            FMT = '%H:%M:%S'
                            # Check time arrive is late or departure is soon
                            if (datetime.timedelta(seconds=hms_to_seconds(time.localtime().tm_hour,
                                                                          time.localtime().tm_min,
                                                                          time.localtime().tm_sec)) -
                                datetime.timedelta(seconds=hms_to_seconds(8, 30, 0))) >= datetime.timedelta(minutes=1):
                                json_to_export['is_late'] = 1
                                timeInterval = datetime.datetime.strptime(json_to_export['hour'],
                                                                          FMT) - datetime.datetime.strptime('08:30:00',
                                                                                                            FMT)
                                json_to_export['arrival_late_time'] = f'{timeInterval}'
                            else:
                                json_to_export['is_late'] = 0

                            if (datetime.timedelta(seconds=hms_to_seconds(17, 30, 0)) -
                                datetime.timedelta(seconds=hms_to_seconds(time.localtime().tm_hour,
                                                                          time.localtime().tm_min,
                                                                          time.localtime().tm_sec))) >= datetime.timedelta(minutes=1):
                                json_to_export['left_early'] = 1
                                timeInterval = datetime.datetime.strptime('17:30:00', FMT) - datetime.datetime.strptime(
                                    json_to_export['hour'], FMT)
                                json_to_export['departure_early_time'] = f'{timeInterval}'
                            else:
                                json_to_export['left_early'] = 0

                            cv2.rectangle(
                                img=frame_orig,
                                pt1=(rect[0], rect[1]),
                                pt2=(rect[2], rect[3]),
                                color=(0, 0, 255),
                                thickness=2
                            )
                            cv2.rectangle(
                                img=frame_orig,
                                pt1=(rect[0], rect[3] - 40),
                                pt2=(rect[2], rect[3]),
                                color=(0, 0, 255),
                                thickness=-1
                            )
                            cv2.putText(
                                img=frame_orig,
                                text=str_show,
                                org=(rect[0] + 5, rect[3] - 25),
                                fontFace=cv2.FONT_HERSHEY_DUPLEX,
                                fontScale=0.5,
                                color=(255, 255, 255),
                                thickness=1,
                                lineType=cv2.LINE_AA
                            )
                            strTime = 'Time: ' + json_to_export['hour']
                            cv2.putText(
                                img=frame_orig,
                                text=strTime,
                                org=(rect[0] + 5, rect[3] - 5),
                                fontFace=cv2.FONT_HERSHEY_DUPLEX,
                                fontScale=0.5,
                                color=(255, 255, 255),
                                thickness=1,
                                lineType=cv2.LINE_AA
                            )
                            r = requests.post(url='http://192.168.143.1:5000/receive_data', json=json_to_export)
                            print("Status: ", r.status_code)
                        cv2.imshow(winname='Video', mat=frame_orig)
                    # Keep showing camera stream even if no human faces are detected
                    cv2.imshow(winname='Video', mat=frame_orig)
                else:
                    continue
            cap.stop()  # Stop multi-threaded Video Stream
            cv2.destroyAllWindows()

            return render_template(template_name_or_list='index.html')

        except Exception as e:
            print(e)

    else:
        return render_template(
            template_name_or_list="warning.html",
            status="No embedding files detected! Please upload image files for embedding!"
        )


@app.route('/receive_data_test', methods=['POST'])
def get_receive_data_test():
    if request.method == 'POST':
        json_data = request.get_json()
        print('jsondata', json_data)
        return jsonify(json_data)


@app.route('/receive_data', methods=['POST'])
def get_receive_data():
    if request.method == 'POST':
        json_data = request.get_json()

        # Check if the user is already in the DB
        connection = database_connection()
        try:
            # Connect to the DB
            cursor = connection.cursor()

            # Get employee_id by employee_code from json data
            employee_id_query = \
                f"SELECT employee_id FROM employee WHERE 1=1 AND employee_code = '{json_data['employeeCode']}'"
            cursor.execute(employee_id_query)
            employee_id = cursor.fetchone()

            cursor = connection.cursor()
            # Query to check if the user as been saw by the camera today
            user_saw_today_sql_query = \
                f"SELECT arrival_time, departure_time FROM timekeeping WHERE 1=1 AND " \
                f"DATE(date_timekeeping) = '{json_data['date']}' AND employee_id = {employee_id[0]}"
            cursor.execute(user_saw_today_sql_query)
            result = cursor.fetchall()
            connection.commit()
            # If use is already in the DB for today:
            if result:
                print('User OUT')
                time_in = result[0][0]
                time_out = result[0][1]
                time_now = datetime.datetime.now()
                is_continue = True
                if time_out is None:
                    minus_time = datetime.timedelta(
                        seconds=hms_to_seconds(time_now.hour, time_now.minute, time_now.second)) - time_in
                    if minus_time < datetime.timedelta(minutes=5):
                        is_continue = False
                else:
                    minus_time = datetime.timedelta(
                        seconds=hms_to_seconds(time_now.hour, time_now.minute, time_now.second)) - time_out
                    if minus_time < datetime.timedelta(minutes=5):
                        is_continue = False

                if is_continue is True:
                    image_path = f"{FILE_PATH}/assets/img/{json_data['date']}/{json_data['employeeCode']}/departure.jpg"

                    # Save image
                    os.makedirs(f"{FILE_PATH}/assets/img/{json_data['date']}/{json_data['employeeCode']}",
                                exist_ok=True)
                    cv2.imwrite(image_path, np.array(json_data['picture_array']))
                    json_data['picture_path'] = image_path

                    # Update timekeeping in the DB
                    if json_data['left_early'] == 1:
                        update_timekeeping_query = \
                            f"UPDATE timekeeping SET departure_time = '{json_data['hour']}', " \
                            f"departure_picture = '{json_data['picture_path']}', left_early = {json_data['left_early']}, departure_early_time = '{json_data['departure_early_time']}' " \
                            f"WHERE employee_id = {employee_id[0]} " \
                            f"AND DATE(date_timekeeping) = '{json_data['date']}'"
                        cursor.execute(update_timekeeping_query)
                    else:
                        update_timekeeping_query = \
                            f"UPDATE timekeeping SET departure_time = '{json_data['hour']}', " \
                            f"departure_picture = '{json_data['picture_path']}', left_early = {json_data['left_early']}" \
                            f"WHERE employee_id = {employee_id[0]} " \
                            f"AND DATE(date_timekeeping) = '{json_data['date']}'"
                        cursor.execute(update_timekeeping_query)
                else:
                    print('Ban ghi moi chua qua 5 phut')
            else:
                print("User IN")
                # Save image
                image_path = \
                    f"{FILE_PATH}/assets/img/history/{json_data['date']}/{json_data['employeeCode']}/arrival.jpg"
                os.makedirs(f"{FILE_PATH}/assets/img/history/{json_data['date']}/{json_data['employeeCode']}",
                            exist_ok=True)
                cv2.imwrite(image_path, np.array(json_data['picture_array']))
                json_data['picture_path'] = image_path

                # Create a new row for the user today:
                if json_data['is_late'] == 1:
                    insert_user_query = f"INSERT INTO timekeeping " \
                                        f"(employee_id, date_timekeeping, arrival_time, arrival_picture, is_late, arrival_late_time) VALUES " \
                                        f"({employee_id[0]}, " \
                                        f"'{json_data['date']}', " \
                                        f"'{json_data['hour']}', " \
                                        f"'{json_data['picture_path']}', " \
                                        f"{json_data['is_late']}, " \
                                        f"'{json_data['arrival_late_time']}')"
                    cursor.execute(insert_user_query)
                else:
                    insert_user_query = f"INSERT INTO timekeeping " \
                                        f"(employee_id, date_timekeeping, arrival_time, arrival_picture, is_late) VALUES " \
                                        f"({employee_id[0]}, " \
                                        f"'{json_data['date']}', " \
                                        f"'{json_data['hour']}', " \
                                        f"'{json_data['picture_path']}', " \
                                        f"{json_data['is_late']}) "
                    cursor.execute(insert_user_query)
                print("Insert done")

        except (Exception, mysql.connector.DatabaseError) as error:
            print("ERROR DB: ", error)
        finally:
            connection.commit()

            # closing database connection.
            if connection:
                cursor.close()
                connection.close()
                print("MySQL connection is closed")

            # Return user's data to the front
        return jsonify(json_data)


@app.route("/")
def index_page():
    """Renders the 'index.html' page for manual image file uploads."""
    return render_template(template_name_or_list="index.html")


@app.route("/predict")
def predict_page():
    """Renders the 'predict.html' page for manual image file uploads for prediction."""
    return render_template(template_name_or_list="predict.html")


if __name__ == '__main__':
    """Server and FaceNet Tensorflow configuration."""

    # Load FaceNet model and configure placeholders for forward pass into the FaceNet model to calculate embeddings
    model_path = 'model/20170512-110547/20170512-110547.pb'
    facenet_model = load_model(model_path)
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    image_size = 160
    images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
    embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
    phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

    # Initiate persistent FaceNet model in memory
    facenet_persistent_session = tf.Session(graph=facenet_model, config=config)

    # Create Multi-Task Cascading Convolutional (MTCNN) neural networks for Face Detection
    pnet, rnet, onet = detect_face.create_mtcnn(sess=facenet_persistent_session, model_path=None)

    # Start flask application on waitress WSGI server
    serve(app=app, host='0.0.0.0', port=5000)
