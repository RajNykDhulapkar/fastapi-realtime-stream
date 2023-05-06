import cv2
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from aiortc import RTCSessionDescription, RTCPeerConnection
from aiortc.contrib.signaling import object_from_string, object_to_string
from aiortc.contrib.media import MediaRelay, MediaStreamTrack
from av import VideoFrame


import json


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

relay = MediaRelay()


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform

    async def recv(self):
        frame = await self.track.recv()

        if self.transform == "rotate":
            # rotate image

            img = frame.to_ndarray(format="bgr24")
            rows, cols, _ = img.shape
            M = cv2.getRotationMatrix2D(
                (cols / 2, rows / 2), frame.time * 45, 1)
            img = cv2.warpAffine(img, M, (cols, rows))

            # rebuild a VideoFrame, preserving timing information
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        else:
            return frame


@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pc = RTCPeerConnection()

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()

    @pc.on("track")
    def on_track(track):
        print("Track %s received", track.kind)

        if track.kind == "audio":
            print("audio track received")
        elif track.kind == "video":
            pc.addTrack(
                VideoTransformTrack(
                    relay.subscribe(track), transform="rotate"
                )
            )
            print("video track received")

    while True:
        message = await websocket.receive_text()
        print("message: ", message[:100])
        # parse the message as JSON and notify the peer
        try:
            message = json.loads(message)
        except:
            print("message is not json")
        # print(message)

        # check if the message is a Session Description Protocol (SDP) offer
        if message['type'] == "offer":
            offer = object_from_string(json.dumps(message['data']))
            await pc.setRemoteDescription(offer)
            print("offer received")

            # create an answer and send it back to the client
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            # print("answer: ", answer)
            print("answer sent")
            await websocket.send_text("answer" + object_to_string(answer))

        # check if the message is an ICE candidate
        elif message['type'] == "candidate":
            candidate = object_from_string(json.dumps({
                "type": "candidate",
                "id": message['data']['sdpMid'],
                "label": message['data']['sdpMLineIndex'],
                **message['data']
            }))
            await pc.addIceCandidate(candidate)


# @app.websocket("/ws")
# async def signaling(websocket: WebSocket):
#     # create a new RTCPeerConnection object
#     pc = RTCPeerConnection()

#     # define a handler for ICE candidates

#     @pc.on("iceconnectionstatechange")
#     async def on_iceconnectionstatechange():
#         if pc.iceConnectionState == "failed":
#             await pc.close()

#     # loop to handle messages from the client
#     while True:
#         message = await websocket.receive_text()

#         # check if the message is a Session Description Protocol (SDP) offer
#         if message.startswith("offer"):
#             offer = object_from_string(message[6:])
#             await pc.setRemoteDescription(offer)

#             # create an answer and send it back to the client
#             answer = await pc.createAnswer()
#             await pc.setLocalDescription(answer)
#             await websocket.send_text("answer" + object_to_string(answer))

#         # check if the message is an ICE candidate
#         elif message.startswith("candidate"):
#             candidate = object_from_string(message[10:])
#             pc.addIceCandidate(candidate)
