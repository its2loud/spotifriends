#!/usr/bin/env python
# -*- coding: utf-8 -*-

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

from spotifriends_cfg import *
import requests
import logging
import json
import os
import threading
import time
import difflib


def get_cache_filename(username = False):
	SPATH = os.path.dirname(os.path.realpath(__file__))+"/"
	if not username:
		return SPATH + cache_dir + '/_app.json'
	return SPATH + cache_dir + '/' + username + '.json'


def load_cache(field, username = False):
	cache_file = get_cache_filename(username)
	try:
		with open(cache_file) as j:
			cache = json.load(j)
			j.close()
			if field in cache:
				return cache[field]
			else: return False
	except IOError:
			return False


def save_cache(field, data, username = False):
	cache_file = get_cache_filename(username)
	try:
		with open(cache_file) as j:
			cache = json.load(j)
			j.close()
	except IOError:
			if not username:
				logging.debug('No cache, creating new.')
			else:		
				logging.debug('No cache for user ' + username + ', creating new.')
			cache = {}
	cache[field] = data
	if not os.path.exists(cache_dir):
		os.makedirs(cache_dir)
	with open(cache_file, 'w') as j:
		json.dump(cache, j, indent=2)
	j.close()


def query_new_spotify_playlist_id(playlist_name):
	scope = "playlist-modify-private"
	sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=spa['c_id'], client_secret=spa['c_secret'], redirect_uri=spa['r_uri']))
	user_id = sp.me()['id']
	rf = sp.user_playlist_create(user_id, playlist_name, False)	
	return rf['id']


def get_spotify_playlist_id(username):
	playlist_id = load_cache('playlist_id', username)
	if not playlist_id:
		logging.debug('No Spotify playlist for user ' + username +  ', creating new.')
		playlist_id = query_new_spotify_playlist_id(username + "'s recent tracks")
		save_cache('playlist_id', playlist_id, username)
	return playlist_id


def query_spotify_playlist_tracks(playlist_id):
	scope = "playlist-modify-private"
	sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=spa['c_id'], client_secret=spa['c_secret'], redirect_uri=spa['r_uri']))
	rf = sp.playlist_tracks(playlist_id)
	if 'items' in rf:
		return rf['items']
	else:
		return False


def query_lastfm_recent_tracks(username, limit = 100):
	lf_api_root = 'http://ws.audioscrobbler.com/2.0/'
	lf_api_request = lf_api_root+'?method=user.getrecenttracks&user='+username+'&api_key='+lfa['a_key']+'&format=json&limit=' + str(limit)
	response = requests.get(lf_api_request)
	rf = response.json()
	if 'recenttracks' in rf:
		return rf['recenttracks']['track']
	else:
		logging.error('Could not receive recent tracks for user "' + username +'" (' + lf_api_request + ')')


def query_spotify_track_id(track, artist, album = False, advanced = True, market = 'DE'):
		sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=spa['c_id'], client_secret=spa['c_secret']))
		if advanced:
			q = '"' + track + '" AND artist:"' + artist + '"'
			if album != False: q += ' AND album:"' + album + '"'
		else:
			q = '"' + artist + '" - "' + track + '"'
		logging.debug('Searching for: %s' % q)

		rs = sp.search(q=q, type='track', limit=1, market=market)
		if 'tracks' in rs and rs['tracks']['total'] > 0:
			return rs['tracks']['items'][0]['id']
		else:
			return False


def get_spotify_track_id(track, artist, album, mbid = False, user = False):
	cached_ids = load_cache('spotify_ids')
	if not cached_ids: cached_ids = {}
	if mbid in cached_ids:
		return cached_ids[mbid]
	cached_uts = False
	cached_now = False
	if user != False and 'username' in user and 'uts' in user:
		if not user['uts']: 					# = nowplaying
			cached_now = load_cache('nowplaying', user['username'])
			if not cached_now: cached_now = {}
			elif (len(mbid) > 0 and mbid == cached_now['mbid']) or (track == cached_now['track'] and artist == cached_now['artist'] and album == cached_now['album']):
				return cached_now['id']
		else:
			cached_uts = load_cache('uts', user['username'])
			if not cached_uts: cached_uts = {}
			elif user['uts'] in cached_uts:
				return cached_uts[user['uts']]
	else:
		logging.debug('D')
	logging.debug('No cached Spotify ID found for "%s" - "%s" (mbid = "%s"), searching.' % (track, artist, mbid))

	result = query_spotify_track_id(track, artist, album)
	if not result:
		result = query_spotify_track_id(track, artist)
	if not result:
		result = query_spotify_track_id(track, artist, advanced = False)

	if result != False:
		if mbid != False and len(mbid) > 0: 	# Saving to cached MBIDs.
			cached_ids[mbid] = result
			save_cache('spotify_ids', cached_ids)
		elif cached_uts != False: 				# Saving to user's cached UTS.
			cached_uts[user['uts']] = result
			save_cache('uts', cached_uts, user['username'])
		elif cached_now != False:				# Saving as user's now playing.
			logging.info('Friend "' + user['username'] + '": ' + 'Now playing: "' + artist + '" - "' + track + '"')
			cached_now = {
				'track' : track,
				'artist' : artist,
				'album' : album,
				'mbid' : mbid,
				'id' : result
			}
			save_cache('nowplaying', cached_now, user['username'])
	else:
		logging.debug('No Spotify ID found for "%s" - "%s" (mbid = "%s")' % (track, artist, mbid))

	return result


def del_spotify_playlist_items(playlist_id, range_start, range_length = 1):
	tracks = query_spotify_playlist_tracks(playlist_id)
	rem_track_ids = []
	for n in range(range_start, range_start+range_length):
		rem_track_ids.append({"uri": tracks[n]['track']['id'], "positions": [n]})
	scope = "playlist-modify-private"
	sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=spa['c_id'], client_secret=spa['c_secret'], redirect_uri=spa['r_uri']))
	sp.playlist_remove_specific_occurrences_of_items(playlist_id, rem_track_ids)


def push_spotify_playlist_items(playlist_id, track_ids, index = -1, reverse = False):
	if not len(track_ids) > 0: return
	if reverse: track_ids = reversed(track_ids)
	scope = "playlist-modify-private"
	sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=spa['c_id'], client_secret=spa['c_secret'], redirect_uri=spa['r_uri']))
	if index < 0:
		rf = sp.playlist_add_items(playlist_id, track_ids)
	else:
		rf = sp.playlist_add_items(playlist_id, track_ids, index)
	if 'snapshot_id' in rf:
		return True
	else:
		logging.error('Could not add tracks (' +  str(len(track_ids)) + ') to playlist "' + playlist_id + '"')
		return False


def replace_spotify_playlist_items(playlist_id, track_ids, range_start, range_length = False):
	if not range_length: range_length = len(track_ids)
	del_spotify_playlist_items(playlist_id, range_start, range_length)
	push_spotify_playlist_items(playlist_id, track_ids, range_start)


def get_lfm_track_info(track):
	result = {}
	result['mbid'] = track['mbid']
	result['track'] = track['name']
	result['artist'] = track['artist']['#text']
	result['album'] = track['album']['#text']
	if '@attr' in track and track['@attr']['nowplaying']:
		result['uts'] = False
	else:
		result['uts'] = track['date']['uts']
	return result


def sync_playlist(username, limit = 100):
	try:
		playlist_id = get_spotify_playlist_id(username)
	except:
		logging.error('Could not open playlist for user "%s"' % username)

	recent_tracks = query_lastfm_recent_tracks(username, limit)
	if not recent_tracks or not len(recent_tracks) > 0:
		logging.error('Friend "%s": Could not retrieve recent tracks from last.fm' % username)
		return
	playlist = query_spotify_playlist_tracks(playlist_id)
	if playlist == False:
		logging.error('Friend "%s": Could not retrieve playlist from Spotify.' % username)
		return
	playlist_old = []
	for item in playlist:
		playlist_old.append(item['track']['id'])

	playlist_new = []
	for track in recent_tracks:
		info = get_lfm_track_info(track)
		track_id = get_spotify_track_id(info['track'], info['artist'], info['album'], info['mbid'], {'username' : username, 'uts' : info['uts']})
		if track_id != False:
			playlist_new.insert(0, track_id)

	if playlist_new == playlist_old:
		logging.debug('Friend "%s": Playlist is up to date.' % username)
		return

	matcher = difflib.SequenceMatcher(None, playlist_old, playlist_new)
	for cmd, i1, i2, j1, j2 in reversed(matcher.get_opcodes()):

	    if cmd == 'delete':
	    	logging.debug('Friend "%s": Deleting items [%d:%d]' % (username, i1, i2))
	        del_spotify_playlist_items(playlist_id, i1, i2-i1)
	    elif cmd == 'insert':
	    	logging.debug('Friend "%s": Inserting %d items at %d' % (username, j2-j1, i1))
	        push_spotify_playlist_items(playlist_id, playlist_new[j1:j2], i1)
	    elif cmd == 'replace':
	    	logging.debug('Friend "%s": Replacing items [%d:%d]' % (username, i1, i2))
	        replace_spotify_playlist_items(playlist_id, playlist_new[j1:j2], i1, i2-i1)


def user_loop(username, limit = 100, interval = 90):
	while True:
		sync_playlist(username, limit)
		time.sleep(interval)


def main():
	threads = {}
	for user in friends:
		logging.debug('Starting thread for user "' + user['username'] + '".')
		threads[user['username']] = threading.Thread(target = user_loop, args = (user['username'], user['track_limit'], user['update_interval']))
		threads[user['username']].daemon = True
		threads[user['username']].start()


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
	logging.getLogger("requests").setLevel(logging.WARNING)
	logging.getLogger("urllib3").setLevel(logging.WARNING)
	logging.getLogger("spotipy").setLevel(logging.WARNING)

	try:
		main()
		while True: time.sleep(100)
	except KeyboardInterrupt:
		print('Received keyboard interrupt, stopping threads.')
