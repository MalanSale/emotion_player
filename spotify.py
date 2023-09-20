import spotipy
import streamlit as st
import os

SPOTIPY_CLIENT_ID = "2ae751452b6a4bb385f129aa2849e30a"
SPOTIPY_CLIENT_SECRET = "fcae1bab1b7d4cf7b3b537ca19ffcd6d"
os.environ["SPOTIPY_CLIENT_ID"] = SPOTIPY_CLIENT_ID
os.environ["SPOTIPY_CLIENT_SECRET"] = SPOTIPY_CLIENT_SECRET

# Use the Spotify API client credentials flow (no user authentication required)
sp = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyClientCredentials())

query = "genre:pop"
track_uris = sp.search(query, limit=1, type="track")
print(track_uris)
st.write(track_uris)
