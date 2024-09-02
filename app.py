from flask import Flask, request, jsonify
import threading
import time
import cv2
from ultralytics import YOLO
import datetime
from twilio.rest import Client

app = Flask(__name__)

detection_thread = None
stop_event = threading.Event()
detection_count = 0
start_time = None
end_time = None
phone_number = None
detected_classes = {}

def run_detection(video_path, phone):
    global detection_count, start_time, end_time, phone_number, detected_classes
    phone_number = phone
    yolo_model_path = 'rstpmdl.pt'  # Ensure this path is correct
    model = YOLO(yolo_model_path)
    cap = cv2.VideoCapture(video_path)
    start_time = datetime.datetime.now()  # Capture the start time

    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    detected_classes = {}  # Reset detected classes for each run

    try:
        while not stop_event.is_set():  # Use stop_event to check if we need to stop the thread
            ret, frame = cap.read()
            if not ret:
                break

            yolomodel = model(frame)
            detection_count = 0  # Reset detection count for each frame

            for output in yolomodel:
                for detection in output.boxes:
                    confi = detection.conf[0]
                    class_id = int(detection.cls[0])
                    class_name = model.names[class_id]

                    if confi > 0.50:
                        if class_name in detected_classes:
                            detected_classes[class_name] += 1
                        else:
                            detected_classes[class_name] = 1
                        detection_count += 1

            time.sleep(2)  # Simulate processing time

    except Exception as e:
        print(f"Error during detection: {e}")
    finally:
        end_time = datetime.datetime.now()  # Capture the end time
        cap.release()
        cv2.destroyAllWindows()

@app.route('/start_detection', methods=['POST'])
def start_detection():
    global detection_thread, detection_count, stop_event
    video_path = request.form.get('video_path')
    phone_number = request.form.get('phone_number')

    if detection_thread and detection_thread.is_alive():
        return jsonify({'status': 'Detection already running', 'count': detection_count}), 400

    detection_count = 0  # Reset count
    stop_event.clear()  # Clear the stop event before starting a new detection
    # Start the detection in a separate thread
    detection_thread = threading.Thread(target=run_detection, args=(video_path, phone_number))
    detection_thread.start()

    return jsonify({'status': 'Detection started', 'count': detection_count})

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    global detection_thread, stop_event, start_time, end_time, detection_count
    if detection_thread and detection_thread.is_alive():
        try:
            stop_event.set()  # Signal the thread to stop
            detection_thread.join()  # Wait for the thread to finish

            # Ensure that a WhatsApp message is sent after the process stops
            send_whatsapp_message(phone_number)

            return jsonify({'status': 'Detection stopped and message sent', 'count': detection_count})
        except Exception as e:
            return jsonify({'status': f'Error stopping detection: {e}'})
    else:
        return jsonify({'status': 'No detection process running'})

def send_whatsapp_message(phone):
    # Twilio credentials
    account_sid = 'AC3bbaef04b28b5ae6c6aa66506cf4db75'
    auth_token = '95950c8efad971ca755d6b5d5b486823'   # Replace with your Twilio Auth Token
    client = Client(account_sid, auth_token)

    # Prepare detected classes summary
    class_summary = "\n".join([f"{cls}: {count}" for cls, count in detected_classes.items()])

    message_body = f"""
    Detection Report:
    Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
    End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
    Total Detections: {detection_count}

    Detected Classes:
    {class_summary}
    """

    try:
        message = client.messages.create(
            body=message_body,
            from_='whatsapp:+14155238886',  # Your Twilio WhatsApp number
            to=f'whatsapp:{phone}'  # Use the passed phone number
        )
        print(f"WhatsApp message sent: {message.sid}")
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')









# from flask import Flask, request, jsonify
# import threading
# import time
# import os
# from twilio.rest import Client
# import cv2
# from ultralytics import YOLO
# import datetime
# import signal

# app = Flask(__name__)

# detection_thread = None
# stop_event = threading.Event()
# detection_count = 0
# start_time = None
# end_time = None
# phone_number = None
# detected_classes = {}

# def run_detection(video_path, phone):
#     global detection_count, start_time, end_time, phone_number, detected_classes
#     phone_number = phone
#     yolo_model_path = 'rstpmdl.pt'
#     model = YOLO(yolo_model_path)
#     cap = cv2.VideoCapture(video_path)
#     start_time = datetime.datetime.now()  # Capture the start time

#     if not cap.isOpened():
#         print("Error: Could not open video.")
#         return

#     detected_classes = {}  # Reset detected classes for each run

#     try:
#         while not stop_event.is_set():  # Use stop_event to check if we need to stop the thread
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             yolomodel = model(frame)
#             detection_count = 0  # Reset detection count for each frame

#             for output in yolomodel:
#                 for detection in output.boxes:
#                     confi = detection.conf[0]
#                     class_id = int(detection.cls[0])
#                     class_name = model.names[class_id]

#                     if confi > 0.50:
#                         if class_name in detected_classes:
#                             detected_classes[class_name] += 1
#                         else:
#                             detected_classes[class_name] = 1
#                         detection_count += 1

#             key = cv2.waitKey(1) & 0xFF
#             if key == ord('q'):
#                 print("Terminating detection...")
#                 break

#             time.sleep(2)  # Simulate processing time

#     except Exception as e:
#         print(f"Error during detection: {e}")
#     finally:
#         end_time = datetime.datetime.now()  # Capture the end time
#         cap.release()
#         cv2.destroyAllWindows()
# @app.route('/test_connection', methods=['GET'])
# def test_connection():
#     return jsonify({'status': 'success'}), 200
# @app.route('/start_detection', methods=['POST'])
# def start_detection():
#     global detection_thread, detection_count, stop_event
#     video_path = request.form.get('video_path')
#     phone_number = request.form.get('phone_number')

#     if detection_thread and detection_thread.is_alive():
#         return jsonify({'status': 'Detection already running', 'count': detection_count}), 400

#     detection_count = 0  # Reset count
#     stop_event.clear()  # Clear the stop event before starting a new detection
#     # Start the detection in a separate thread
#     detection_thread = threading.Thread(target=run_detection, args=(video_path, phone_number))
#     detection_thread.start()

#     return jsonify({'status': 'Detection started', 'count': detection_count})

# @app.route('/stop_detection', methods=['POST'])
# def stop_detection():
#     global detection_thread, stop_event, start_time, end_time, detection_count
#     if detection_thread and detection_thread.is_alive():
#         try:
#             stop_event.set()  # Signal the thread to stop
#             detection_thread.join()  # Wait for the thread to finish

#             # Ensure that a WhatsApp message is sent after the process stops
#             send_whatsapp_message(phone_number)

#             return jsonify({'status': 'Detection stopped and message sent', 'count': detection_count})
#         except Exception as e:
#             return jsonify({'status': f'Error stopping detection: {e}'})
#     else:
#         return jsonify({'status': 'No detection process running'})

# def send_whatsapp_message(phone):
#     # Twilio credentials
#     account_sid = 'AC3bbaef04b28b5ae6c6aa66506cf4db75'
#     auth_token = '95950c8efad971ca755d6b5d5b486823'
#     client = Client(account_sid, auth_token)

#     # Prepare detected classes summary
#     class_summary = "\n".join([f"{cls}: {count}" for cls, count in detected_classes.items()])

#     message_body = f"""
#     Detection Report:
#     Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
#     End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
#     Total Detections: {detection_count}

#     Detected Classes:
#     {class_summary}
#     """

#     try:
#         message = client.messages.create(
#             body=message_body,
#             from_='whatsapp:+14155238886',  # Your Twilio WhatsApp number
#             to=f'whatsapp:{phone}'  # Use the passed phone number
#         )
#         print(f"WhatsApp message sent: {message.sid}")
#     except Exception as e:
#         print(f"Failed to send WhatsApp message: {e}")

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0')
















# from flask import Flask, request, jsonify
# import subprocess
# import threading
# import time
# import os
# from twilio.rest import Client

# app = Flask(__name__)

# process = None
# detection_count = 0
# phone_number = None  # Add this global variable to hold the phone number

# def run_detection(video_path, phone):
#     global detection_count, process, phone_number
#     phone_number = phone  # Store the phone number globally
#     yolo_model_path = 'rstpmdl.pt'
#     command = f"python detect_and_display_elephants.py --video_path {video_path} --phone_number {phone_number}"

#     # Start the process
#     process = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

#     try:
#         while True:
#             if process is None:  # Check if process has been set to None
#                 break

#             if process.poll() is not None:  # Check if the process has terminated
#                 break

#             time.sleep(2)  # Simulate processing time
#             detection_count += 1  # Increment the count (this would be updated with real data in a production system)
#     except Exception as e:
#         print(f"Error during detection: {e}")
#     finally:
#         process = None  # Ensure process is cleaned up

# @app.route('/start_detection', methods=['POST'])
# def start_detection():
#     global process, detection_count
#     video_path = request.form.get('video_path')
#     phone_number = request.form.get('phone_number')

#     if process and process.poll() is None:
#         return jsonify({'status': 'Detection already running', 'count': detection_count}), 400

#     detection_count = 0  # Reset count
#     # Start the detection in a separate thread
#     threading.Thread(target=run_detection, args=(video_path, phone_number)).start()

#     return jsonify({'status': 'Detection started', 'count': detection_count})

# @app.route('/stop_detection', methods=['POST'])
# def stop_detection():
#     global process
#     if process:
#         try:
#             # Attempt to terminate the process group
#             os.system(f'taskkill /PID {process.pid} /F /T')  # /T terminates the process and its child processes

#             # Wait for the process to terminate properly
#             process.wait()

#             # After stopping, set process to None
#             process = None

#             # Ensure that a WhatsApp message is sent after the process stops
#             send_whatsapp_message(phone_number)

#             return jsonify({'status': 'Detection stopped and message sent', 'count': detection_count})
#         except Exception as e:
#             return jsonify({'status': f'Error stopping detection: {e}'})
#     else:
#         return jsonify({'status': 'No detection process running'})

# def send_whatsapp_message(phone):

#     # Twilio credentials
#     account_sid = 'AC3bbaef04b28b5ae6c6aa66506cf4db75'
#     auth_token = '95950c8efad971ca755d6b5d5b486823'
#     client = Client(account_sid, auth_token)

#     message_body = f"""
#     Detection Report:
#     Process was successfully terminated.
#     Total Detections: {detection_count}
#     """

#     try:
#         message = client.messages.create(
#             body=message_body,
#             from_='whatsapp:+14155238886',  # Your Twilio WhatsApp number
#             to=f'whatsapp:{phone}'  # Use the passed phone number
#         )
#         print(f"WhatsApp message sent: {message.sid}")
#     except Exception as e:
#         print(f"Failed to send WhatsApp message: {e}")

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0')
