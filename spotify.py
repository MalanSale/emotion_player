import base64
import os
import random
import time
import av
import cv2
import mediapipe as mp
import spotipy
import streamlit as st
from deepface import DeepFace
from face_recognition.api import face_locations
from spotipy.oauth2 import SpotifyOAuth
from streamlit_webrtc import webrtc_streamer

os.environ["SPOTIPY_CLIENT_ID"] = st.secrets["SPOTIPY_CLIENT_ID"]
os.environ["SPOTIPY_CLIENT_SECRET"] = st.secrets["SPOTIPY_CLIENT_SECRET"]
os.environ["SPOTIPY_REDIRECT_URI"] = st.secrets["SPOTIPY_REDIRECT_URI"]
scope = "user-library-read user-read-playback-state user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

holistic = mp.solutions.holistic
hands = mp.solutions.hands
hol = holistic.Holistic()
drawing = mp.solutions.drawing_utils


class EmotionMusicPlayer:
    genres = {
        "relax": [
            "acoustic",
            "ambient",
            "chill",
            "downtempo",
            "new-age",
            "piano",
            "sleep",
            "trip-hop",
            "classical",
        ],
        "energetic": [
            "afrobeat",
            "anime",
            "breakbeat",
            "british",
            "dance",
            "detroit-techno",
            "j-dance",
            "j-idol",
            "j-pop",
            "j-rock",
            "k-pop",
            "party",
            "power-pop",
            "progressive-house",
            "road-trip",
            "rockabilly",
            "summer",
            "swedish",
            "techno",
            "trance",
            "work-out",
        ],
        "angry": [
            "black-metal",
            "death-metal",
            "grindcore",
            "hardcore",
            "punk",
            "punk-rock",
        ],
        "neutral": [
            "alternative",
            "jazz",
            "singer-songwriter",
            "classical",
            "indian classical",
        ],
        "surprise": ["bossanova", "disco", "show-tunes"],
        "happy": [
            "brazil",
            "cantopop",
            "comedy",
            "disco",
            "disney",
            "edm",
            "funk",
            "happy",
            "honky-tonk",
            "latin",
            "reggaeton",
            "rock-n-roll",
            "salsa",
            "sertanejo",
            "spanish",
            "world-music",
            "bollywood hits",
            "hollywood hits",
        ],
        "sad": [
            "blues",
            "emo",
            "folk",
            "grunge",
            "metal",
            "pop-film",
            "sad",
            "songwriter",
            "classical",
            "indian classical",
        ],
        "fear": ["ambient", "dark-ambient", "drone", "horror", "post-rock"],
        "disgust": ["grindcore", "hardcore"],
    }
    instrumental_genres = {
        "happy": [
            "instrumental-pop english",
            "instrumental-dance english",
            "instrumental-bollywood hits",
            "instrumental-hollywood hits",
            "instrumental songs",
            "instrumental-salsa spanish",
            "instrumental-cumbia spanish",
            "instrumental-chanson french",
            "instrumental-disco french",
            "instrumental-bollywood hindi",
            "instrumental-dhol hindi",
            "instrumental music",
        ],
        "sad": [
            "instrumental-piano",
            "instrumental-ambient",
            "instrumental ",
            "classical music",
            "silent",
            "instrumental-bolero",
            "instrumental-tango",
            "classical sad",
            "instrumental spanish classical",
            "instrumental-chanson",
            "instrumental-sad",
            "classical",
            "instrumental french classical",
            "instrumental-sad",
            "instrumental-flute",
            "instrumental classical",
            "instrumental indian classical",
        ],
        "relax": [
            "instrumental acoustic",
            "instrumental ambient",
            "instrumental chill",
            "instrumental downtempo",
            "instrumental new-age",
            "instrumental piano",
            "instrumental sleep",
            "instrumental trip-hop",
            "instrumental classical",
        ],
        "energetic": [
            "instrumental afrobeat",
            "instrumental anime",
            "instrumental breakbeat",
            "instrumental british",
            "instrumental dance",
            "instrumental detroit-techno",
            "instrumental j-dance",
            "instrumental j-idol",
            "instrumental j-pop",
            "instrumental j-rock",
        ],
        "angry": [
            "instrumental black-metal",
            "instrumental death-metal",
            "instrumental grindcore",
            "instrumental hardcore",
            "instrumental punk",
            "instrumental punk-rock",
        ],
        "neutral": [
            "instrumental alternative",
            "instrumental jazz",
            "instrumental singer-songwriter",
            "instrumental classical",
            "instrumental indian classical",
        ],
        "surprise": [
            "instrumental bossanova",
            "instrumental disco",
            "instrumental show-tunes",
        ],
        "fear": [
            "instrumental ambient",
            "instrumental dark-ambient",
            "instrumental drone",
            "instrumental horror",
            "instrumental post-rock",
        ],
        "disgust": ["instrumental grindcore", "instrumental hardcore"],
    }

    recently_played_songs = []
    limit = 50

    def __init__(self):
        self.audio_queue = []
        self.msg_placeholder = st.empty()
        self.sound = st.empty()
        self.sound1 = st.empty()
        self.current_playing_index = None
        self.select_box = st.empty()
        self.recommended_songs = {}
        self.recommended_songs_area = st.empty()
        self.current_audio_player = None
        self.currently_playing = None
        self.is_playing = False

    def recommend_and_store_music(self, emotion, mood):
        self.recommended_songs = {}

        if mood == "Generic":
            selected_genre = random.choice(self.genres.get(emotion.lower()))
        else:
            selected_genre = random.choice(
                self.instrumental_genres.get(emotion.lower())
            )

        track_uris = self.search_song_by_genre(selected_genre)
        if not track_uris:
            st.warning(f"No songs found for the {selected_genre} genre.")
            return None
        else:
            try:
                recommended_uris = []
                while len(recommended_uris) < 7:
                    random_track = random.choice(track_uris["tracks"]["items"])
                    if random_track:
                        uri = random_track["uri"]
                        (
                            audio_data,
                            track_name,
                            artists,
                            preview_url,
                            player_url,
                            duration,
                        ) = self.play_song(uri, [])
                        if player_url not in recommended_uris:
                            self.recommended_songs.setdefault(emotion, []).append(
                                player_url
                            )
                            recommended_uris.append(player_url)

                return recommended_uris
            except IndexError:
                pass

    def play_next_song(self):
        if self.audio_queue:
            (
                audio_data,
                track_name,
                artists,
                preview_url,
                player_url,
                duration,
            ) = self.audio_queue.pop(0)
            self.autoplay_audio(
                audio_data, track_name, artists, preview_url, player_url, duration
            )
            self.play_next_song()

    def search_song_by_genre(self, genre):
        query = f" genre:{genre}" if genre else "year:2010-2023"
        return sp.search(query, limit=self.limit, type="track")

    def play_song(self, track_uri, track_uris):
        player_url = f"https://open.spotify.com/embed/track/{track_uri.split(':')[2]}"
        track_info = sp.track(track_uri)
        duration = track_info["duration_ms"]
        uri = track_info["uri"]
        preview_url = track_info["preview_url"]

        if preview_url and player_url:
            return (
                "",
                track_info["name"],
                ", ".join(artist["name"] for artist in track_info["artists"]),
                preview_url,
                player_url,
                duration,
            )

        else:
            print("Song preview not available.")

            return b"", "", "", "", "", ""

    def autoplay_audio(
        self, data, track_name, artists, preview_url, player_url, duration
    ):
        recommended_songs_content = []

        for emotion, song_uris in self.recommended_songs.items():
            html_string1 = (
                f'<iframe src="{player_url}" width="300" height="80" frameborder="0" allowtransparency="true" '
                'allow="clipboard-write; encrypted-media; fullscreen"></iframe>'
            )
            content = html_string1
            content += "\n"
            content += f"\nRecommended songs for {emotion} emotion:\n"

            for song_uri in song_uris:
                iframe_html = f'<iframe src="{song_uri}" width="300" height="80" frameborder="0" allowtransparency="true" allow="clipboard-write; encrypted-media; fullscreen"></iframe>'
                content += iframe_html
            recommended_songs_content.append(content)

        combined_content = "<br>".join(recommended_songs_content)

        self.recommended_songs_area.markdown(combined_content, unsafe_allow_html=True)

        self.msg_placeholder.text("")
        self.sound.empty()
        self.sound1.empty()
        if duration:
            duration_sec = int(float(duration)) // 1000
        else:
            duration_sec = 29
        if preview_url:
            self.msg_placeholder.text(f"Now Playing: {track_name} by {artists}")
            html_string = f"""
                            <audio controls autoplay>
                              <source src={preview_url} type="audio/mp3">
                            </audio>
                            """
            self.sound.markdown(html_string, unsafe_allow_html=True)
            # self.sound1.markdown(
            #         f'<iframe src="{player_url}" width="300" height="80" frameborder="0" allowtransparency="true" '
            #         'allow="clipboard-write; encrypted-media; fullscreen"></iframe>',
            #         unsafe_allow_html=True,
            #     )

            time.sleep(duration_sec)
            self.msg_placeholder.text("")
            self.sound.empty()
            self.sound1.empty()

    def play_next_song1(self):
        if self.audio_queue:
            self.audio_queue.pop(0)
            if self.audio_queue:
                (
                    audio_data,
                    track_name,
                    artists,
                    preview_url,
                    player_url,
                ) = self.audio_queue[0]
                self.sound.stop()
                self.autoplay_audio(
                    audio_data, track_name, artists, preview_url, player_url
                )

    def play_previous_song(self):
        if len(self.audio_queue) >= 2:
            current_song_data = self.audio_queue.pop(0)
            self.audio_queue.insert(1, current_song_data)
            audio_data, track_name, artists, preview_url, player_url = self.audio_queue[
                0
            ]
            self.sound.stop()
            self.autoplay_audio(
                audio_data, track_name, artists, preview_url, player_url
            )

    def recommend_music(self, emotion, mood):
        if mood == "Generic":
            selected_genre = random.choice(self.genres.get(emotion.lower()))
        else:
            selected_genre = random.choice(
                self.instrumental_genres.get(emotion.lower())
            )

        track_uris = self.search_song_by_genre(selected_genre)
        if not track_uris:
            st.warning(f"No songs found for the {selected_genre} genre.")
            return None
        else:
            try:
                random_track = random.choice(track_uris["tracks"]["items"])
                if random_track:
                    uri = random_track["uri"]
                    return uri, track_uris
            except IndexError:
                pass

    def set_audio_queue(
        self, audio_data, track_name, artists, preview_url, player_url, duration
    ):
        self.audio_queue = [
            (audio_data, track_name, artists, preview_url, player_url, duration)
        ]
        self.current_playing_index = 0


class EmotionDetector:
    detected_emotion = ""

    def recv(self, frame):
        DeepFace.build_model("Emotion")
        img = frame.to_ndarray(format="bgr24")
        rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations_list = face_locations(rgb_frame)
        res = hol.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        predicted_emotion = ""
        for top, right, bottom, left in face_locations_list:
            face_roi = img[top:bottom, left:right]

            try:
                result = DeepFace.analyze(
                    face_roi, actions=["emotion"], enforce_detection=False
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
        drawing.draw_landmarks(img, res.face_landmarks, holistic.FACEMESH_TESSELATION)
        drawing.draw_landmarks(img, res.left_hand_landmarks, hands.HAND_CONNECTIONS)
        drawing.draw_landmarks(img, res.right_hand_landmarks, hands.HAND_CONNECTIONS)
        return av.VideoFrame.from_ndarray(img, format="bgr24")


def main():
    # def get_img_as_base64(file):
    #     with open(file, "rb") as f:
    #         data = f.read()
    #     return base64.b64encode(data).decode()
    #
    # img = get_img_as_base64("mario-la-pergola-uxV3wDMyccM-unsplash.jpg")
    # page_bg_img = f"""
    # <style>
    #
    # [data-testid="stSidebar"] > div:first-child {{
    # background-image: url("data:image/png;base64,{img}");
    # background-position: center;
    # background-repeat: repeat;
    # background-attachment: fixed;
    # }}
    #    </style>
    # """
    #
    # st.markdown(page_bg_img, unsafe_allow_html=True)

    st.title("Real Time Emotion Based Music Player Application 🎵😄😠🤮😨😀😐😔😮")
    activiteis = ["Home", "About"]
    choice = st.sidebar.selectbox("Select Activity", activiteis)
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

        ctx = webrtc_streamer(key="emotion", video_processor_factory=EmotionDetector)
        time.sleep(8)

        col1, col2 = st.columns([0.5, 1])
        with col1:
            next_btn = st.button("Next")
        with col2:
            prev_btn = st.button("Previous")

        music_player = EmotionMusicPlayer()
        # volume = st.slider("Volume", min_value=0, max_value=100, value=50)
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
