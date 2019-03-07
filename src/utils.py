import re

def get_hashtags_from_str(string):
	return [tag.strip("#") for tag in string.split() if tag.startswith("#")]