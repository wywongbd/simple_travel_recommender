from datetime import datetime
import time
import re
import json

def get_unixtime():
	return time.time()

def get_dt_from_unixtime(unixtime):
	return datetime.fromtimestamp(unixtime)

def get_hashtags_from_str(string):
	return [tag.strip("#") for tag in string.split() if tag.startswith("#")]

def save_dict_ls(dict_ls, path):
	with open(path, 'w') as fout:
		json.dump(dict_ls, fout)

def read_dict_ls(path):
	with open(path, "r") as file:
		return eval(file.readline())