ffmpeg -re -f v4l2 -i /dev/video0 -s 1280x720 -c:v libx264 -preset ultrafast -tune zerolatency -flags low_delay -c:a aac -f flv rtmp://localhost/live/video1
