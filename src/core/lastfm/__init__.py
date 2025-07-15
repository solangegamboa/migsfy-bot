"""
Last.fm integration module for migsfy-bot.
Provides functionality to interact with Last.fm API and download music by tags.
"""

from .tag_downloader import get_top_tracks_by_tag, download_tracks_by_tag, get_lastfm_network
