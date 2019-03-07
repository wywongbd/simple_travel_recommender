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

        self._login()
        self._fetch_followings()
        
    def _login(self):
        self.api = InstagramAPI(self.username, self.password)
        self.api.login()
        self.api.getUsernameInfo(self.user_id)
        
    def _fetch_followings(self):
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

    def _fetch_followings_posts(self, lookback_ndays=10, silent=True):
        followings_posts_dict = {}

        for i, (user_id, user) in enumerate(self.followings_dict.items()):
            if not silent:
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

    def _get_hashtags_from_post(self, post_dict):
        caption_exist = (post_dict is not None) and \
                        ('caption' in post_dict) and \
                        (post_dict['caption'] is not None) and \
                        ('text' in post_dict['caption'])
        if caption_exist: 
            return get_hashtags_from_str(post_dict['caption']['text'])
        else:
            return []

    def _get_posts_from_hashtag(self, hashtag):
        self.api.getHashtagFeed(hashtag)
        return self.api.LastJson['items']

    def _get_related_tags(self, hashtag, min_coocurrence_probablity=0.01):
        posts_ls = self._get_posts_from_hashtag(hashtag)
        tags = set()
        count_dict = {}
        N = 0

        for post in posts_ls:
            hashtag_ls = self._get_hashtags_from_post(post)
            for tag in hashtag_ls:
                count_dict[tag] = count_dict.get(tag, 0) + 1
                N += 1

        for i, (tag, count) in enumerate(count_dict.items()):
            if count / N >= min_coocurrence_probablity:
                tags.add(tag)

        return tags

    def _get_cluster_from_hashtag_feed(self, hashtag, min_coocurrence_probablity=0.01):
        # returns a set of tags strongly related with the given hashtag
        tags = self._get_related_tags(hashtag, min_coocurrence_probablity)
        tags_ls = [self._get_related_tags(tag, min_coocurrence_probablity) for tag in tags]
        tags_ls = [tags_set.intersection(tags) for tags_set in tags_ls]
        return set.union(*tags_ls)

    def get_recent_posts(self, user_id, lookback_ndays=10):
        unixtime = int(time.mktime((datetime.now().date() - timedelta(days=lookback_ndays)).timetuple()))
        return self.api.getTotalUserFeed(user_id, unixtime)

    def suggest(self, locations_ls, lookback_ndays=1, min_coocurrence_probablity=(0.01, 0.01)):
        if self.followings_posts_dict is None:
            self._fetch_followings_posts(lookback_ndays)

        travel_cluster = self._get_cluster_from_hashtag_feed('travel', min_coocurrence_probablity[0])
        print(travel_cluster)
        location_cluster_dict = {}
        for location in locations_ls:
            cluster = self._get_cluster_from_hashtag_feed(location, min_coocurrence_probablity[1])
            location_cluster_dict[location] = cluster - travel_cluster
            print(location_cluster_dict[location])

        location_count_dict = {}
        location_posts_dict = {}
        for (user_id, posts_dict) in self.followings_posts_dict.items():
            for (post_id, post_dict) in posts_dict.items():
                    hashtags = set(self._get_hashtags_from_post(post_dict))
                    for location, cluster in location_cluster_dict.items():
                        if len(hashtags.intersection(travel_cluster)) > 0 and len(hashtags.intersection(cluster)) > 0:
                            location_count_dict[location] = location_count_dict.get(location, 0) + 1

                            if location not in location_posts_dict:
                                location_posts_dict[location] = []    
                            location_posts_dict[location].append(post_dict)

        return location_count_dict

    def suggest_with_clusters(self, travel_cluster, location_cluster_dict, lookback_ndays, n_intersections=1):
        if self.followings_posts_dict is None:
            self._fetch_followings_posts(lookback_ndays)

        travel_cluster_tags = travel_cluster.tags
        location_cluster_tags = {}
        for location in location_cluster_dict:
            location_cluster_tags[location] = location_cluster_dict[location].tags - travel_cluster_tags 

        location_count_dict = {}
        location_posts_dict = {}
        for (user_id, posts_dict) in self.followings_posts_dict.items():
            for (post_id, post_dict) in posts_dict.items():
                    hashtags = set(self._get_hashtags_from_post(post_dict))
                    for location, cluster in location_cluster_tags.items():
                        if len(hashtags.intersection(travel_cluster_tags)) >= n_intersections and \
                            len(hashtags.intersection(cluster)) >= n_intersections:
                            location_count_dict[location] = location_count_dict.get(location, 0) + 1

                            if location not in location_posts_dict:
                                location_posts_dict[location] = []    
                            location_posts_dict[location].append(post_dict)

        return location_count_dict, location_posts_dict