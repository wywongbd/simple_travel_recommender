from InstagramAPI import InstagramAPI
from datetime import datetime
import time

class SimpleRecommender(object):
    def __init__(self, user_id, username, password):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.api = None
        self.followings_dict = None
        
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

        self.followings_dict = { 
            f['pk']: f
            for f in following
        }

    def suggest(self, days=1):
        pass