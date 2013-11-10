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
import httplib

def store_voicemail(s3_bucket, hashed_user, url):
	key = hashlib.sha256(hashed_user + url + str(random.randint(0, 1000))).hexdigest()

	(filename, headers) = urllib.urlretrieve(url)

	s3_key = s3_bucket.new_key(key)
	s3_key.set_contents_from_filename(filename)
	s3_key.set_acl('public-read')

	return (filename, s3_key.generate_url(expires_in=0, query_auth=False))

def create_pollock(s3_bucket, voicemail_filesname):
	return 'http://foo'

def add_to_gallery(hashed_user, voicemail_url, pollock_url):
	gallery = httplib.HTTPConnection('api.pollock.artcollective.io')
	gallery_entry = {
		'url': pollock_url,
		'inspiration_url': voicemail_url
	}

	gallery.request('POST', '/' + hashed_user, json.dumps(gallery_entry))
	response = gallery.getresponse()

	json_response = json.load(response)

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

