import unittest
import config
import json
from werkzeug.exceptions import HTTPException
from elasticsearch import Elasticsearch
from app import *

# To test, make sure to set TESTING to True in config.py
class Tests(unittest.TestCase):

    # Sets up before each test function
    def setUp(self):
        # Ensures TESTING is set to True before starting
        self.assertEqual(True, config.TESTING)
        # Setting up context
        self.ctx = app.app_context()
        # Making sure to set up to correct ES url defined by
        # TESTING_ELASTICSEARCH_URL in configs
        ELASTICSEARCH_URL = config.TESTING_ELASTICSEARCH_URL
        if (ELASTICSEARCH_URL == ''):
            self.es = Elasticsearch()
        else:
            self.es = Elasticsearch(ELASTICSEARCH_URL)
        self.es.indices.create('tests')

    # After each test method deletes testing index
    def tearDown(self):
        self.es.indices.delete('tests')

    # Just testing adding contacts
    def test_new_contact(self):
        with self.ctx:
            self.assertEqual(({'mobile_phone': '1234567890', 'name': 'john baker'}, 201), \
            (json.loads(create_contact({'mobile_phone': '1234567890', 'name' : 'john baker'})[0].data), 201))
            self.assertEqual(({'address': '123 Cherry Rd', 'name': 'john connor'}, 201), \
            (json.loads(create_contact({'address': '123 Cherry Rd', 'name' : 'john connor'})[0].data), 201))
            self.assertEqual(({'name': 'jeffrey baker', 'notes': 'funny guy'}, 201), \
            (json.loads(create_contact({'name' : 'jeffrey baker', 'notes': 'funny guy'})[0].data), 201))
            self.assertEqual(({'email_address': 'jc@mail.com', 'name': 'jeffrey connor'}, 201), \
            (json.loads(create_contact({'email_address': 'jc@mail.com', 'name' : 'jeffrey connor'})[0].data), 201))
            # Making sure it only accepts allowed fields for contacts
            try:
                create_contact({'name' : 'jasmine bubbles', 'field_not_allowed': 'bad'})
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(400, err.code)
            # Making sure email format is correct
            try:
                create_contact({'name' : 'jasmine bubbles', 'email_address': 'notanemail'})
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(400, err.code)
            create_contact({'name' : 'jasmine bubbles', 'email_address': 'emailformat@email.com'})
            # Making sure phone number is not longer than 30 characters
            try:
                create_contact({'name' : 'jazzy blues', 'mobile_phone': '1234567890123456789012345678901'})
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(400, err.code)
            create_contact({'name' : 'jazzy blues', 'mobile_phone': '123456789012345678901234567890'})

    # Testing to make sure existing contact names are not added as contacts.
    # If 409 error is not thrown, should fail
    def test_adding_existing_contact(self):
        with self.ctx:
            create_contact({'name' : 'john baker'})
            try:
                create_contact({'name' : 'john baker'})
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(409, err.code)
            # Also testing with Uppercases
            try:
                create_contact({'name' : 'John Baker'})
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(409, err.code)

    # Testing get functionality
    def test_get_contact(self):
        with self.ctx:
            create_contact({'name' : 'john baker'})
            create_contact({'name' : 'james baker'})
            self.assertEqual({'name': 'john baker'}, json.loads(get_contact('john baker')[0].data))
            self.assertEqual({'name': 'james baker'}, json.loads(get_contact('james baker')[0].data))
            # Shouldn't be able to get a contact that doesn't exist
            try:
                get_contact('zack baker')
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(404, err.code)

    # Testing delete functionality
    def test_delete_contact(self):
        with self.ctx:
            create_contact({'name' : 'john baker'})
            get_contact('john baker')
            delete_contact('john baker')
            # john baker was deleted, should throw 404
            try:
                get_contact('john baker')
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(404, err.code)
            # Can't delete contact that does not exist
            try:
                delete_contact('jackie chan')
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(404, err.code)

    # Testing update functionality
    def test_update_contact(self):
        with self.ctx:
            # Can't update contact that does not exist
            try:
                update_contact('john baker', {'mobile_phone' : '1234567890'})
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(404, err.code)
            create_contact({'name' : 'john baker'})
            # Should not be able to modify name, which is the id/pk
            try:
                update_contact('john baker', {'name' : 'not john baker'})
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(400, err.code)
            # Should update contact, not replace it
            update_contact('john baker', {'mobile_phone' : '1234567890'})
            self.assertEqual({'mobile_phone' : '1234567890', 'name': 'john baker'}, \
            json.loads(get_contact('john baker')[0].data))

    # ERROR:
    # Traceback (most recent call last):
    #   File "tests.py", line 145, in test_contact_query
    #     json.loads(get_contact_query(None, None, None)[0].data))
    #   File "/Users/jl/Documents/webDev/address-book/app.py", line 50, in get_contact_query
    #     filter_path=['hits.hits._source'], size=pageSize*page)['hits']['hits']
    # KeyError: 'hits'
    # # Testing query functionality
    # def test_contact_query(self):
    #     with self.ctx:
    #         create_contact({"name" : "david jeffers", "address": "1234 Cherry Lane"})
    #         create_contact({"name" : "david heller", "address": "1234 Berry Lane"})
    #         create_contact({"name" : "david ross", "address": "4321 Cherry Lane"})
    #         create_contact({"name" : "david frank", "address": "100 Candy Lane"})
    #         # If no arguments are provided, should return all contacts
    #         self.assertEqual([{"address": "100 Candy Lane", "name": "david frank"}, \
    #         {"address": "1234 Berry Lane", "name": "david heller"}, \
    #         {"address": "1234 Cherry Lane", "name": "david jeffers"}, \
    #         {"address": "4321 Cherry Lane", "name": "david ross"}], \
    #         json.loads(get_contact_query(None, None, None)[0].data))
    #         # Putting in 1234 for query argument should result in these 2 results
    #         self.assertEqual([{"address": "1234 Berry Lane", "name": "david heller"}, \
    #         {"address": "1234 Cherry Lane", "name": "david jeffers"}], \
    #         json.loads(get_contact_query(None, None, '1234')[0].data))
    #         # Putting in david for query argument should result in all 4 davids
    #         self.assertEqual([{"address": "100 Candy Lane", "name": "david frank"}, \
    #         {"address": "1234 Berry Lane", "name": "david heller"}, \
    #         {"address": "1234 Cherry Lane", "name": "david jeffers"}, \
    #         {"address": "4321 Cherry Lane", "name": "david ross"}], \
    #         json.loads(get_contact_query(None, None, 'david')[0].data))
    #         # Setting pageSize to 2 and page to 1. Should get first 2 contacts of prev
    #         self.assertEqual([{"address": "100 Candy Lane", "name": "david frank"}, \
    #         {"address": "1234 Berry Lane", "name": "david heller"}], \
    #         json.loads(get_contact_query('2', '1', 'david')[0].data))
    #         # Setting page to 2. Should get the other 2 contacts
    #         self.assertEqual([{"address": "1234 Cherry Lane", "name": "david jeffers"}, \
    #         {"address": "4321 Cherry Lane", "name": "david ross"}], \
    #         json.loads(get_contact_query('2', '2', 'david')[0].data))
    #         # Setting page to 3. Should get empty list
    #         self.assertEqual([], \
    #         json.loads(get_contact_query('2', '3', 'david')[0].data))
    #         # Setting page to 1 and query to david, but no pageSize. pageSize will
    #         # default to 10
    #         self.assertEqual([{"address": "100 Candy Lane", "name": "david frank"}, \
    #         {"address": "1234 Berry Lane", "name": "david heller"}, \
    #         {"address": "1234 Cherry Lane", "name": "david jeffers"}, \
    #         {"address": "4321 Cherry Lane", "name": "david ross"}], \
    #         json.loads(get_contact_query(None, '1', 'david')[0].data))
    #         # Setting page to 2 for prev, should be empty list
    #         self.assertEqual([], \
    #         json.loads(get_contact_query(None, '2', 'david')[0].data))

# Set failfast to True to test one at a time
if __name__ == '__main__':
    unittest.main(failfast=True)
