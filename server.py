#!/usr/bin/python
# coding=utf-8
from flask import Flask, jsonify,abort,make_response,request
import urlparse
import db
import SS
from logger import log
from socket import gethostname


app = Flask(__name__)

PORT = 8080

"""
Codes:
200 success
401 insuffient rights
400 generic wrong
404 error in understanding request
"""

#creds = db.check_credentials(self.headers.getheader('X-User-ID'),
#	self.headers.getheader('X-User-Email'), self.headers.getheader('X-User-Pass'))

@app.route('/getgroups', methods=['GET'])
def get_groups():
	uuid = request.args.get('uuid')
	if not uuid:
		abort(401)
	else:
		return (jsonify(db.getGroups(uuid)),200)


@app.route('/getgroup/', methods=['GET'])
def get_group():
	uuid = request.args.get('uuid')
	ugid = request.args.get('ugid')
	group = db._get_group(ugid,uuid)
	if group == 401:
		abort(401)
	return (jsonify(group),200)

@app.route('/sendmail', methods=['GET'])
def send_mail():
	uuid = request.args.get('uuid')
	ugid = request.args.get('ugid')
	people = db.get_people(ugid,uuid)
	status = SS.gen_people(people)
	if status ==200:
		db.group_sent(ugid)
		return(jsonify({'status': status }))
	abort(400)

@app.route('/creategroup', methods=['POST'])
def create_group():
	uuid = 'null'
	try:
		uuid = request.json["uuid"]
	except:
		log("error: Cant capture uuid POST")
	if uuid is not None:
		status = db._add_group(request.json["group_name"],uuid)
		return jsonify({'status': status })
	abort(404)

@app.route('/addperson', methods=['POST'])
def add_person():
	uuid = 'null'
	status = db._add_person(request.json)
	if status == 401:
		abort(401)
	return (jsonify(status), 200)

@app.route('/updateperson', methods=['PUT'])
def update_person():
	uuid = 'null'
	try:
		uuid = request.json.pop("uuid", None)
	except:
		log("error: Cant capture uuid POST")
		abort(401)
	status = db._update_person(request.json,uuid)
	return (jsonify({'status': status }))

@app.route('/updategroup', methods=['PUT'])
def update_group():
	uuid = 'null'
	try:
		uuid = request.json.pop("uuid", None)
	except:
		log("error: Cant capture uuid POST")
		abort(401)
	status = db._update_group(request.json,uuid)
	return (jsonify({'status': status }))

@app.route('/deleteperson', methods=['DELETE'])
def delete_person():
	uuid = 'null'
	try:
		uuid = request.args.get('uuid')
	except:
		log("error: Cant capture uuid DELETE")
		abort(401)
	if uuid is not None:
		status = db._delete_person( request.args.get('id'),uuid)
		return (jsonify({'status': status }))
	abort(401)

@app.route('/deletegroup', methods=['DELETE'])
def delete_group():
	uuid = 'null'
	try:
		uuid = request.args.get('uuid')
	except:
		log("error: Cant capture uuid DELETE")
		abort(401)
	if uuid is not None:
		status = db._delete_group( request.args.get('ugid'),uuid)
		return (jsonify({'status': status }))
	abort(401)


if __name__ == '__main__':
	if 'liveconsole' not in gethostname():
		app.run(debug=True)
