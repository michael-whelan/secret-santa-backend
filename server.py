#!/usr/bin/python
# coding=utf-8

from BaseHTTPServer import HTTPServer,BaseHTTPRequestHandler
import json
import cgi
import urlparse
import db
import SS
from logger import log

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

PORT = 8080

"""
Codes:
200 success
201 insuffient rights
202 added person
401 uuid not found
402 group not found
404 error in understanding request
"""

#creds = db.check_credentials(self.headers.getheader('X-User-ID'),
#	self.headers.getheader('X-User-Email'), self.headers.getheader('X-User-Pass'))

class Handler (BaseHTTPRequestHandler) :
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
	server = HTTPServer(("localhost", PORT), Handler)
	print ("serving on port", PORT)
	server.serve_forever()
