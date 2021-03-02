#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['spa', 'lfa', 'friends', 'cache_dir' ]


cache_dir = 'spotifriends_cache'

# Spotify API authentication
# https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app
spa = {
	'c_id' : '##################################',
	'c_secret' : '##################################',
	'r_uri' : 'https://spotifriends.local'
	}

# last.fm API authentication
# https://www.last.fm/api/account/create
lfa = {
	'a_key' : '##################################',
	's_secret' : '##################################'
	}

# last.fm usernames
friends = [	{
			'username': 'rj',
			'track_limit' : 20,
			'update_interval' : 300
			}
		]