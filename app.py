from flask import Flask, render_template, request, jsonify, abort
from elasticsearch import Elasticsearch
from werkzeug.exceptions import HTTPException
import re

# Creates instance of Flask for our app
app = Flask(__name__)
# Loads configuration from config.py
app.config.from_object('config')
# Default URL is http://localhost:9200/ if not provided in config.py
ELASTICSEARCH_URL = app.config['ELASTICSEARCH_URL']
# Default has no API key if not provided in config.py
API_KEY = app.config['API_KEY']
# Setting index to tests if TESTING is True in config.py
APP_INDEX = 'tests' if app.config['TESTING'] else 'contacts'
# If ELASTICSEARCH_URL is set, it will use that URL instead
if (ELASTICSEARCH_URL == ''):
    es = Elasticsearch()
else:
    es = Elasticsearch(ELASTICSEARCH_URL)
# Allowed fields for a contact
allowed_contact_fields = {'name', 'first_name', 'middle_name', 'last_name', 'email_address', \
'website', 'home_phone', 'work_phone', 'mobile_phone', 'address', 'notes'}

# Handles requests to /contact
@app.route('/contact', methods=['GET', 'POST'])
def handle_contact():
    # Checks for correct API key if set in config.py
    if API_KEY != '' and request.headers.get('X_API_KEY') != API_KEY:
        abort(401, {'message': '''Unauthorized, requires correct API key (e.g., -H 'X-Api-Key: KEY_HERE')'''})
    # If request method is GET
    if request.method == 'GET':
        return get_contact_query(request.args.get('pageSize'), request.args.get('page'), request.args.get('query'))
    # If request method is POST, request should be to create a new Contact
    else:
        # Enforces JSON format and calls create function with provided data
        return create_contact(request.get_json(force=True))

# Returns an array of objects in JSON format based on request arguments
def get_contact_query(pageSize, page, query):
    # pageSize defaults to 10 and page defaults to 1 if not provided.
    # Default error handler will throw error response if invalid arguments provided
    pageSize = int (pageSize) if pageSize else 10
    page = int (page) if page else 1
    # If query is not provided as an argument
    if not query:
        hits = es.search(index=APP_INDEX, doc_type="contact", \
        filter_path=['hits.hits._source'], size=pageSize*page)['hits']['hits']
        # If pageSize is not provided, return all contacts
        if not pageSize:
            queried_contact_list = [contact['_source'] for contact in hits]
        # If pageSize is provided, return corresponding contacts for page and pageSize
        else:
            queried_contact_list = [contact['_source'] for contact in hits][pageSize*page-pageSize:pageSize*page]
    # If query is provided as an argument
    else:
        hits = es.search(index=APP_INDEX, doc_type="contact", \
        filter_path=['hits.hits._source'], size=pageSize*page, body={"query": {"query_string" : {"query": query}}})['hits']['hits']
        # If pageSize is provided, return corresponding contacts for page and pageSize
        if pageSize:
            queried_contact_list = [contact['_source'] for contact in hits][pageSize*page-pageSize:pageSize*page]
        # Otherwise return all results for that query
        else:
            queried_contact_list = [contact['_source'] for contact in hits]
    return jsonify(queried_contact_list), 200

# Creates a new contact with given data
def create_contact(data):
    # Makes sure name is included, since it will be used as the id/primary key
    if not 'name' in data:
        abort(400, {'message': 'Must have name in data'})
    # Ensuring name is saved in same lowercase format
    name = data['name'].lower()
    data['name'] = name
    # Contact name must be unique. If name does not already exist, create contact
    if es.exists(index=APP_INDEX, doc_type='contact', id=name):
        abort(409, {'message': 'Contact already exists, try a PUT request to modify current contact'})
    # Will abort and throw error if data is invalid
    check_data_validity(data)
    # Create if it passes all checks
    es.index(index=APP_INDEX, doc_type='contact', id=name, body=data)
    return jsonify(data), 201

# Handles requests to /contact/{name}
@app.route('/contact/<string:name>', methods=['GET', 'PUT', 'DELETE'])
def handle_contact_name(name):
    # All names are saved as lowercase
    name = name.lower()
    # Checks for correct API key if set in config.py
    if API_KEY != '' and request.headers.get('X_API_KEY') != API_KEY:
        abort(401, {'message': '''Unauthorized, requires correct API key (e.g., -H 'X-Api-Key: KEY_HERE')'''})
    # If request if GET, call and return get function
    if request.method == 'GET':
        return get_contact(name)
    # If request if PUT, call and return update function
    elif request.method == 'PUT':
        return update_contact(name, request.get_json(force=True))
    # If request if DELETE, call and return delete function
    else:
        return delete_contact(name)

# Retrieves contact in JSON format if found
def get_contact(name):
    if not es.exists(index=APP_INDEX, doc_type='contact', id=name):
        abort(404, {'message': 'Contact not found'})
    result = es.get(index=APP_INDEX, doc_type='contact', id=name)
    return jsonify(result['_source']), 200

# Updates contact if found
def update_contact(name, data):
    if not es.exists(index=APP_INDEX, doc_type='contact', id=name):
        abort(404, {'message': 'Contact not found'})
    # Making sure name is not changed
    if data.get('name') and data.get('name').lower() != name:
        abort(400, {'message': 'Cannot modify name. It is used as a primary key'})
    # Will abort and throw error if data is invalid
    check_data_validity(data)
    # Update if it passes all checks
    es.update(index=APP_INDEX, doc_type='contact', id=name, body={"doc": data})
    return jsonify({'message': 'Contact updated'}), 200

# Deletes contact if found
def delete_contact(name):
    if not es.exists(index=APP_INDEX, doc_type='contact', id=name):
        abort(404, {'message': 'Contact not found'})
    es.delete(index=APP_INDEX, doc_type='contact', id=name)
    return jsonify({'message': 'Contact deleted'}), 200

# Handles exceptions. Returns error/description (JSON format) and response code
@app.errorhandler(Exception)
def handle_error(e):
    response_code = 500
    if isinstance(e, HTTPException):
        response_code = e.code
    return jsonify(error=str(e)), response_code

# Checks data for contact to be created/updated and ensures validity
def check_data_validity(data):
    # Checking to ensure only allowed fields are given for contact data
    if not set(data.keys()).issubset(allowed_contact_fields):
        abort(400, {'message': 'Field not allowed. Allowed fields are: '+ ' '.join(allowed_contact_fields)})
    # The following mainly checks to ensure character length. Can be modified as needed
    if data.get('name') and len(data.get('name')) > 122:
        abort(400, {'message': 'The limit for name is 101 characters'})
    if data.get('first_name') and len(data.get('first_name')) > 40:
        abort(400, {'message': 'The limit for first_name is 40 characters'})
    if data.get('middle_name') and len(data.get('middle_name')) > 40:
        abort(400, {'message': 'The limit for middle_name is 40 characters'})
    if data.get('last_name') and len(data.get('last_name')) > 40:
        abort(400, {'message': 'The limit for last_name is 40 characters'})
    if data.get('email_address'):
        if len(data.get('email_address')) > 200:
            abort(400, {'message': 'The limit for email_address is 200 characters'})
        # Ensures correct email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data.get('email_address')):
            abort(400, {'message': 'Invalid format for email_address'})
    if data.get('website') and len(data.get('website')) > 255:
        abort(400, {'message': 'The limit for website is 255 characters'})
    if data.get('home_phone') and len(data.get('home_phone')) > 30:
        abort(400, {'message': 'The limit for home_phone is 30 characters'})
    if data.get('work_phone') and len(data.get('work_phone')) > 30:
        abort(400, {'message': 'The limit for work_phone is 30 characters'})
    if data.get('mobile_phone') and len(data.get('mobile_phone')) > 30:
        abort(400, {'message': 'The limit for mobile_phone is 30 characters'})
    if data.get('address') and len(data.get('address')) > 255:
        abort(400, {'message': 'The limit for address is 255 characters'})
    if data.get('notes') and len(data.get('notes')) > 255:
        abort(400, {'message': 'The limit for notes is 255 characters'})

# Simple page to show api options
@app.route('/')
def index():
    return render_template('index.html')

# Runs the app for development
if __name__ == '__main__':
    app.run(debug=True)
