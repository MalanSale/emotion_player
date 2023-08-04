components.html("""
<html>
<head>
   <title>Music player based on emotion detection to help with focus</title>
   <style>
      *{
         background-color: #242926;
      }
      #videoCam {
         width: 900px;
         height: 400px;
         margin-left: 0px;
         border: 3px solid #ccc;
         background: white;
      }
      #startBtn {
         margin-left: 390px;
         width: 120px;
         height: 45px;
         cursor: pointer;
         font-weight: bold;
      }
      #startBtn:hover{
         background-color: #2ade5a;
         color: black;
      }
   </style>
</head>
<body>
   <h1><font color=white>EmDef</h1>
   <br/>
   <video id="videoCam"></video>
   <br/><br/>
   <button id="startBtn" onclick="openCam()">Open Camera</button>
   <script>
      function openCam(){
         let All_mediaDevices=navigator.mediaDevices
         if (!All_mediaDevices || !All_mediaDevices.getUserMedia) {
            console.log("getUserMedia() not supported.");
            return;
         }
         All_mediaDevices.getUserMedia({
            audio: false,
            video: true
         })
         .then(function(vidStream) {
            var video = document.getElementById('videoCam');
            if ("srcObject" in video) {
               video.srcObject = vidStream;
            } else {
               video.src = window.URL.createObjectURL(vidStream);
            }
            video.onloadedmetadata = function(e) {
               video.play();
            };
         })
         .catch(function(e) {
            console.log(e.name + ": " + e.message);
         });
      }
   </script> 
</body>
</html>""", width=920, height=600, scrolling=True)


#components.html("")
