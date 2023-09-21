import base64
import time
import av
import cv2
import spotipy
import streamlit as st
from deepface import DeepFace
from face_recognition.api import face_locations
from spotipy.oauth2 import SpotifyOAuth
from streamlit_option_menu import option_menu
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
from player import EmotionMusicPlayer
import os

os.environ["SPOTIPY_CLIENT_ID"] = st.secrets["SPOTIPY_CLIENT_ID"]
os.environ["SPOTIPY_CLIENT_SECRET"] = st.secrets["SPOTIPY_CLIENT_SECRET"]
os.environ["SPOTIPY_REDIRECT_URI"] = st.secrets["SPOTIPY_REDIRECT_URI"]

# Use the Spotify API client credentials flow (no user authentication required)
sp = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyClientCredentials())

query = "genre:pop"
track_uris = sp.search(query, limit=1, type="track")
print(track_uris)

company_name = "ChillTrill"

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
                    face_roi, actions=("emotion",), enforce_detection=False
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
    SPR_SPOTIFY_URL = 'https://cdn-icons-png.flaticon.com/512/2111/2111624.png'
    st.sidebar.image(SPR_SPOTIFY_URL,use_column_width=False, width=200, )
    with st.sidebar:
        menu = option_menu(
            None,
            ["Home", "About"],
            icons=["house", "info"],
            menu_icon="cast",
            default_index=0,
        )
    generic_mood = st.sidebar.radio("Select song type", options=["Generic", "Focused"])
    if menu == "Home":
        html_temp_home1 = """<div style="border:groove;padding:0.5px">     
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

        col1, col2 = st.columns([0.5, 1])
        with col1:
            next_btn = st.button("Next")
        with col2:
            prev_btn = st.button("Previous")
        time.sleep(8)
        music_player = EmotionMusicPlayer(sp=sp)
        print(music_player)
        while True:
            if getattr(ctx, "video_processor", None):
                detected_emotion = ctx.video_processor.detected_emotion
                print('Detected emotion',detected_emotion)
               
                if detected_emotion and generic_mood:
                    recommended_song_uris = music_player.recommend_and_store_music(
                            detected_emotion, generic_mood
                        )
                    print(recommended_song_uris)
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
    elif menu == "About":
        st.markdown(
            f"""
                <section>
                    <h2>Welcome to {company_name}</h2>
                    <p>
                        Welcome to {company_name}, where music meets emotions in a harmonious blend of technology and artistry. Our mission is to transform the way you experience music by creating a dynamic, deeply personal, and emotionally resonant listening experience.
                    </p>
                </section>
                <section>
                    <h2>Our Story</h2>
                    <p>
                        At {company_name}, we believe that music is more than just sound. It's a powerful medium that has the ability to touch our souls, evoke memories, and connect us to our deepest emotions. With this belief, we embarked on a journey to create an app that would revolutionize the way people interact with their music.
                    </p>
                    <p>
                        Our team of music enthusiasts, engineers, and designers came together with a shared passion for leveraging cutting-edge technology to enhance the emotional impact of music. We wanted to create an app that not only plays your favorite songs but also understands and responds to your feelings.
                    </p>
                </section>
                <section>
                    <h2>How It Works</h2>
                    <p>
                        Our emotion-based music player is built on a sophisticated algorithm that analyzes your emotional state in real-time. By using a combination of audio analysis, user input, and machine learning, we can accurately identify your current mood and tailor the music to match it.
                    </p>
                    <p>
                        Whether you're feeling upbeat and energetic or introspective and relaxed, [Your App Name] has a playlist ready to accompany your emotional journey. You can also customize your music experience by adjusting the settings to fine-tune the emotional resonance of your playlist.
                    </p>
                </section>
                <section>
                    <h2>Why Choose Us</h2>
                    <ul>
                        <li><strong>Emotion-Driven Playlists:</strong> Experience music that syncs with your feelings, making every listening session a unique and immersive experience.</li>
                        <li><strong>Personalized Recommendations:</strong> Our app learns your music preferences and emotional triggers, offering you songs and playlists that resonate with you on a deeper level.</li>
                        <li><strong>User-Centric Design:</strong> We've designed our app with simplicity and user-friendliness in mind, ensuring that everyone, from music aficionados to casual listeners, can enjoy a seamless experience.</li>
                        <li><strong>Privacy and Security:</strong> Your emotional data and personal information are treated with the utmost care. We prioritize your privacy and adhere to strict security protocols.</li>
                    </ul>
                </section>
                <section>
                    <h2>Join Us on This Journey</h2>
                    <p>
                        At {company_name}, we're committed to continuously improving and innovating our app to provide you with the best possible music experience. Join us on this exciting journey as we explore the uncharted territory of emotion-driven music.
                    </p>
                    <p>
                        Thank you for choosing {company_name} as your music companion. Together, we'll discover the incredible emotional power of music and make every note count.
                    </p>
                </section>
            """,
            unsafe_allow_html=True,
        )


# Streamlit Customisation
st.set_page_config(
    page_title=company_name,
    page_icon="🎵",
)
st.markdown(
    f"""
    <style>
    .stApp {{
        background: url(data:image/jpg;base64,{base64.b64encode(open("assets/images/cover.jpg", "rb").read()).decode()});
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
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
    </style>
    """,
    unsafe_allow_html=True,
)


if __name__ == "__main__":
    main()
