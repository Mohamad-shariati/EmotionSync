import os
import cv2
import numpy as np
import requests
import time
import json
import struct
import socket
from deepface import DeepFace

# تنظیمات دوربین
username = "admin"
password = "admin"
url = "http://192.168.1.3:8080/shot.jpg"

# تنظیمات UDP
UDP_IP = "127.0.0.1"
UDP_PORT = 8000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# مسیر فایل JSON
dir_path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(dir_path, "wazowski.json")

last_analysis_time = 0
analysis_interval = 1.0  # ثانیه
message_counter = 0

while True:
    # دریافت و نمایش فریم
    resp = requests.get(url, auth=(username, password))
    img_array = np.array(bytearray(resp.content), dtype=np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    cv2.imshow("Camera Feed", frame)

    # آنالیز هر ثانیه یکبار
    current_time = time.time()
    if current_time - last_analysis_time >= analysis_interval:
        try:
            # آنالیز احساسات
            result = DeepFace.analyze(frame, actions=['emotion'])
            if isinstance(result, list):
                result = result[0]

            # استخراج دیکشنری احساسات و مرتب‌سازی بر اساس احتمال
            emotions = result["emotion"]
            sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)

            # آماده‌سازی داده JSON
            message_counter += 1
            data = {
                "message": str(message_counter),
                "Emotion1": sorted_emotions[0][0],
                "Emotion2": sorted_emotions[1][0],
                "Emotion3": sorted_emotions[2][0],
                "Emotion4": sorted_emotions[3][0],
            }

            # نوشتن فایل JSON
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"[{message_counter}] JSON written:", data)

            # خواندن باینری و ارسال UDP
            with open(filename, "rb") as f:
                file_data = f.read()
            header = struct.pack('>I', len(file_data))
            packet = header + file_data
            sock.sendto(packet, (UDP_IP, UDP_PORT))
            print(f"[{message_counter}] Sent {len(packet)} bytes to {UDP_IP}:{UDP_PORT}")

            # نمایش dominant emotion روی فریم
            dominant = sorted_emotions[0][0]
            cv2.putText(frame,
                        dominant,
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2)

        except Exception as e:
            print("Error in analysis or send:", e)

        last_analysis_time = current_time

    # خروج با q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

sock.close()
cv2.destroyAllWindows()
