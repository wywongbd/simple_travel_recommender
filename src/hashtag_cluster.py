from utils import count_occurences, save_dict_ls, load_dict_ls
from url_decoder import InstagramPost
import sys
import json

sys.path.append('../instagram_crawler')
from crawler import get_posts_by_hashtag
sys.path.pop()

class Cluster(object):
	def __init__(self, hashtag, min_coocurrence_probablity=0.01, sample_size=100, filename=None):
		if filename is None:
			self.hashtag = hashtag
			self.min_coocurrence_probablity = min_coocurrence_probablity
			self.sample_size = sample_size
			self.tags = None
			self._setup()
		else:
			# if filename provided, load cluster from provided path
			dict_ls = load_dict_ls(filename)
			d = eval(dict_ls[0])
			self.hashtag = d['hashtag']
			self.min_coocurrence_probablity = d['min_coocurrence_probablity']
			self.sample_size = d['sample_size']
			self.tags = d['tags']

	def _setup(self):
		# this function constructs the cluster
		self.tags = self._get_related_tags(self.hashtag)
		tags_ls = [self._get_related_tags(tag) for tag in self.tags]
		tags_ls = [tags_set.intersection(self.tags) for tags_set in tags_ls]
		self.tags = set.union(*tags_ls)

	def _get_related_tags(self, hashtag):
		# this function collects all tags that co-occur frequently with the given hashtag
		posts_ls = get_posts_by_hashtag(hashtag, self.sample_size)
		tags = set()
		count_dict = {}
		N = 0

		for post in posts_ls:
			post_obj = InstagramPost(post['key'])
			for tag in post_obj.hashtag_ls:
				count_dict[tag] = count_dict.get(tag, 0) + 1
				N += 1

		# select only tags that occur frequently enough 
		for i, (tag, count) in enumerate(count_dict.items()):
			if count / N >= self.min_coocurrence_probablity:
				tags.add(tag)

		return tags

	def save_cluster(self, filename):
		save_dict_ls([str(vars(self))], filename)

	def contains(self, hashtag):
		return hashtag in self.tags 