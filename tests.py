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

    # Testing to ensure validity in arguments provided for query
    def test_valid_query_arguments(self):
        with self.ctx:
            create_contact({'name' : 'john baker'})
            create_contact({'name' : 'john bob'})
            create_contact({'name' : 'john jones'})
            create_contact({'name' : 'john jeter'})
            # page is given while pageSize is not given. Should throw 400 error
            try:
                get_contact_query(None, 2, 'john')
                raise AssertionError()
            except HTTPException as err:
                self.assertEqual(400, err.code)

# Set failfast to True to test one at a time
if __name__ == '__main__':
    unittest.main(failfast=True)
