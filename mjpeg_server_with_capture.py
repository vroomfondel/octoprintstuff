#!/usr/bin/python3

# This is the same as mjpeg_server.py, but uses the h/w MJPEG encoder.
# BASED ON https://github.com/raspberrypi/picamera2
# ESPECIALLY ON https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server_2.py
# IN CONJUNCTION WITH https://github.com/raspberrypi/picamera2/blob/main/examples/still_during_video.py

# DATASHEET: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf

import sys
import io
import json
import logging
import socketserver
from http import server
from threading import Condition
from typing import Tuple

from picamera2 import Picamera2, MappedArray
from picamera2.encoders import MJPEGEncoder, Quality
from picamera2.outputs import FileOutput

import time

INSTALL_CV2_IF_MISSING: bool = True

try:
    import cv2
except Exception as cv2ex:
    print(str(cv2ex), flush=True)

    if INSTALL_CV2_IF_MISSING:
        try:
            print("TRYING TO INSTALL VIA PIP INTERNALLY...", flush=True)

            import pip

            if hasattr(pip, 'main'):
                #pip.main(['install', "--break-system-packages", "opencv-python"])
                pip.main(['install', "opencv-python"])
            else:
                # pip._internal.main(['install', "--break-system-packages", "opencv-python"])
                pip._internal.main(['install', "--break-system-packages", "opencv-python"])

            import cv2
        except Exception as intpip:
            print(str(intpip), flush=True)

            print("TRYING TO INSTALL VIA 'sudo apt'...", flush=True)

            import subprocess
            subprocess.check_call(["sudo", "apt", "-y", "install", "python3-opencv"])

            import cv2





# https://www.libcamera.org/getting-started.html
import libcamera

NRM: libcamera.controls.draft.NoiseReductionModeEnum = libcamera.controls.draft.NoiseReductionModeEnum.HighQuality  # libcamera.controls.draft.NoiseReductionModeEnum.HighQuality  # libcamera.controls.draft.NoiseReductionModeEnum.Fast  # .Minimal ?!
ENCQ: Quality = Quality.HIGH
WIDTH: int = 960  #640  #1920  #1296  # 960
HEIGHT: int = 720  #480  #1080  #972  # 720
FRAMERATE: int = 7
BUFFER_COUNT: int = 6  # DEFAULT: 6


TIMESTAMP_TEXT_COLOUR: Tuple[int, int, int] = (0, 255, 0)
TIMESTAMP_TEXT_ORIGIN: Tuple[int, int] = (0, 30)
TIMESTAMP_TEXT_FONT = cv2.FONT_HERSHEY_SIMPLEX
TIMESTAMP_TEXT_SCALE: int = 1
TIMESTAMP_TEXT_THICKNESS = 2

def apply_timestamp(request):
  timestamp = time.strftime("%Y-%m-%d %X")
  with MappedArray(request, "main") as m:
    cv2.putText(m.array, timestamp, TIMESTAMP_TEXT_ORIGIN, TIMESTAMP_TEXT_FONT, TIMESTAMP_TEXT_SCALE, TIMESTAMP_TEXT_COLOUR, TIMESTAMP_TEXT_THICKNESS)



PAGE = f"""\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="{WIDTH}" height="{HEIGHT}" />
</body>
</html>
"""


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/capture.jpg' or self.path == '/?action=snapshot':
            request = picam2.capture_request()
            # request.save("main", "test.jpg")
            data = io.BytesIO()
            request.save('main', data, format='jpeg')
            request.release()

            buff = data.getbuffer()

            print(f"{len(buff)=}")

            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', len(buff))
            self.end_headers()

            self.wfile.write(buff)

        elif self.path == '/stream.mjpg' or self.path == '/?action=stream':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam2 = Picamera2()

# tuning = Picamera2.load_tuning_file("imx477_noir.json")
# picam2 = Picamera2(tuning=tuning)
#
# config = picam2.create_still_configuration(raw={'format': 'SBGGR12', 'size': (4056, 3040)})
# picam2.configure(config)
# print('Sensor configuration:', picam2.camera_configuration()['sensor'])
# print('Stream Configuration:', picam2.camera_configuration()['raw'])

#  Transform(hflip=True, vflip=True)

video_conf: dict = picam2.create_video_configuration(
    main={"size": (WIDTH, HEIGHT)},
    controls={"FrameRate": FRAMERATE, "NoiseReductionMode": NRM},
    buffer_count=BUFFER_COUNT
)



from uuid import UUID
from datetime import date
from datetime import timedelta
from datetime import datetime

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'reprJSON'):
            return obj.reprJSON()
        elif type(obj) == UUID:
            obj: UUID
            return str(obj)
        elif type(obj) == datetime:
            obj: datetime
            return obj.strftime("%Y-%m-%d %H:%M:%S %Z")
        elif type(obj) == date:
            obj: date
            return obj.strftime("%Y-%m-%d")
        elif type(obj) == timedelta:
            obj: timedelta
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


print("VIDEO_CONF:", flush=True)
print(json.dumps(video_conf, indent=4, sort_keys=True, cls=ComplexEncoder, default=str), flush=True)


picam2.align_configuration(video_conf)


print("VIDEO_CONF_AFTER_ALIGNMENT:", flush=True)
print(json.dumps(video_conf, indent=4, sort_keys=True, cls=ComplexEncoder, default=str), flush=True)



picam2.configure(video_conf)
picam2.pre_callback = apply_timestamp

output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output), quality=ENCQ)

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
