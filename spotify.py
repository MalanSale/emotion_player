import spotipy
import streamlit as st
from spotipy.oauth2 import SpotifyOAuth
import os

SPOTIPY_CLIENT_ID = "2ae751452b6a4bb385f129aa2849e30a"
SPOTIPY_CLIENT_SECRET = "fcae1bab1b7d4cf7b3b537ca19ffcd6d"
SPOTIPY_REDIRECT_URI = 'http://localhost:8080'
os.environ["SPOTIPY_CLIENT_ID"] = SPOTIPY_CLIENT_ID
os.environ["SPOTIPY_CLIENT_SECRET"] = SPOTIPY_CLIENT_SECRET
os.environ["SPOTIPY_REDIRECT_URI"] = SPOTIPY_REDIRECT_URI
scope = "user-library-read user-read-playback-state user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
print(sp)
query = f" genre:pop"
track_uris=sp.search(query, limit=1, type="track")
print(track_uris)
st.write(track_uris)
