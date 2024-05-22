from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random
import requests
import hid
import struct
import threading

# Variable to store the timestamp of the last API call
last_api_call_time = 0

app = Flask(__name__)
socketio = SocketIO(app)

# Constants for the device (replace with actual values)
VENDOR_ID = 0x239a  # Replace with your device's Vendor ID
PRODUCT_ID = 0x80cc  # Replace with your device's Product ID

# Spotify API credentials
SPOTIPY_CLIENT_ID = 'CLIENT_ID'
SPOTIPY_CLIENT_SECRET = 'CLIENT_SECRET'
SPOTIPY_REDIRECT_URI = 'URL'

# Define the scope
scope = "user-read-recently-played user-read-playback-state user-modify-playback-state user-top-read streaming"

# Initialize Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=scope))

# State tracking for buttons and axes
last_button_states = [0] * 9
last_axis_states = {'X': 127, 'Y': 127, 'Z': 127, 'Rx': 127, 'Ry': 127, 'Rz': 127}

# Tracking if an axis trigger has been sent
axis_trigger_sent = {'X': False, 'Y': False, 'Z': False, 'Rx': False, 'Ry': False, 'Rz': False}

# Timestamp for the last recommendation sent
last_recommendation_time = 0

available_genres = ["acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime", "black-metal", "bluegrass", "blues", "bossanova", "brazil", "breakbeat", "british", "cantopop", "chicago-house", "children", "chill", "classical", "club", "comedy", "country", "dance", "dancehall", "death-metal", "deep-house", "detroit-techno", "disco", "disney", "drum-and-bass", "dub", "dubstep", "edm", "electro", "electronic", "emo", "folk", "forro", "french", "funk", "garage", "german", "gospel", "goth", "grindcore", "groove", "grunge", "guitar", "happy", "hard-rock", "hardcore", "hardstyle", "heavy-metal", "hip-hop", "holidays", "honky-tonk", "house", "idm", "indian", "indie", "indie-pop", "industrial", "iranian", "j-dance", "j-idol", "j-pop", "j-rock", "jazz", "k-pop", "kids", "latin", "latino", "malay", "mandopop", "metal", "metal-misc", "metalcore", "minimal-techno", "movies", "mpb", "new-age", "new-release", "opera", "pagode", "party", "philippines-opm", "piano", "pop", "pop-film", "post-dubstep", "power-pop", "progressive-house", "psych-rock", "punk", "punk-rock", "r-n-b", "rainy-day", "reggae", "reggaeton", "road-trip", "rock", "rock-n-roll", "rockabilly", "romance", "sad", "salsa", "samba", "sertanejo", "show-tunes", "singer-songwriter", "ska", "sleep", "songwriter", "soul", "soundtracks", "spanish", "study", "summer", "swedish", "synth-pop", "tango", "techno", "trance", "trip-hop", "turkish", "work-out", "world-music"]

# Feature mapping for axes
feature_mapping = {
    'X': 'danceability',
    'Y': 'energy',
    'Z': 'acousticness',
    'Rx': 'duration_ms',
    'Ry': 'valence',
    'Rz': 'popularity'
}

@app.route('/state')
def get_state():
    return jsonify({
        'buttons': last_button_states,
        'axes': last_axis_states
    })

def read_device(vendor_id, product_id):
    # Open the device
    try:
        device = hid.Device(vendor_id, product_id)
        print(f"Device opened: {device.manufacturer} {device.product}")

        # Read and parse reports
        while True:
            # This will block until it reads a report
            data = device.read(9)  # Read 9 bytes; as per your descriptor
            if data:
                parse_hid_report(data)

    except IOError as e:
        print(f"Could not open device: {e}")
    finally:
        if device:
            device.close()

# Function to handle API calls with rate limiting
def make_spotify_api_call(func, *args, max_retries=10, initial_delay=1, backoff_factor=2, **kwargs):
    global last_api_call_time
    retries = 0
    delay = initial_delay
    while retries < max_retries:
        elapsed_time = time.time() - last_api_call_time
        if elapsed_time < 1:
            time.sleep(1 - elapsed_time)
        try:
            result = func(*args, **kwargs)
            last_api_call_time = time.time()
            return result
        except (spotipy.exceptions.SpotifyException, requests.exceptions.RequestException) as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get('Retry-After', delay))
                print(f"Rate limited. Retrying in {retry_after} seconds...")
                time.sleep(retry_after)
                delay *= backoff_factor
                retries += 1
            else:
                raise
    raise Exception("Max retries reached. Unable to make the API call.")

def get_top_tracks():
    top_tracks = make_spotify_api_call(sp.current_user_top_tracks, limit=50, time_range='short_term')['items']

    # Sort the tracks by year in ascending order
    top_tracks.sort(key=lambda track: track['album']['release_date'][:4], reverse=True)

    unique_artist_tracks = []
    seen_artists = set()
    for track in top_tracks:
        artist = track['artists'][0]['id']
        if artist not in seen_artists:
            unique_artist_tracks.append(track)
            seen_artists.add(artist)
            if len(unique_artist_tracks) >= 8:
                break
    unique_artist_tracks = list(reversed(unique_artist_tracks[:8]))
    return unique_artist_tracks

top_tracks = get_top_tracks()
  
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/current_song')
def current_song():
    playback_state = make_spotify_api_call(sp.current_playback)
    if playback_state and playback_state['is_playing'] and playback_state['item']:
        seed_track = playback_state['item']
    else:
        recently_played = sp.current_user_recently_played(limit=1)['items']
        if recently_played:
            seed_track = recently_played[0]['track']
        else:
            return jsonify({"error": "No currently playing or recently played tracks found."}), 404
    
    seed_track_id = seed_track['id']
    seed_track_features = make_spotify_api_call(sp.audio_features, seed_track_id)[0]

    # Scale duration to 0-100 range based on 2 to 10 minutes
    scaled_duration = max(0, min(100, (seed_track['duration_ms'] - 120000) / (600000 - 120000) * 100))

    track_data = {
        'track_name': seed_track['name'],
        'artist_name': seed_track['artists'][0]['name'],
        'album_name': seed_track['album']['name'],
        'album_art': seed_track['album']['images'][0]['url'],
        'features': {
            'danceability': seed_track_features['danceability'] * 100,
            'energy': seed_track_features['energy'] * 100,
            'acousticness': seed_track_features['acousticness'] * 100,
            'duration_ms': scaled_duration,  # Scale to 0-100 range
            'valence': seed_track_features['valence'] * 100,
            'popularity': seed_track['popularity']  # Added popularity here
        }
    }

    return jsonify(track_data)

@app.route('/recommendations', methods=['POST'])
def recommendations():
    global last_recommendation_time
    data = request.json
    feature_adjustment = data.get('feature_adjustment')
    feature_name = data.get('feature_name')
    seed_track_id = data.get('seed_track_id')

    recommendation_params = {
        'limit': 20,
    }

    target_audio_features = {}

    if seed_track_id:
    
        # Get the user's currently playing track
        playback_state = make_spotify_api_call(sp.current_playback)
        if playback_state and playback_state['is_playing'] and playback_state['item']:
            seed_track = playback_state['item']
        else:
            recently_played = sp.current_user_recently_played(limit=1)['items']
            if recently_played:
                seed_track = recently_played[0]['track']
            else:
                return jsonify({"error": "No currently playing or recently played tracks found."}), 404
        
        current_track_id = seed_track['id']
        seed_track_features = make_spotify_api_call(sp.audio_features, current_track_id)[0]

        recommendation_params['seed_tracks'] = [seed_track_id]
        target_audio_features['target_danceability'] = seed_track_features['danceability']
        target_audio_features['target_energy'] = seed_track_features['energy']
        target_audio_features['target_acousticness'] = seed_track_features['acousticness']
        target_audio_features['target_duration_ms'] = seed_track_features['duration_ms']
        target_audio_features['target_valence'] = seed_track_features['valence']
        target_audio_features['target_popularity'] = seed_track['popularity']

    else:

        # Get the user's currently playing track
        playback_state = make_spotify_api_call(sp.current_playback)
        if playback_state and playback_state['is_playing'] and playback_state['item']:
            seed_track = playback_state['item']
        else:
            recently_played = sp.current_user_recently_played(limit=1)['items']
            if recently_played:
                seed_track = recently_played[0]['track']
            else:
                return jsonify({"error": "No currently playing or recently played tracks found."}), 404
        
        seed_track_id = seed_track['id']
        seed_track_features = make_spotify_api_call(sp.audio_features, seed_track_id)[0]
    
            
        recommendation_params['seed_tracks'] = [seed_track_id]

        if feature_name:
            adjustment_value = 0.1 if feature_adjustment > 0 else -0.1
            popularity_adjustment_value = 5 if feature_adjustment > 0 else -5
            duration_adjustment_value = 90000 if feature_adjustment > 0 else -90000

            if feature_name == 'danceability':
                if feature_adjustment > 0:
                    target_audio_features['min_danceability'] = min(seed_track_features['danceability'] + adjustment_value, 1.0)
                else:
                    target_audio_features['max_danceability'] = max(seed_track_features['danceability'] + adjustment_value, 0.0)
            elif feature_name == 'energy':
                if feature_adjustment < 0:
                    target_audio_features['min_energy'] = min(seed_track_features['energy'] + adjustment_value, 1.0)
                else:
                    target_audio_features['max_energy'] = max(seed_track_features['energy'] + adjustment_value, 0.0)
            elif feature_name == 'acousticness':
                if feature_adjustment < 0:
                    target_audio_features['min_acousticness'] = min(seed_track_features['acousticness'] + adjustment_value, 1.0)
                else:
                    target_audio_features['max_acousticness'] = max(seed_track_features['acousticness'] + adjustment_value, 0.0)
            elif feature_name == 'duration_ms':
                if feature_adjustment > 0:
                    target_audio_features['min_duration_ms'] = min(seed_track['duration_ms'] + duration_adjustment_value, 1800000)
                else:
                    target_audio_features['max_duration_ms'] = max(seed_track['duration_ms'] + duration_adjustment_value, 120000)
            elif feature_name == 'valence':
                if feature_adjustment > 0:
                    target_audio_features['min_valence'] = min(seed_track_features['valence'] + adjustment_value, 1.0)
                else:
                    target_audio_features['max_valence'] = max(seed_track_features['valence'] + adjustment_value, 0.0)
            elif feature_name == 'popularity':
                if feature_adjustment > 0:
                    target_audio_features['min_popularity'] = min(seed_track['popularity'] + popularity_adjustment_value, 100)
                else:
                    target_audio_features['max_popularity'] = max(seed_track['popularity'] + popularity_adjustment_value, 0)

            recommendation_params.update(target_audio_features)

    try:
        print(f"Recommendation params: {recommendation_params}")
        recommendations = sp.recommendations(**recommendation_params)['tracks']
        if not recommendations:
            return jsonify({"error": "No recommendations found."}), 404
    
        random_song = random.choice(recommendations)
    
        track_uri = f"spotify:track:{random_song['id']}"
        make_spotify_api_call(sp.start_playback, uris=[track_uri])
    
        last_recommendation_time = time.time()  # Update the timestamp for the last recommendation
    
        # Emit an event to notify the front-end
        socketio.emit('new_recommendation', {'feature_name': feature_name})
    
        return jsonify({"success": True})
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify exception: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Exception in /recommendations: {e}")
        return jsonify({"error": str(e)}), 500

def parse_hid_report(data):
    global last_button_states, last_axis_states, axis_trigger_sent, last_recommendation_time

    # Ignore inputs if within cooldown period
    if time.time() - last_recommendation_time < 2:
        return

    report_id = data[0]
    if report_id == 4:
        buttons_byte0 = data[1]
        buttons_byte1 = data[2]

        button_states = [(buttons_byte0 >> i) & 1 for i in range(8)]
        button9 = (buttons_byte1 & 0x01)
        button_states.append(button9)

        x, y, z, rx, ry, rz = struct.unpack('<6B', bytes(data[3:9]))

        # Handle Button 9 press for play/pause toggle
        if button9 and not last_button_states[8]:  # Button 9 is the last button in the list
            toggle_playback()

    # Handle Buttons 1-8 for track recommendations

        button_labels = [
            'Top Track 1', 'Top Track 2', 'Top Track 3', 'Top Track 4',
            'Top Track 5', 'Top Track 6', 'Top Track 7', 'Top Track', 'Play/Pause'
        ]

        for i, state in enumerate(button_states):
            if state and not last_button_states[i]:
                print(button_labels[i])
                if i < 8:
                    seed_track = top_tracks[i] if i < len(top_tracks) else None
                    trigger_track_recommendation(seed_track, i+1)
                    print(f"Track {i+1}: {seed_track['name']} by {seed_track['artists'][0]['name']}")                
            last_button_states[i] = state

        axis_labels = ['X', 'Y', 'Z', 'Rx', 'Ry', 'Rz']
        axis_values = {'X': x, 'Y': y, 'Z': z, 'Rx': rx, 'Ry': ry, 'Rz': rz}
        
        for label, value in axis_values.items():
            if value == 0 and last_axis_states[label] != 0:
                if not axis_trigger_sent[label]:
                    print(f"{label}: Min")
                    trigger_spotify_adjustment(label, -1)
                    axis_trigger_sent[label] = True
            elif value == 254 and last_axis_states[label] != 254:
                if not axis_trigger_sent[label]:
                    print(f"{label}: Max")
                    trigger_spotify_adjustment(label, 1)
                    axis_trigger_sent[label] = True
            elif value == 127:
                axis_trigger_sent[label] = False  # Reset the trigger flag when returning to midpoint

            last_axis_states[label] = value

def toggle_playback():
    try:
        playback_state = make_spotify_api_call(sp.current_playback)
        if playback_state and playback_state['is_playing']:
            make_spotify_api_call(sp.pause_playback)
            print("Playback paused")
        else:
            make_spotify_api_call(sp.start_playback)
            print("Playback started")
    except Exception as e:
        print(f"Error toggling playback: {e}")

def trigger_spotify_adjustment(axis, adjustment):
    global last_recommendation_time
    feature_name = feature_mapping[axis]
    data = {
        'feature_name': feature_name,
        'feature_adjustment': adjustment,
    }
    response = requests.post('http://127.0.0.1:5000/recommendations', json=data)
    if response.status_code == 200:
        print(f"Triggered Spotify adjustment for {feature_name} with adjustment {adjustment}")
        last_recommendation_time = time.time()  # Update the timestamp for the last recommendation
        
        # Emit an event to notify the front-end
        socketio.emit('new_recommendation', {'feature_name': feature_name})
        
        print("emitting feature")
        print(feature_name)
    else:
        print(f"Failed to trigger Spotify adjustment: {response.json().get('error')}")

def trigger_track_recommendation(seed_track, button_id):
    data = {
        'seed_track_id': seed_track['id'],
        'feature_adjustment': 1,
        'feature_name': 'button' + str(button_id)
    }
    try:
        response = requests.post('http://127.0.0.1:5000/recommendations', json=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content.decode('utf-8')}")
        if response.status_code == 200:
            print(f"Triggered Spotify recommendation for track {seed_track['name']}")
            last_recommendation_time = time.time()  # Update the timestamp for the last recommendation
        else:
            print(f"Failed to trigger Spotify recommendation: {response.json().get('error')}")
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")

if __name__ == '__main__':
    # Start HID reading in a separate thread
    hid_thread = threading.Thread(target=read_device, args=(VENDOR_ID, PRODUCT_ID))
    hid_thread.start()

    # Start Flask server
    app.run(debug=True, use_reloader=False)
