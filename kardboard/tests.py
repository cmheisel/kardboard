import unittest2
import kardboard

class KardboardTestCase(unittest2.TestCase):
	def setUp(self):
		kardboard.app.config['MONGODB_DB'] = 'kardboard-unittest'
		self.app = kardboard.app.test_client()

	def tearDown(self):
		from mongoengine.connection import _get_db
		db = _get_db()
		#Truncate/wipe the test database
		[ db.drop_collection(name) for name in db.collection_names() \
			if 'system.' not in name ]


class ModelTests(KardboardTestCase):
	def test_sanity(self):
		self.assert_(True)

if __name__ == "__main__":
	unittest2.main()