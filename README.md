# Address Book API

## Data Model:
**In JSON Format**
* **name:** primary key, 122 char limit  
* **first_name:** 40 char limit  
* **middle_name:** 40 char limit  
* **last_name:** 40 char limit  
* **email_address:** 200 char limit  
* **website:** 255 char limit  
* **home_phone:** 30 char limit  
* **work_phone:** 30 char limit  
* **mobile_phone:** 30 char limit
* **address:** 255 char limit  
* **notes:** 255 char limit  

## Endpoints:
&nbsp;&nbsp;**To query:**  
&nbsp;&nbsp;&nbsp;&nbsp;GET /contact?pageSize={}&page={}&query={}  
&nbsp;&nbsp;&nbsp;&nbsp;(e.g., "http://localhost:5000/contact?pageSize=10&page=1&query=jeffrey")  
&nbsp;&nbsp;**To add a contact:**  
&nbsp;&nbsp;&nbsp;&nbsp;POST /contact  
&nbsp;&nbsp;&nbsp;&nbsp;(e.g., curl -X POST "http://localhost:5000/contact" -d '{"name": "jeffrey franklin", "work_phone": "1234567890"}')  
&nbsp;&nbsp;**To get a contact:**  
&nbsp;&nbsp;&nbsp;&nbsp;GET /contact/{name}  
&nbsp;&nbsp;**To update a contact:**  
&nbsp;&nbsp;&nbsp;&nbsp;PUT /contact/{name}  
&nbsp;&nbsp;&nbsp;&nbsp;(e.g., curl -X PUT "http://localhost:5000/contact/jeffrey%20franklin" -d '{"work_phone": "0987654321"}')  
&nbsp;&nbsp;**To delete a contact:**  
&nbsp;&nbsp;&nbsp;&nbsp;DELETE /contact/{name}  

## To run:
**Set up a virtual environment**  
Dependencies are in requirements.txt.  
&nbsp;&nbsp;&nbsp;&nbsp;$ pip3 install requirements.txt  
**Modify config.py as needed**  
**Run production server**  
&nbsp;&nbsp;&nbsp;&nbsp;$ flask run

## To test:
**Modify config.py to reflect testing**  
&nbsp;&nbsp;&nbsp;&nbsp;Set TESTING_ELASTICSEARCH_URL as needed and TESTING to True  
&nbsp;&nbsp;&nbsp;&nbsp;$ python3 tests.py
