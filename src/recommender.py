from InstagramAPI import InstagramAPI
from datetime import datetime, timedelta
from url_decoder import InstagramPost
from utils import get_hashtags_from_str

import time
import warnings
import json

class SimpleRecommender(object):
    def __init__(self, user_id, username, password):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.api = None
        self.followings_dict = None
        self.followings_posts_dict = None
        self._setup()
        
    def _setup(self):
        self.api = InstagramAPI(self.username, self.password)
        self.api.login()
        self.api.getUsernameInfo(self.user_id)
        
        following = []
        next_max_id = True
        
        while next_max_id:
            # first iteration hack
            if next_max_id is True:
                next_max_id = ''

            _ = self.api.getUserFollowings(self.user_id, maxid=next_max_id)
            following.extend(self.api.LastJson.get('users', []))
            next_max_id = self.api.LastJson.get('next_max_id', '')

        # pk is actually the user_id
        self.followings_dict = { 
            f['pk']: f
            for f in following
        }

    def _fetch_followings_posts(self, lookback_ndays=10):
        followings_posts_dict = {}

        for i, (user_id, user) in enumerate(self.followings_dict.items()):
            print("Fetching %s/%s (user_id = %s)" % (i+1, len(self.followings_dict), user_id))
            posts = []

            try:
                posts = self.get_recent_posts(user_id, lookback_ndays)
            except Exception as error:
                print("Fetch failed: %s" % str(error))

            if len(posts) > 0:
                posts = {post['pk']: post for post in posts}
                followings_posts_dict[user_id] = posts 

        self.followings_posts_dict = followings_posts_dict

    def get_recent_posts(self, user_id, lookback_ndays=10):
        unixtime = int(time.mktime((datetime.now().date() - timedelta(days=lookback_ndays)).timetuple()))
        return self.api.getTotalUserFeed(user_id, unixtime)

    def suggest(self, lookback_ndays=1):
        if self.followings_posts_dict is None:
            self._fetch_followings_posts(lookback_ndays)
        
        hashtag_count_dict = {}
        for (user_id, posts_dict) in self.followings_posts_dict.items():
            for (post_id, post_dict) in posts_dict.items():
                caption_exist = (post_dict is not None) and \
                                ('caption' in post_dict) and \
                                (post_dict['caption'] is not None) and \
                                ('text' in post_dict['caption'])
                if caption_exist: 
                    hashtags = get_hashtags_from_str(post_dict['caption']['text'])
                    for hashtag in hashtags:
                        hashtag_count_dict[hashtag] = hashtag_count_dict.get(hashtag, 0) + 1

        return hashtag_count_dict