import time

import av
import cv2
import spotipy
import streamlit as st
from deepface import DeepFace
from face_recognition.api import face_locations
from spotipy.oauth2 import SpotifyOAuth
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

from player import EmotionMusicPlayer

scope = "user-library-read user-read-playback-state user-modify-playback-state"
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=st.secrets["SPOTIPY_CLIENT_ID"],
        client_secret=st.secrets["SPOTIPY_CLIENT_SECRET"],
        scope=scope
    )
)


class EmotionDetector(VideoProcessorBase):
    detected_emotion = ""

    def recv(self, frame):
        DeepFace.build_model("Emotion")
        img = frame.to_ndarray(format="bgr24")
        rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations_list = face_locations(rgb_frame)
        predicted_emotion = ""
        for top, right, bottom, left in face_locations_list:
            face_roi = img[top:bottom, left:right]

            try:
                result = DeepFace.analyze(
                    face_roi,
                    actions=("emotion",),
                    enforce_detection=False
                )
                emotion_predictions = result[0]["emotion"]
                predicted_emotion = max(
                    emotion_predictions, key=emotion_predictions.get
                )
            except ValueError as e:
                predicted_emotion = "Unknown"

            text = f"Mood: {predicted_emotion}"
            cv2.putText(
                img,
                text,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
        self.detected_emotion = predicted_emotion
        return av.VideoFrame.from_ndarray(img, format="bgr24")


def main():
    st.title("Real Time Emotion Based Music Player Application")
    activities = ["Home", "About"]
    choice = st.sidebar.selectbox("Select Activity", activities)
    generic_mood = st.sidebar.selectbox("Select song type:", ["Generic", "Focused"])
    if choice == "Home":
        html_temp_home1 = """<div style="background-color:#FC4C02;padding:0.5px">     
                            <h4 style="color:white;text-align:center;">
                            Start Your Real Time Face Emotion Detection.
                             </h4>
                             </div>
                             </br>"""

        st.markdown(html_temp_home1, unsafe_allow_html=True)
        st.subheader(
            """
                * Get ready with all the emotions you can express. 
                """
        )
        st.write(
            "1. Click Start to open your camera and give permission for prediction"
        )
        st.write("2. This will predict your emotion.")
        st.write("3. Music will be played based on your mood.")
        st.write("4. Change the track by clicking the Next/Prev button.")

        ctx = webrtc_streamer(
            key="emotion",
            video_processor_factory=EmotionDetector,
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            },
            media_stream_constraints={"video": True, "audio": False},
        )
        # time.sleep(8)

        col1, col2 = st.columns([0.5, 1])
        with col1:
            next_btn = st.button("Next")
        with col2:
            prev_btn = st.button("Previous")

        music_player = EmotionMusicPlayer(sp=sp)
        while True:
            if getattr(ctx, "video_processor", None):
                detected_emotion = ctx.video_processor.detected_emotion

                if detected_emotion and generic_mood:
                    recommended_song_uris = music_player.recommend_and_store_music(
                        detected_emotion, generic_mood
                    )
                    selected_track_uri, track_uris = music_player.recommend_music(
                        detected_emotion, generic_mood
                    )

                    if selected_track_uri:
                        (
                            audio_data,
                            track_name,
                            artists,
                            preview_url,
                            player_url,
                            duration,
                        ) = music_player.play_song(selected_track_uri, [])
                        music_player.set_audio_queue(
                            audio_data,
                            track_name,
                            artists,
                            preview_url,
                            player_url,
                            duration,
                        )
                        if len(music_player.audio_queue) == 1:
                            music_player.play_next_song()

            if next_btn:
                music_player.play_next_song1()

            if prev_btn:
                music_player.play_previous_song()

            time.sleep(0.1)


# Streamlit Customisation
st.set_page_config(
    page_title="Emotion Music Player",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.sidebar.title("Settings")

st.markdown(
    """
    <style>
    body {
        background-color: white;
        font-family: Arial, sans-serif;
        margin: 0;
    }
    .stApp {
        background-color: lightblue;
        max-width: 1200px;
        margin: 0 auto;
    }
    .st-sidebar .sidebar-content {
        background-color: #333;
        color: #fff;
    }
    .st-block-container {
        padding: 20px;
        background-color: #009900
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }
    .st-title {
        font-size: 36px;
        color: #333;
    }
    .st-subheader {
        font-size: 24px;
        color: #333;
    }
    .st-button {
        background-color: #FC4C02;
        color: #FF0	;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .st-button:hover {
        background-color: #FF5733;
    }
    .st-slider {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if __name__ == "__main__":
    main()
