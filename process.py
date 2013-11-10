"""Voicemail to pollock

Usage:
	voicemail_to_pollock --s3-id=<id> --s3-secret=<secret>
"""
from docopt import docopt
from boto.s3.connection import S3Connection

import sys
import json
import hashlib
import random
import urllib

def main(s3_id, s3_secret):
	job = json.load(sys.stdin)

	hashed_user = hashlib.sha256(job['From']).hexdigest()
	key = hashlib.sha256(hashed_user + job['Url'] + str(random.randint(0, 1000))).hexdigest()

	(filename, headers) = urllib.urlretrieve(job['Url'])

	conn = S3Connection(s3_id, s3_secret)

	s3_bucket = conn.get_bucket('pollock-artcollectiveio')

	s3_key = s3_bucket.new_key(key)
	s3_key.set_contents_from_filename(filename)
	s3_key.set_acl('public-read')

	print s3_key.generate_url(expires_in=0, query_auth=False)


if __name__ == '__main__':
	arguments = docopt(__doc__, version='0.1.0')
	main(arguments['--s3-id'], arguments['--s3-secret'])

