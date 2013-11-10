"""Voicemail to pollock

Usage:
	voicemail_to_pollock --s3-id=<id> --s3-secret=<secret> --twilio-account=<account> --twilio-token=<token>
"""
from docopt import docopt
from boto.s3.connection import S3Connection
from twilio.rest import TwilioRestClient

import sys
import json
import hashlib
import random
import urllib
import httplib2
import subprocess
import time

def upload_file(s3_bucket, key, filename):
	s3_key = s3_bucket.new_key(key)
	s3_key.set_contents_from_filename(filename)
	s3_key.set_acl('public-read')
	
	return s3_key.generate_url(expires_in=0, query_auth=False)

def store_voicemail(s3_bucket, hashed_user, url):
	key = hashlib.sha256(hashed_user + url + str(random.randint(0, 1000))).hexdigest()

	(filename, headers) = urllib.urlretrieve(url)

	httplib2.Http().request(url, method='DELETE')

	return (filename, upload_file(s3_bucket, key, filename))

def create_pollock(s3_bucket, voicemail_filename):
	key = hashlib.sha256(voicemail_filename + str(time.time()) + str(random.randint(0, 1000))).hexdigest()
	filename = '/tmp/pollock-%s.png' % key

	subprocess.call('pollock -n 1000 -o %s' % filename, shell=True)

	return upload_file(s3_bucket, key, filename)

def add_to_gallery(hashed_user, voicemail_url, pollock_url):
	gallery_entry = {
		'url': pollock_url,
		'inspiration_url': voicemail_url
	}

	(response, content) = httplib2.Http().request(
		'http://api.pollock.artcollective.io/%s' % hashed_user,
		method='POST',
		body=json.dumps(gallery_entry)
	)

	json_response = json.loads(content)

	return 'http://pollock.artcollective.io/' + json_response['pid']

def send_to_muse(client, from_phonenumber, gallery_url):
	client.messages.create(
		to=from_phonenumber,
		from_='+441290211866',
		body='Your painting is ready, please go to ' + gallery_url
	)
	pass

if __name__ == '__main__':
	arguments = docopt(__doc__, version='0.1.0')

	s3_conn = S3Connection(arguments['--s3-id'], arguments['--s3-secret'])
	s3_bucket = s3_conn.get_bucket('pollock-artcollectiveio')

	twilio_client = TwilioRestClient(arguments['--twilio-account'], arguments['--twilio-token'])

	job = json.load(sys.stdin)
	hashed_user = hashlib.sha256(job['From']).hexdigest()

	(voicemail_filename, voicemail_url) = store_voicemail(s3_bucket, hashed_user, job['Url'])
	pollock_url = create_pollock(s3_bucket, voicemail_filename)

	gallery_url = add_to_gallery(hashed_user, voicemail_url, pollock_url)

	send_to_muse(twilio_client, job['From'], gallery_url)

