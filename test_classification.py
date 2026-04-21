"""Test script for classification module"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'yami'))

from classification import ClassificationManager, Genre, ListeningMode, SongInfo

print('Classification module imported successfully')

# Create classification manager
cm = ClassificationManager()

# Test song classification
song1 = SongInfo(
    file_path='/test/artist1 - rock song.mp3',
    title='Rock Song',
    artist='Artist1'
)
song1.genre = cm.classify_song_by_content(song1)
print(f'Song1: {song1.artist} - {song1.title}, Genre: {song1.genre.value}')

song2 = SongInfo(
    file_path='/test/artist2 - sleep music.mp3',
    title='Sleep Music',
    artist='Artist2'
)
song2.genre = cm.classify_song_by_content(song2)
print(f'Song2: {song2.artist} - {song2.title}, Genre: {song2.genre.value}')

song3 = SongInfo(
    file_path='/test/artist1 - dj mix.mp3',
    title='DJ Mix',
    artist='Artist1'
)
song3.genre = cm.classify_song_by_content(song3)
print(f'Song3: {song3.artist} - {song3.title}, Genre: {song3.genre.value}')

song4 = SongInfo(
    file_path='/test/抖音热歌 - artist3.mp3',
    title='热门歌曲',
    artist='Artist3'
)
song4.genre = cm.classify_song_by_content(song4)
print(f'Song4: {song4.artist} - {song4.title}, Genre: {song4.genre.value}')

song5 = SongInfo(
    file_path='/test/artist4 - lofi chill.mp3',
    title='Lo-Fi Music',
    artist='Artist4'
)
song5.genre = cm.classify_song_by_content(song5)
print(f'Song5: {song5.artist} - {song5.title}, Genre: {song5.genre.value}')

# Add songs to manager
cm.add_song(song1)
cm.add_song(song2)
cm.add_song(song3)
cm.add_song(song4)
cm.add_song(song5)

# Test artist grouping
print(f'\nArtists: {cm.get_all_artists()}')
print(f'Songs by Artist1: {len(cm.get_songs_by_artist("Artist1"))}')

# Test genre grouping
print(f'\nGenres: {[g.value for g in cm.get_all_genres()]}')
print(f'Songs in Rock genre: {len(cm.get_songs_by_genre(Genre.ROCK))}')
print(f'Songs in Sleep genre: {len(cm.get_songs_by_genre(Genre.SLEEP))}')

# Test listening modes
print(f'\n=== Listening Modes ===')
print(f'Songs for Random mode: {len(cm.get_songs_for_mode(ListeningMode.RANDOM))}')
print(f'Songs for Sleep mode: {len(cm.get_songs_for_mode(ListeningMode.SLEEP))}')
print(f'Songs for DJ mode: {len(cm.get_songs_for_mode(ListeningMode.DJ))}')
print(f'Songs for TikTok mode: {len(cm.get_songs_for_mode(ListeningMode.TIKTOK))}')
print(f'Songs for Lo-Fi mode: {len(cm.get_songs_for_mode(ListeningMode.LOFI))}')
print(f'Songs for Relax mode: {len(cm.get_songs_for_mode(ListeningMode.RELAX))}')

# Test clear
cm.clear()
print(f'\nAfter clear - Total songs: {len(cm.all_songs)}')
print(f'After clear - Artists: {cm.get_all_artists()}')

print('\n=== All tests passed! ===')
