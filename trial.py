import base64
import io
import os
import random
import time
import av
import cv2
import mediapipe as mp
import requests
import spotipy
import streamlit as st
from deepface import DeepFace
from face_recognition.api import face_locations
from pydub import AudioSegment
from spotipy.oauth2 import SpotifyOAuth
from streamlit_webrtc import webrtc_streamer
from IPython.display import Audio, display
from pydub.playback import play

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
        self.current_track_index = 0
        self.current_audio_data = None
        self.current_track_name = ""
        self.current_artists = ""
        self.is_playing = False
        self.current_audio_duration = 0

    def enqueue_audio(self, audio_data, track_name, artists):
        self.audio_queue.append((audio_data, track_name, artists))

    def play_next_song(self):
        if self.audio_queue:
            audio_data, track_name, artists = self.audio_queue.pop(0)
            self.autoplay_audio(audio_data, track_name, artists)
            self.play_next_song()

    def search_song_by_genre(self, genre):
        query = f" genre:{genre}" if genre else "year:2010-2023"
        return sp.search(query, limit=self.limit, type="track")

    def select_random_song(self, track_uris):
        available_songs = [
            track_uri
            for track_uri in track_uris
            if track_uri not in self.recently_played_songs
        ]
        if available_songs:
            selected_song = random.choice(available_songs)
            self.recently_played_songs.append(selected_song)
            return selected_song
        st.warning(
            "All songs in this genre have been played. Refresh the page to start again."
        )

    def play_song(self, track_uri, track_uris):
        track_info = sp.track(track_uri)
        preview_url = track_info["preview_url"]
        print("------------------", preview_url)
        if preview_url:
            for _ in range(5):
                response = requests.get(preview_url)
                if response.status_code == 200:
                    audio = AudioSegment.from_file(
                        io.BytesIO(response.content), format="mp3"
                    )
                    audio_data = io.BytesIO()
                    audio.export(audio_data, format="mp3")

                    return (
                        audio_data.getvalue(),
                        track_info["name"],
                        ", ".join(artist["name"] for artist in track_info["artists"]),
                    )
                print("Error downloading audio.")
                time.sleep(1)

        else:
            print("Song preview not available.")
            return b"", "", ""

    def autoplay_audio(self, data, track_name, artists):
        msg_placeholder = st.empty()
        if data:
            audio = AudioSegment.from_file(io.BytesIO(data), format="mp3")
            msg_placeholder.text(f"Now Playing: {track_name} by {artists}")
            play(audio)
            msg_placeholder.text("")

    def recommend_music(self, emotion, mood):
        if mood == "Generic":
            selected_genre = random.choice(self.genres.get(emotion.lower()))
        else:
            selected_genre = random.choice(
                self.instrumental_genres.get(emotion.lower())
            )

        track_uris = self.search_song_by_genre(selected_genre)

        if not track_uris:
            msg_placeholder.text(f"No songs found for the {selected_genre} genre.")
            msg_placeholder.text("")
        else:
            try:
                random_track = random.choice(track_uris["tracks"]["items"])
                if random_track:
                    uri = random_track["uri"]
                    return uri

            except IndexError:
                pass


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
    st.title("Real Time Emotion Based Music Player Application 😠🤮😨😀😐😔😮")
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
        st.write("3. When you done, click Recommend Music button.")
        st.write("4. Music will be played based on your mood.")
        st.write("5. Change the track by clicking the Next button.")

        ctx = webrtc_streamer(key="emotion", video_processor_factory=EmotionDetector)
        time.sleep(8)
        music_player = EmotionMusicPlayer()

        try:
            while True:
                if getattr(ctx, "video_processor", None):
                    detected_emotion = ctx.video_processor.detected_emotion
                    if detected_emotion:
                        selected_track_uri = music_player.recommend_music(
                            detected_emotion, generic_mood
                        )
                        if selected_track_uri:
                            audio_data, track_name, artists = music_player.play_song(
                                selected_track_uri, []
                            )
                            music_player.enqueue_audio(audio_data, track_name, artists)
                            if len(music_player.audio_queue) == 1:
                                music_player.play_next_song()

        except AttributeError:
            pass


# Streamlit Customisation
st.markdown(
    """ <style>
header {visibility: hidden;}
footer {visibility: hidden;}
</style> """,
    unsafe_allow_html=True,
)

if __name__ == "__main__":
    main()
