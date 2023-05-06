import React, { useEffect, useRef } from "react";

function App() {
  const videoRef = useRef(null);
  const friendsVideoRef = useRef(null);

  useEffect(() => {
    // Get user media
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: false })
      .then((stream) => {
        // Set video source
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        console.log("Video source set", stream);

        // Create a new RTCPeerConnection object
        const peerConnection = new RTCPeerConnection({
          iceServers: [
            {
              urls: "stun:stun.stunprotocol.org",
            },
          ],
        });

        // Add the local stream to the peer connection
        stream.getTracks().forEach((track) => {
          peerConnection.addTrack(track, stream);
        });

        // Set the remote description
        peerConnection.addEventListener("track", (event) => {
          console.log("Track received", event);
          friendsVideoRef.current.srcObject = event.streams[0];
          friendsVideoRef.current.play();
        });

        // Send the stream to the server
        // const socket = io.connect("http://localhost:8000/ws");
        const socket = new WebSocket("ws://localhost:8000/websocket");

        socket.onopen = () => {
          console.log("Socket connected");
          // socket.send(JSON.stringify({ type: "stream", data: stream.id }));

          // Handle ICE candidates for the peer connection
          peerConnection.addEventListener("icecandidate", (event) => {
            if (event.candidate) {
              console.log("Sending ICE candidate", event);
              socket.send(
                JSON.stringify({ type: "candidate", data: event.candidate })
              );
            }
          });

          // Create an offer and send it to the server
          peerConnection
            .createOffer()
            .then((offer) => {
              return peerConnection.setLocalDescription(offer);
            })
            .then(() => {
              if (socket.readyState === WebSocket.OPEN) {
                console.log("Offer created");
                console.log("offer sent to server");
                socket.send(
                  JSON.stringify({
                    type: "offer",
                    data: peerConnection.localDescription,
                  })
                );
              }
            });
        };

        socket.onmessage = (event) => {
          console.log("Socket message received", event.type);
          let message;
          try {
            message = JSON.parse(event.data);
          } catch (err) {
            message = event;
          }

          if (message.data.startsWith("offer")) {
            console.log("Offer received");
            message = {
              type: "offer",
              data: JSON.parse(message.data.replace("offer", "")),
            };
          } else if (message.data.startsWith("answer")) {
            console.log("Answer received");
            message = {
              type: "answer",
              data: JSON.parse(message.data.replace("answer", "")),
            };
          } else if (message.data.startsWith("candidate")) {
            console.log("Candidate received");
            message = {
              type: "candidate",
              data: JSON.parse(message.data.replace("candidate", "")),
            };
          } else {
            console.log("Stream received");
            message = {
              type: "stream",
              data: message.data,
            };
          }

          if (message.type === "stream") {
            friendsVideoRef.current.srcObject = message.data;
            friendsVideoRef.current.play();
          } else if (message.type === "offer") {
            peerConnection
              .setRemoteDescription(new RTCSessionDescription(message.data))
              .then(() => {
                return peerConnection.createAnswer();
              })
              .then((answer) => {
                return peerConnection.setLocalDescription(answer);
              })
              .then(() => {
                console.log("Answer created");
                socket.send(
                  JSON.stringify({
                    type: "answer",
                    data: peerConnection.localDescription,
                  })
                );
              });
          } else if (message.type === "answer") {
            console.log("Answer received from server");
            peerConnection.setRemoteDescription(
              new RTCSessionDescription(message.data)
            );
          } else if (message.type === "icecandidate") {
            peerConnection.addIceCandidate(new RTCIceCandidate(message.data));
          }
        };
      })
      .catch((err) => console.log(err));
  }, []);

  return (
    <div className="">
      <div className="flex gap-10 bg-slate-100 rounded-lg  m-10 p-10">
        <video className="border border-black" ref={videoRef} />
        <video className="border border-black" ref={friendsVideoRef} />
      </div>
    </div>
  );
}

export default App;
