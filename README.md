# octoprint adaptions for octoprint running on RPI4 with new picamera2

replacement for https://github.com/jacksonliam/mjpg-streamer.git // mjpg-streamer-experimental used from within [octoprint](https://octoprint.org).

## Description

After upgrading my raspberry pi 4 from bullseye running [octoprint](https://octoprint.org)-installation (I think, or even the octoprint-image itself), the 
camera did not work anymore or to be more precise, the camera could not be used properly anymore with mjpeg-streamer.

Something around camera support changing to be about a new library and mjpeg-streamer failing
* https://octoprint.org/blog/2023/05/24/a-new-camera-stack-for-octopi/
* https://github.com/raspberrypi/picamera2

I also tried to get something working with ```rpicam-vid -t 0 --inline --listen -o tcp://0.0.0.0:8888``` and so 
just relaying that to mjpeg_streamer. But that was no fun at all.

## Getting Started

### Dependencies

#### hardware / environment
  * libcap2-dev
  * picamera2
  * raspberry-pi 4
  * rapsbian bookworm
  * installed picamera2-libraries /-apps (e.g. by issuing ```sudo apt -y install rpicam-apps```)
  * camera (not necessarily csi connected, but that was my starting point)
    ```
    # libcamera-hello --list-cameras
    Available cameras
    -----------------
    0 : ov5647 [2592x1944 10-bit GBRG] (/base/soc/i2c0mux/i2c@1/ov5647@36)
        Modes: 'SGBRG10_CSI2P' : 640x480 [30.00 fps - (65535, 65535)/65535x65535 crop]
                                 1296x972 [30.00 fps - (65535, 65535)/65535x65535 crop]
                                 1920x1080 [30.00 fps - (65535, 65535)/65535x65535 crop]
                                 2592x1944 [30.00 fps - (65535, 65535)/65535x65535 crop]
    ```


#### software / environment
  * systemlibcap2-dev (e.g. ```apt -y install systemlibcap2-dev````)
  * picamera2
  * octoprint-manual-setup described here: https://community.octoprint.org/t/setting-up-octoprint-on-a-raspberry-pi-running-raspberry-pi-os-debian/2337

#### Notes
* maybe the installation on an octoprint-image would also work, but it may be the files have different locations


### Installing
assuming, the installation was done as described here: https://community.octoprint.org/t/setting-up-octoprint-on-a-raspberry-pi-running-raspberry-pi-os-debian/2337
* copy mjpeg_server_with_capture.py to /home/pi/mjpeg_server_with_capture.py
* EITHER: 
  * edit /home/pi/scripts/webcamDaemon to include the lines in webcamDaemon at the beginning (which basically keeps the orignal code inactive since the ```exit $?``` skips the rest of the file)
* OR:
  * just copy webcamDaemon to /home/pi/scripts/webcamDaemon and make sure it is set to executable (chmod)
* ```systemctl restart webcamd``` to restart the webcamDaemon and to use the new code
* copy over haproxy.cfg to /etc/haproxy/haproxy.cfg (or make the appropriate adaptions)
* the new webcam-server is streaming mjpeg on http://WHATEVERIP:8000/stream.mjpg
  * haproxy is offering this also (as reverse-proxy) on http://WHATEVERIP/webcam2/stream.mjpg and on http://WHATEVERIP/webcam2/?action=stream 
* the new webcam-server is providing jpg snapshots on http://WHATEVERIP:8000/snapshot.jpg and on http://WHATEVERIP:8000/?action=snapshot 
  * haproxy is offering this also (as reverse-proxy) on http://WHATEVERIP/webcam2/snapshot.jpg and on http://WHATEVERIP/webcam2/?action=snapshot
* adapt the settings for the webcam in octoprint to reflect the new ports (e.g. change STREAM-URL to ```/webcam2/stream.mjpg``` and SNAPSHOT-URL to ```http://127.0.0.1:8000/?action=snapshot```) 

### Executing program

* if you have followed the installation from above, it should already be working 


## Authors

Contributors names and contact info

* This repo's owner
* Other people mentioned/credited in the files

## Version History

* -0.42
    * there will be no proper versioning
    * earlier versions used INA219, but INA226 seems to be 
      more accurate and can additionally/also monitor voltage on the high side whilst 
      monitoring current on the low side.
  

## License

This project is licensed under the LGPL where applicable/possible License - see the [LICENSE.md](LICENSE.md) file for details.
Some files/part of files could be governed by different/other licenses and/or licensors, 
such as (e.g., but not limited to) [MIT](LICENSEMIT.md) | [GPL](LICENSEGPL.md) | [LGPL](LICENSELGPL.md); so please also 
regard/pay attention to comments in regards to that throughout the codebase / files / part of files.

## Acknowledgments

Inspiration, code snippets, etc.
* please see comments in files for that



## TODO
* make width / height configurable (at the moment just edit mjpeg_sever_with_capture.py)
* framerate-settings perhaps
  
## NOTES
It seems to run smoothly, and the performance seems to be amazing so far - there is not even a 
hint of flickering left in the frames (which happened quite a lot in the last weeks).
