import random
import os
import streamlit as st
from pydub import AudioSegment
import requests
import io
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cv2
from deepface import DeepFace
import time
import webbrowser
import pandas as pd
import numpy as np
from deepface import DeepFace
from face_recognition.api import face_locations
from streamlit_player import st_player

os.environ["SPOTIPY_CLIENT_ID"] = "2ae751452b6a4bb385f129aa2849e30a"
os.environ["SPOTIPY_CLIENT_SECRET"] = "fcae1bab1b7d4cf7b3b537ca19ffcd6d"
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:8080"
scope = "user-library-read user-read-playback-state user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

hindi_mood_genre_mapping = {
    "happy": ["bollywood hits"],
    "sad": ["indian classical"],
    "energetic": ["dance", "indian pop","Electronic"],
    "relax": ["indian classical", "ambient"],
    "neutral":["instrumental","ambient"],
    "surprise":["Electronic Dance Music","Experimental"],
    "fear":["Dark Ambient","Horror Soundtracks"],
    "angry":["Metal","Rap"],
    "disgust":["Grindcore","Noise"],
}

english_mood_genre_mapping = {
    "happy": ["pop", "rock"],
    "sad": ["chill", "indie"],
    "energetic": ["dance", "edm"],
    "relax": ["jazz", "ambient"],
    "neutral":["instrumental","ambient"],
    "surprise":["Electronic Dance Music","Experimental"],
    "fear":["Dark Ambient","Horror Soundtracks"],
    "angry":["Metal","Rap"],
    "disgust":["Grindcore","Noise"],
}

marathi_mood_genre_mapping = {
    "happy": ["marathi pop"],
    "sad": ["marathi classical"],
    "energetic": ["marathi dance"],
    "relax": ["marathi instrumental"],
    "neutral":["instrumental","ambient"],
    "surprise":["Electronic Dance Music","Experimental"],
    "fear":["Dark Ambient","Horror Soundtracks"],
    "angry":["Metal","Rap"],
    "disgust":["Grindcore","Noise"],
}
recently_played_songs = []
emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

def get_dominant_emotion(emotion_predictions):
    return max(emotion_predictions, key=emotion_predictions.get)

def select_random_genre(mood, language):
    mood = mood.lower()
    if language.lower() == "hindi" and mood in hindi_mood_genre_mapping:
        return random.choice(hindi_mood_genre_mapping[mood])
    elif language.lower() == "english" and mood in english_mood_genre_mapping:
        return random.choice(english_mood_genre_mapping[mood])
    elif language.lower() == "marathi" and mood in marathi_mood_genre_mapping:
        return random.choice(marathi_mood_genre_mapping[mood])
    else:
        return None

def search_song_by_language_and_genre(language, genre):
    query = f" genre:{genre}"
    results = sp.search(query, limit=50, type="track")
    if results["tracks"]["items"]:
        track_uris = [item["uri"] for item in results["tracks"]["items"]]
        return track_uris
    else:
        return None

def select_random_song(track_uris):
    available_songs = [track_uri for track_uri in track_uris if track_uri not in recently_played_songs]
    if not available_songs:
        return None
    return random.choice(available_songs)

def play_song(track_uri):
    track_info = sp.track(track_uri)
    preview_url = track_info["preview_url"]

    if preview_url:
        response = requests.get(preview_url)
        if response.status_code == 200:
            audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")

            audio_data = io.BytesIO()
            audio.export(audio_data, format="wav")
            return audio_data.getvalue()
        else:
            print("Error downloading audio.")
    else:
        print("Song preview not available.")

def main():

    st.title("Emotion Based Music Recommender")
    image_placeholder = st.empty()
    image_path = "mario-la-pergola-uxV3wDMyccM-unsplash.jpg"
    emotion_detection_button = st.button("Emotion Detection")
    if not emotion_detection_button:
        image_placeholder.image(image_path, use_column_width=True, output_format="JPEG", width=100)

    # st.image(image_path,use_column_width=True, output_format="JPEG", width=100)
    moods = ["happy", "sad", "energetic", "relax", "neutral", "surprise", "fear", "angry", "disgust"]
    languages = ["Hindi", "English", "Marathi"]

    if emotion_detection_button:
        most_predicted_emotion = mood_detect()
        # st.write("Emotion Detected:", most_predicted_emotion)
        lang = 'English'
        with st.sidebar:
            most_predicted_emotion_index = moods.index(most_predicted_emotion)
            # user_mood = st.selectbox("Select your mood:", moods, index=most_predicted_emotion_index)
            default_lang_index = languages.index(lang)
            user_language = st.selectbox("Select your preferred language:", languages, index=default_lang_index)
        selected_genre = select_random_genre(most_predicted_emotion, lang.lower())

    else:
        # Additional feature: Stop the camera stream when switching to "Choose Mood"
        with st.sidebar:
            user_mood = st.selectbox("Select your mood:", moods, index=0)
            user_language = st.selectbox("Select your preferred language:", languages, index=0)
        selected_genre = select_random_genre(user_mood, user_language.lower())

    if not selected_genre:
        st.error("Invalid mood and language combination.")
        return
    track_uris = search_song_by_language_and_genre(user_language.lower(), selected_genre)
    if not track_uris:
        st.error(f"No songs found for the {selected_genre} genre in {user_language} language.")
        return

    st.success(f"Playing a random {selected_genre} song in {user_language} language to match your mood.")
    random_track_uri = select_random_song(track_uris)
    if random_track_uri:
        recently_played_songs.append(random_track_uri)
        if len(recently_played_songs) > len(random_track_uri):
            recently_played_songs.pop(0)
        audio_data = play_song(random_track_uri)
        st.audio(audio_data, format="audio/wav", start_time=0)
    else:
        st.warning("No new songs available. Try again later.")

def mood_detect():

    DeepFace.build_model("Emotion")
    cap = cv2.VideoCapture(0)
    video_placeholder = st.empty()
    detection_duration = 8
    start_time = time.time()
    while time.time() - start_time < detection_duration:

        ret, frame = cap.read()
        if not ret:
            st.write("Error capturing the frame from the webcam.")
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations_list = face_locations(rgb_frame)

        for (top, right, bottom, left) in face_locations_list:
            face_roi = frame[top:bottom, left:right]

            try:
                result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
                emotion_predictions = result[0]['emotion']
                predicted_emotion = get_dominant_emotion(emotion_predictions)
            except ValueError as e:
                predicted_emotion = 'Unknown'

            text = f"Mood: {predicted_emotion}"
            cv2.putText(frame, text, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        video_placeholder.image(frame, channels="BGR", use_column_width=True)
    cap.release()
    cv2.destroyAllWindows()
    st.write("Detected Mood:", predicted_emotion)
    most_predicted_emotion = predicted_emotion
    return most_predicted_emotion

if __name__ == "__main__":
    main()



