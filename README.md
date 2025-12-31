# Spotify Local Downloader

This is a simple tool to download high-quality songs locally using metadata from Spotify (Anna's Archive) and audio from Tidal.

## ⚠️ Requirements
1. **Python 3**: You need Python installed on your computer.
   - [Download Python Here](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
2. **Spotify Database**: You need the `.sqlite3` database file from Anna's Archive.
   - **Link**: [Anna's Archive](https://annas-archive.org)
   - **Search Term**: Search for `Anna's Archive Spotify 2025 Metadata` (Look for `spotify_clean.sqlite3.zst`).
   - **Download**: It is usually a large download (Torrent). You will need the `.sqlite3` file from inside the archive.

## 🚀 How to Run

### Step 1: Install Dependencies
Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:
```bash
pip install requests
```

### Step 2: Run the Script
1. Open the folder containing these files.
2. **On Windows**: Double-click the `download_songs.py` file.
   - *If that doesn't work*: Right-click inside the folder > "Open in Terminal" > Type `python download_songs.py` and hit Enter.
3. **On Mac/Linux**: Open Terminal, navigate to the folder, and run:
   ```bash
   python3 download_songs.py
   ```

### Step 3: Follow the Instructions
The script will ask you for 4 things:

1.  **Database File**: Drag and drop your `.sqlite3` file into the terminal window when asked.
2.  **Download Folder**: Where you want the music to go (Press Enter to create a 'downloads' folder here).
3.  **Genres**: Type the genres you want (e.g., `pop, rock`) or press Enter for the default (Bollywood/Filmi).
4.  **Limit**: How many songs to download (e.g., `100`).

## ❓ FAQ

**Q: It says "Rate Limit" or "429"?**
A: This means Tidal is slowing us down. The script will automatically pause for 30 seconds and resume. Just let it run.

**Q: Some songs are skipped?**
A: Not every song on Spotify is available on Tidal, or sometimes the names don't match exactly. This is normal.

**Q: Where is the music?**
A: Check the folder you selected in Step 2 (default is a `downloads` folder next to the script).
