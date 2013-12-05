from pymongo import MongoClient
import httplib
import socket

from blueprint import cfg
import librato
import statsd

#pip install pymongo

address = cfg.get('mongodb', 'address')
port = cfg.get('mongodb', 'port')
protocol = 'https' if cfg.getboolean('server', 'use_https') else 'http'
database = cfg.get('mongodb', 'database')
collection = cfg.get('mongodb', 'collection')
url = cfg.get('server', 'address')

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
    Remove an object from MongoDB.
    """
    content_length = head(key)
    if content_length is None:
        return None
    librato.count('blueprint-io-server.requests.delete')
    statsd.increment('blueprint-io-server.requests.delete')
    try:
        collection.delete({"key" : key})
    except:
        return False

def delete_blueprint(secret, name):
    return delete(key_for_blueprint(secret, name))


def delete_tarball(secret, name, sha):
    return delete(key_for_tarball(secret, name, sha))


def get(key):
    """
    Fetch an object from MongoDB.
    """
    librato.count('blueprint-io-server.requests.get')
    statsd.increment('blueprint-io-server.requests.get')
    try:
        k = collection.find_one({"key" : key})
        if k is None:
    	   return None
    except:
        return False
    return k['tarball']


def get_blueprint(secret, name):
    return get(key_for_blueprint(secret, name))


def get_tarball(secret, name, sha):
    return get(key_for_tarball(secret, name, sha))


def head(key):
    """
    Make a HEAD request for an object in MongoDB. 
    This returns the size of the tarball.
    """
    librato.count('blueprint-io-server.requests.head')
    statsd.increment('blueprint-io-server.requests.head')
    try:
        k = collection.find_one({"key" : key})
        if k is None:
            return None
    except:
        return False
    return len(k['tarball'])


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
    List objects in MongoDB whose key begins with the given prefix
    """
    librato.count('blueprint-io-server.requests.list')
    statsd.increment('blueprint-io-server.requests.list')
    try:
        result = collection.find({"key" : '^%s' % (key)})
    except:
        return False
    return result


def put(key, data):
    """
    Store an object in MongoDB.
    """
    librato.count('blueprint-io-server.requests.put')
    statsd.increment('blueprint-io-server.requests.put')
    # TODO librato.something('blueprint-io-server.storage', len(data))
    statsd.update('blueprint-io-server.storage', len(data))
    element = StoredObject(key, data)
    try:
        collection.insert(element.__dict__)
    except:
        return False
    return True



def put_blueprint(secret, name, data):
    return put(key_for_blueprint(secret, name), data)


def put_tarball(secret, name, sha, data):
    return put(key_for_tarball(secret, name, sha), data)


def url_for(key):
    return '{0}://{1}/{2}'.format(protocol, url, key)


def url_for_blueprint(secret, name):
    return url_for(key_for_blueprint(secret, name))


def url_for_tarball(secret, name, sha):
    return url_for(key_for_tarball(secret, name, sha))
