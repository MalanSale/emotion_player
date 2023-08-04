import spotipy
from spotipy.oauth2 import SpotifyOAuth
scope = 'user-read-private playlist-read-private playlist-modify-public'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='a20d0f0a5d7b4de1a9584431931fe9b3',
    client_secret='d483d27de7504438952a119835c4b8bd', redirect_uri='http://127.0.0.1:3000',scope=scope))

# user = sp.album(album_id='5XrmpQEvCaqW8jRA1pwtwD?',market='IN')
playlists = sp.user_playlists('spotify')
# print(playlists)
while playlists:
    for i, playlist in enumerate(playlists['items']):
        print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None