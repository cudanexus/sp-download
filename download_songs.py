import sqlite3
import requests
import json
import base64
import random
import os
import time
import csv
import sys

# --- Configuration & Defaults ---
DEFAULT_TIDAL_INSTANCES = [
    "https://triton.squid.wtf",
    "https://api.tidalhifi.com", 
    "https://tidal.sharkr.dev"
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_user_input():
    clear_screen()
    print("==============================================")
    print("   Spotify Downloader (via Tidal & Anna's Archive)")
    print("==============================================")
    print("Please answer the following questions to start:\n")

    # 1. Database Path
    while True:
        db_path = input("1. Drag and drop your Spotify .sqlite3 database file here (or type path): ").strip()
        # Remove quotes if drag/drop added them
        db_path = db_path.replace("'", "").replace('"', "")
        if os.path.isfile(db_path):
            break
        print(f"   [Error] File not found: {db_path}. Please try again.\n")

    # 2. Download Directory
    while True:
        music_dir = input("\n2. Where do you want to save the music? (Press Enter for 'downloads' folder): ").strip()
        if not music_dir:
            music_dir = os.path.join(os.getcwd(), 'downloads')
        
        try:
            os.makedirs(music_dir, exist_ok=True)
            break
        except Exception as e:
            print(f"   [Error] Could not create directory: {e}. Try a different path.")

    # 3. Genres
    print("\n3. What genres do you want to download?")
    print("   (e.g., 'pop, rock, jazz' or leave empty for 'bollywood, filmi')")
    genre_input = input("   Genres: ").strip()
    if not genre_input:
        genres = ['bollywood', 'filmi', 'desi pop']
    else:
        genres = [g.strip().lower() for g in genre_input.split(',')]

    # 4. Limit
    while True:
        limit_input = input("\n4. How many songs to download? (Type a number, e.g., 100): ").strip()
        if limit_input.isdigit():
            limit = int(limit_input)
            break
        print("   [Error] Please enter a valid number.")

    return db_path, music_dir, genres, limit

# --- Logging Setup ---
LOG_FILE = 'download_log.txt'

def log(msg, verbose=True):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    if verbose:
        print(msg) 
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(formatted_msg + "\n")

# --- CSV Mapping Setup ---
CSV_FILE = 'track_mapping.csv'

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Spotify ID', 'Track Name', 'Artist', 'Popularity', 'Status', 'Tidal URL'])

def log_csv(spotify_id, name, artist, popularity, status, url=''):
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([spotify_id, name, artist, popularity, status, url])
    except Exception as e:
        log(f"  [CSV Error] {e}")

# --- API Handling ---
TIDAL_CACHE = {}

def get_tidal_url_for_track(track_name, artist_name, spotify_id):
    if spotify_id in TIDAL_CACHE:
        return TIDAL_CACHE[spotify_id]
        
    query = f"{track_name} {artist_name}"
    instances = DEFAULT_TIDAL_INSTANCES.copy()
    random.shuffle(instances)
    
    for base_url in instances:
        try:
            base_url = base_url.rstrip('/')
            # 1. Search
            search_url = f"{base_url}/search/?s={requests.utils.quote(query)}"
            resp = requests.get(search_url, timeout=5)
            
            if resp.status_code == 429:
                log(f"  [429] Instance {base_url} is rate limiting. Cooling down...", verbose=False)
                continue 
            
            if resp.status_code != 200: continue
            data = resp.json()
            
            items = []
            if isinstance(data, list): items = data
            elif isinstance(data, dict):
                if 'items' in data: items = data['items']
                elif 'tracks' in data and 'items' in data['tracks']: items = data['tracks']['items']
                elif 'data' in data:
                    d = data['data']
                    if 'items' in d: items = d['items']
                    elif 'tracks' in d and 'items' in d['tracks']: items = d['tracks']['items']
            
            if not items: continue
            
            tidal_id = None
            for item in items:
                t = item.get('item', item)
                if t.get('id'):
                    tidal_id = t.get('id')
                    break
            
            if not tidal_id: continue
            
            # 2. Get Stream (HIGH Quality AAC)
            track_url = f"{base_url}/track/?id={tidal_id}&quality=HIGH"
            resp = requests.get(track_url, timeout=5)
            if resp.status_code != 200: continue
            track_data = resp.json()
            
            manifest = None
            if 'manifest' in track_data: manifest = track_data['manifest']
            elif 'data' in track_data:
                d = track_data['data']
                if 'manifest' in d: manifest = d['manifest']
            elif isinstance(track_data, list) and len(track_data) > 0 and 'manifest' in track_data[0]:
                manifest = track_data[0]['manifest']

            if not manifest: continue
            
            try:
                decoded = base64.b64decode(manifest).decode('utf-8')
                stream_json = json.loads(decoded)
                if 'urls' in stream_json and stream_json['urls']:
                    stream_url = stream_json['urls'][0]
                    TIDAL_CACHE[spotify_id] = stream_url
                    return stream_url
            except:
                continue
                
        except Exception:
            continue
            
    return None

def main():
    try:
        db_path, music_dir, genres, max_limit = get_user_input()
        
        init_csv()
        print("\n\nConnecting to database...")
        conn = sqlite3.connect(db_path)
        
        print("Counting matching tracks (this might take a moment)...")
        
        placeholders = ','.join(['?'] * len(genres))
        
        # 1. Count
        count_query = f"""
            SELECT count(DISTINCT t.id)
            FROM tracks t
            JOIN track_artists ta ON t.rowid = ta.track_rowid
            JOIN artists a ON ta.artist_rowid = a.rowid
            JOIN artist_genres ag ON a.rowid = ag.artist_rowid
            WHERE ag.genre IN ({placeholders})
        """
        try:
            total_count = conn.execute(count_query, genres).fetchone()[0]
            print(f"Total tracks found for genres {genres}: {total_count}")
        except sqlite3.OperationalError as e:
            print(f"\n[Database Error] Could not query database. Is this the correct Spotify URL database?\nError: {e}")
            return
        
        # 2. Query
        limit_clause = f"LIMIT {max_limit}" if max_limit > 0 else ""
        print(f"Querying top {max_limit} tracks by popularity...")

        query = f"""
            SELECT DISTINCT t.name, t.id, t.popularity, 
                   (SELECT name FROM artists WHERE rowid = ta.artist_rowid) as artist_name
            FROM tracks t
            JOIN track_artists ta ON t.rowid = ta.track_rowid
            JOIN artists a ON ta.artist_rowid = a.rowid
            JOIN artist_genres ag ON a.rowid = ag.artist_rowid
            WHERE ag.genre IN ({placeholders})
            ORDER BY t.popularity DESC
            {limit_clause}
        """
        
        cursor = conn.execute(query, genres)
        tracks = cursor.fetchall()
        conn.close()
        
        print(f"Found {len(tracks)} tracks to process.\n")
        log("--- Download Session Started ---")
        
        seen_ids = set()

        for i, (name, spotify_id, popularity, artist_name) in enumerate(tracks, 1):
            if spotify_id in seen_ids: continue
            seen_ids.add(spotify_id)

            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in ' .-_()']).strip()
            filename = f"{safe_name} - {spotify_id}.mp3"
            filepath = os.path.join(music_dir, filename)
            
            if os.path.exists(filepath):
                print(f"[{i}/{len(tracks)}] [Skip] {name} (File exists)")
                continue
                
            print(f"[{i}/{len(tracks)}] Processing: {name} - {artist_name} (Pop: {popularity})")

            stream_url = get_tidal_url_for_track(name, artist_name, spotify_id)
            
            if stream_url:
                print("         Downloading...", end='\r')
                try:
                    r = requests.get(stream_url, stream=True)
                    if r.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                        log(f"  [Done] {name}")
                        log_csv(spotify_id, name, artist_name, popularity, "Downloaded", stream_url)
                    elif r.status_code == 429:
                        print("         [429] Rate Limit. Pausing 30s...")
                        time.sleep(30)
                    else:
                        print(f"         [Fail] HTTP {r.status_code}")
                except Exception as e:
                    print(f"         [Error] {e}")
            else:
                print("         [Skip] Not found on Tidal")
                log_csv(spotify_id, name, artist_name, popularity, "Tidal Not Found", "")
                
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\nStopped by user.")
    except Exception as e:
        print(f"\n\nAn unexpected error occurred: {e}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
