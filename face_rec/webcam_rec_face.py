# -*- coding:utf-8 -*-
# @last update time:2022/11/6 17:05
import face_recognition
import cv2
import numpy as np
import os
import threading
import datetime

# This is a demo of running face recognition on live video from your webcam. It's a little more complicated than the
# other example, but it includes some basic performance tweaks to make things run a lot faster:
#   1. Process each video frame at 1/4 resolution (though still display it at full resolution)
#   2. Only detect faces in every other frame of video.

# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.
# OpenCV is *not* required to use the face_recognition library. It's only required if you want to run this
# specific demo. If you have trouble installing it, try any of the other demos that don't require it instead.

# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

# Load a sample picture and learn how to recognize it.
fido_pic_path = os.path.join(os.path.dirname(__file__), 'data/fido/IMG_20170903_085232.jpg')
if os.path.exists(fido_pic_path):
    fido_image = face_recognition.load_image_file(fido_pic_path)
    fido_face_encoding = face_recognition.face_encodings(fido_image)[0]
else:
    fido_face_encoding = None

# Load a second sample picture and learn how to recognize it.
# biden_image = face_recognition.load_image_file("biden.jpg")
# biden_face_encoding = face_recognition.face_encodings(biden_image)[0]

# Create arrays of known face encodings and their names
if fido_face_encoding is not None:
    known_face_encodings = [
        fido_face_encoding,
        # biden_face_encoding
    ]
    known_face_names = [
        "fido",
        # "Joe Biden"
    ]
else:
    known_face_encodings = None
    known_face_names = None

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

def get_vedio_result(is_save_result=True, 
                    path = os.path.join(os.path.dirname(__file__), 'data/result')):
    while process_this_frame:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Only process every other frame of video to save time
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        name = "Unknown"
        for face_encoding in face_encodings:
            if known_face_encodings is not None:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

            face_names.append(name)

        if known_face_names is not None:
            if known_face_names[0] in face_names:
                if is_save_result:
                    _is_save_result(is_save_result, path,frame,face_locations,face_names)
                return True
        elif len(face_names)>0:
            _is_save_result(is_save_result, path,frame,face_locations,face_names)
            return True

def _is_save_result(is_save_result:bool, path:str,frame,face_locations,face_names):
    if is_save_result:
        os.makedirs(path, exist_ok=True)
        filename = '.'.join(str(datetime.datetime.now()).split(':'))+'.png'
        filename = os.path.join(path, filename)
        threading.Thread(target=save_result_img,
                        args=(face_locations, face_names,frame,filename)
                        ).start()

def save_result_img(face_locations, face_names, frame,filename):
     # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
    cv2.imwrite(filename=filename, img=frame)


def release_webcam_resource():
    # Release handle to the webcam
    video_capture.release()


if __name__ == "__main__":
    get_vedio_result()
    release_webcam_resource()