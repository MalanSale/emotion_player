import base64
import io
import os
import random

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

os.environ["SPOTIPY_CLIENT_ID"] = "2ae751452b6a4bb385f129aa2849e30a"
os.environ["SPOTIPY_CLIENT_SECRET"] = "fcae1bab1b7d4cf7b3b537ca19ffcd6d"
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:8080"
scope = "user-library-read user-read-playback-state user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

msg_placeholder = st.empty()

holistic = mp.solutions.holistic
hands = mp.solutions.hands
hol = holistic.Holistic()
drawing = mp.solutions.drawing_utils


class EmotionMusicPlayer:
    genres = {
        "relax": ["acoustic", "ambient", "chill", "downtempo", "new-age", "piano", "sleep", "trip-hop"],
        "energetic": ["afrobeat", "anime", "breakbeat", "british", "dance", "detroit-techno", "j-dance", "j-idol",
                      "j-pop",
                      "j-rock", "k-pop", "party", "power-pop", "progressive-house", "road-trip", "rockabilly", "summer",
                      "swedish", "techno", "trance", "work-out"],
        "angry": ["black-metal", "death-metal", "grindcore", "hardcore", "punk", "punk-rock"],
        "neutral": ["alternative", "jazz", "singer-songwriter"],
        "surprise": ["bossanova", "disco", "show-tunes"],
        "happy": ["brazil", "cantopop", "comedy", "disco", "disney", "edm", "funk", "happy", "honky-tonk", "latin",
                  "reggaeton", "rock-n-roll", "salsa", "sertanejo", "spanish", "world-music"],
        "sad": ["blues", "emo", "folk", "grunge", "metal", "pop-film", "sad", "songwriter"],
        "fear": ["ambient", "dark-ambient", "drone", "horror", "post-rock"],
        "disgust": ["grindcore", "hardcore"]
    }
    recently_played_songs = []
    limit = 50

    def search_song_by_genre(self, genre):
        query = f" genre:{genre}" if genre else 'year:2010-2023'
        return sp.search(query, limit=self.limit, type="track")

    def select_random_song(self, track_uris):
        available_songs = [
            track_uri for track_uri in track_uris if track_uri not in self.recently_played_songs
        ]
        if available_songs:
            selected_song = random.choice(available_songs)
            self.recently_played_songs.append(selected_song)
            return selected_song
        st.warning("All songs in this genre have been played. Refresh the page to start again.")

    def play_song(self, track_uri, track_uris):
        track_info = sp.track(track_uri)

        preview_url = track_info["preview_url"]

        if preview_url:
            response = requests.get(preview_url)
            if response.status_code == 200:
                st.subheader("Now Playing:")
                st.write(f"Track: {track_info['name']}")
                st.write(f"Artist: {', '.join(artist['name'] for artist in track_info['artists'])}")

                audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")

                audio_data = io.BytesIO()
                audio.export(audio_data, format="mp3")
                return audio_data.getvalue()
            else:
                print("Error downloading audio.")
        else:
            print("Song preview not available.")
            random_track_uri = self.select_random_song(track_uris)
            self.play_song(random_track_uri, track_uris)
            return

    def autoplay_audio(self, data):
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio id='audio_player' controls autoplay="true" start="0">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

    def recommend_music(self, emotion):
        selected_genre = random.choice(self.genres.get(emotion.lower()))
        track_uris = self.search_song_by_genre(selected_genre)
        if not track_uris:
            msg_placeholder.text(
                f"No songs found for the {selected_genre} genre."
            )
            msg_placeholder.text("")
        else:
            # random_track_uri = self.select_random_song(track_uris)
            random_track = random.choice(track_uris["tracks"]["items"])

            if random_track:
                uri = random_track['uri']
                # audio_data = self.play_song(random_track_uri, track_uris)
                # self.autoplay_audio(audio_data)
                player_url = f"https://open.spotify.com/embed/track/{uri.split(':')[2]}"

                # Use the Streamlit `IFrame` to embed the player
                st.markdown(
                    f'<iframe src="{player_url}" width="300" height="80" frameborder="0" allowtransparency="true" '
                    'allow="clipboard-write; encrypted-media; fullscreen"></iframe>',
                    unsafe_allow_html=True,
                )


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
                predicted_emotion = max(emotion_predictions, key=emotion_predictions.get)
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
    # Face Analysis Application #
    st.title("Real Time Emotion Based Music Player Application 😠🤮😨😀😐😔😮")
    activiteis = ["Home", "About"]
    choice = st.sidebar.selectbox("Select Activity", activiteis)

    # Homepage.
    if choice == "Home":
        html_temp_home1 = """<div style="background-color:#FC4C02;padding:0.5px">
                             <h4 style="color:white;text-align:center;">
                            Start Your Real Time Face Emotion Detection.
                             </h4>
                             </div>
                             </br>"""

        st.markdown(html_temp_home1, unsafe_allow_html=True)
        st.subheader('''
                * Get ready with all the emotions you can express. 
                ''')
        st.write("1. Click Start to open your camera and give permission for prediction")
        st.write("2. This will predict your emotion.")
        st.write("3. When you done, click Recommend Music button.")
        st.write("4. Music will be played based on your mood.")
        st.write("5. Change the track by clicking the Recommend Music button again.")

        ctx = webrtc_streamer(key="emotion", video_processor_factory=EmotionDetector)

        music_btn = st.button("Recommend Track")
        music_player = EmotionMusicPlayer()

        if music_btn and getattr(ctx, "video_processor", None):
            detected_emotion = ctx.video_processor.detected_emotion
            if detected_emotion:
                with st.spinner("Please wait while we recommend music for you..."):
                    music_player.recommend_music(detected_emotion)

    # About.
    elif choice == "About":
        st.subheader("About this app")
        html_temp_about1 = """<div style="background-color:#36454F;padding:30px">
                                    <h4 style="color:white;">
                                     This app predicts facial emotion in real time.
                                     It uses a pre-trained model to predict the emotion.
                                     Based on the mood music will be played.
                                    </h4>
                                    </div>
                                    </br>
                                    """
        st.markdown(html_temp_about1, unsafe_allow_html=True)


# Streamlit Customisation
st.markdown(""" <style>
header {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
