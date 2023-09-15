import random
import time

import streamlit as st


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

    def __init__(self, sp):
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
        self.sp = sp

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
        return self.sp.search(query, limit=self.limit, type="track")

    def play_song(self, track_uri, track_uris):
        player_url = f"https://open.spotify.com/embed/track/{track_uri.split(':')[2]}"
        track_info = self.sp.track(track_uri)
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
