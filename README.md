# spotifriends
Python script to sync last.fm user's recent tracks to a Spotify playlist

## Requirements

- spotipy
  https://spotipy.readthedocs.io/en/2.16.1/

  ```bash
  pip install spotipy --upgrade
  ```
- Spotify API account  
  https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app
  
- last.fm API account  
  https://www.last.fm/api/account/create

## Configuration
  ```bash
  nano spotifriends_cfg.py
  ```
- Set up credentials for the Spotify and last.fm API
- Set up a list of usernames you want to sync their recently played tracks from, along with a limit and update interval

## Run
  ```bash
  python spotifriends.py
  ```
The first time you run the script, spotipy will open a browser window for granting access via Spotify and prompt you to copy and paste the resulting callback URL. Spotipy generates a hidden file *.cache* to store the neccessary tokens.

The script frequently requests the user's recently played tracks from last.fm and tries to find a matching track on Spotify. These Spotify IDs are cached either associated with the music brainz ID, or if there is none, associated with the timestamp provided in the user's recent tracklist. This information will be stored in the automatically created subdirectory *spotifriends_cache*. That way only new tracks should be looked up to build a list of Spotify track IDs, which is then synced to an automatically created playlist *username's recent tracks*.
  
## Notes

Unfortunately, Spotify doesn't seem to continue playing songs added via the API after playback has been started. Therefore, it is not possible, to listen to the same song as a friend at the same time.
