from bs4 import BeautifulSoup
from datetime import datetime

import warnings
import requests
import json
import re

class InstagramPost(object):
	def __init__(self, post_url):
		self.post_url = post_url
		self.request = requests.get(self.post_url) 
		self.soup = BeautifulSoup(self.request.text, "html.parser")
		self.upload_date = self._get_post_upload_date()
		self.hashtag_ls = self._get_hashtags()

	def _get_post_upload_date(self):
		try:
			scripts = self.soup.find_all('script')
			for script in scripts:
				if 'uploadDate' in script.text:
					date_str = json.loads(str(script.get_text()))['uploadDate']
					date_str = re.sub('[^0-9]',' ', date_str)
					dt_obj = datetime.strptime(date_str, '%Y %m %d %H %M %S')
					return dt_obj

		except Exception as error:
			warnings.warn('Error while finding upload date in given post_url (%s)! \n %s' % (self.post_url, str(error)))

		return None

	def _get_hashtags(self):
		try:
			hashtags = self.soup.find_all('meta', property='instapp:hashtags')
			hashtags = [e.get('content') for e in hashtags]
			return hashtags

		except Exception as error:
			warnings.warn('Error while finding hashtags in given post_url (%s)! \n %s' % (self.post_url, str(error)))

		return []


