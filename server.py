#!/usr/bin/python
# coding=utf-8

from BaseHTTPServer import HTTPServer,BaseHTTPRequestHandler
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
202 added person
401 insuffient rights
402 group not found
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
	import pdb; pdb.set_trace()
	if uuid is not None:
		status = db._delete_group( request.args.get('ugid'),uuid)
		return (jsonify({'status': status }))
	abort(401)
	# elif self.path.split('?')[0] == "/deletegroup":
	# status = db.delete_group(par,creds)

class Handler(BaseHTTPRequestHandler):
	def do_OPTIONS(self):
		self.send_response(200, "ok")
		self.send_header('Access-Control-Allow-Origin', '*')
		self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
		self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
		self.send_header("Access-Control-Allow-Headers", "Content-Type")
		self.end_headers()

	def do_GET(self) :
		# Look for main page
		if self.path=="/":
			self.path="/index.html"
		
		creds= {'uuid': 'null'}

		par = urlparse.parse_qs(urlparse.urlparse(self.path).query)
		try:
			creds['uuid'] = par['uuid'][0]
		except:
			log("warning: Cant capture uuid GET")
		
		path = self.path.split('?')[0]
		if path == "/getgroups" or path == "/getgroups/":
			self.send_response(200)
			self.wfile.write("\n")
			if creds['uuid'] =='null':
				self.send_response(201)
			else:
				json.dump(db.getGroups(creds['uuid']), self.wfile)
			self.end_headers
			return
		if path == "/getgroup":
			
			group = db.getGroup(par['ugid'][0],creds['uuid'])
			if group == 201:
				self.send_response(201)
				self.wfile.write("\n")
			else:
				self.send_response(200)
				self.wfile.write("\n")
				json.dump(group, self.wfile)
			self.end_headers()
			return
		if path == "/sendmail":
			people = db.get_people(par['ugid'][0],creds['uuid'])
			status = SS.gen_people(people)
			if status ==200:
				db.group_sent(par['ugid'][0])
			self.send_response(status)
			self.end_headers()
		self.send_response(404)
		return
	

	def parse_POST(self):
		length = int(self.headers.getheader('content-length'))
		# Get form data
		postvars = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
		newJson ={}
		for k in postvars:
			v = json.loads(k)
			for key in v:
				newJson[key] = v[key]
		return newJson

	def do_POST(self):
		creds= {'uuid': 'null'}
		postvars = self.parse_POST()
		try:
			creds['uuid'] = postvars['uuid']
		except:
			log("error: Cant capture uuid POST")
		
		if creds is not None:
			status = 404
			if self.path == "/creategroup" or self.path == "/creategroup/":
				status = db.addGroup(postvars["group_name"],creds)
			elif self.path == "/addperson" or self.path == "/addperson/":
				status = db.add_person(postvars,creds)
			self.send_response(status)
			self.end_headers()
			return
		self.send_response(404)
		self.end_headers()

	def do_PUT(self):
		creds= {'uuid': 'null'}

		postvars = self.parse_POST()
		try:
			creds['uuid'] = postvars['uuid']
		except:
			log("error: Cant capture uuid PUT")
		if creds is not None:
			status = 404
			if self.path == "/updateperson" or self.path == "/updateperson/":
				status = db.update_person(postvars,creds)
			elif self.path == "/updategroup" or self.path == "/updategroup/":
				status = db.update_group(postvars,creds)
			self.send_response(status)
			self.end_headers()
			return
		self.send_response(404)
		self.end_headers()


	def do_DELETE(self):
		creds= {'uuid': 'test'}
		par = urlparse.parse_qs(urlparse.urlparse(self.path).query)
		try:
			creds['uuid'] = par['uuid'][0]
		except:
			log("error: Cant capture uuid DELETE")
		
		if creds is not None:
			if self.path.split('?')[0] == "/deleteperson":
				status = db.delete_person(par,creds)
			elif self.path.split('?')[0] == "/deletegroup":
				status = db.delete_group(par,creds)
			self.send_response(status)
			self.end_headers()
if __name__ == '__main__':
	if 'liveconsole' not in gethostname():
		app.run(debug=True)
	#server = HTTPServer(("localhost", PORT), Handler)
	#print ("serving on port", PORT)
	#server.serve_forever()
