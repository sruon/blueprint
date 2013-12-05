from pymongo import MongoClient
import httplib
import socket

from blueprint import cfg
import librato
import statsd

#pip install pymongo

address = cfg.get('mongodb', 'address')
port = cfg.get('mongodb', 'port')
database = cfg.get('mongodb', 'database')
collection = cfg.get('mongodb', 'collection')

client = MongoClient(address, int(port))
db = client[database]
collection = db[collection]

class StoredObject:
	key = None
	tarball = None
	def __init__(self, key, tarball):
		self.key = key
		self.tarball = tarball

def delete(key):
    """
    Remove an object from S3.  DELETE requests are free but this function
    still makes one billable request to account for freed storage.
    """
    content_length = head(key)
    if content_length is None:
        return None
    librato.count('blueprint-io-server.requests.delete')
    statsd.increment('blueprint-io-server.requests.delete')
    collection.delete({"key" : key})


def delete_blueprint(secret, name):
    return delete(key_for_blueprint(secret, name))


def delete_tarball(secret, name, sha):
    return delete(key_for_tarball(secret, name, sha))


def get(key):
    """
    Fetch an object from S3.  This function makes one billable request.
    """
    librato.count('blueprint-io-server.requests.get')
    statsd.increment('blueprint-io-server.requests.get')
    k = collection.find_one({"key" : key})
    if k is None:
    	return False
    return k.tarball


def get_blueprint(secret, name):
    return get(key_for_blueprint(secret, name))


def get_tarball(secret, name, sha):
    return get(key_for_tarball(secret, name, sha))


def head(key):
    """
    Make a HEAD request for an object in S3.  This is needed to find the
    object's length so it can be accounted.  This function makes one
    billable request and anticipates another.
    """
    librato.count('blueprint-io-server.requests.head')
    statsd.increment('blueprint-io-server.requests.head')
    k = collection.find_one({"key" : key})
    if k is None:
      	return None
    return len(k.tarball)


def head_blueprint(secret, name):
    return head(key_for_blueprint(secret, name))


def head_tarball(secret, name, sha):
    return head(key_for_tarball(secret, name, sha))


def key_for_blueprint(secret, name):
    return '{0}/{1}/{2}'.format(secret,
                                name,
                                'blueprint.json')


def key_for_tarball(secret, name, sha):
    return '{0}/{1}/{2}.tar'.format(secret,
                                    name,
                                    sha)


def list(key):
    """
    List objects in S3 whose keys begin with the given prefix.  This
    function makes at least one billable request.
    """
    librato.count('blueprint-io-server.requests.list')
    statsd.increment('blueprint-io-server.requests.list')
    result = collection.find({"key" : '^%s' % (key)})
    return list(result)


def put(key, data):
    """
    Store an object in S3.  This function makes one billable request.
    """
    librato.count('blueprint-io-server.requests.put')
    statsd.increment('blueprint-io-server.requests.put')
    # TODO librato.something('blueprint-io-server.storage', len(data))
    statsd.update('blueprint-io-server.storage', len(data))
    element = StoredObject(key, data)
    collection.insert(element.__dict__)
    return True



def put_blueprint(secret, name, data):
    return put(key_for_blueprint(secret, name), data)


def put_tarball(secret, name, sha, data):
    return put(key_for_tarball(secret, name, sha), data)


def url_for(key):
    return ''


def url_for_blueprint(secret, name):
    return url_for(key_for_blueprint(secret, name))


def url_for_tarball(secret, name, sha):
    return url_for(key_for_tarball(secret, name, sha))
