from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
import cv2

app = FastAPI()


def stream_video():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(frame) + b'\r\n')

    cap.release()


@app.get('/video_feed')
async def video_feed():
    return StreamingResponse(stream_video(), media_type="multipart/x-mixed-replace;boundary=frame")


@app.get('/')
async def homepage():
    html_content = """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <img  
            style="width: 400px; height: 300px;"
            src="/video_feed" />
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
