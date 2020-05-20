import sqlite3
import uuid
import datetime
import hashlib


def generate_uid():
	return uuid.uuid1().hex

def uniqueEntry(q):
	conn = sqlite3.connect('secretsanta.db')
	#query = "SELECT %s from %s where %s = '%s'" % (sel, tbl,sel,email)
	cursor = conn.execute(q)
	data = cursor.fetchall()
	conn.close()
	if not data:
		return True
	else:
		return False


def getUser(u,e,recpass):
	query= ""
	conn = sqlite3.connect('secretsanta.db')
	if u is not None:
		query = "SELECT * from users where uuid = '%s'" % (u)
	else:
		query = "SELECT * from users where email = '%s'" % (e)
	cursor = conn.execute(query)
	if cursor == None:
		return None
	rows = [x for x in cursor]
	cols = [x[0] for x in cursor.description]
	data = {}
	for row in rows:
		for prop, val in zip(cols, row):
			data[prop] = val
	
	conn.close()
	print ("getUser done successfully")
	return data

def getGroups(uuid):
	#query = """SELECT * from groups where admin = (select id from users where uuid = '%s');""" % (uuid)
	#query = """SELECT g.id as group_id,g.group_name,g.sent, p.id as person_id,p.name,p.email,p.active, p.nots from groups g inner join
	#people p where g.id = p.group_id and g.admin_uuid = '%s' order by p.group_id;""" % (uuid)
	query = """SELECT id as group_id,group_name,sent, public, group_url_id from groups 
	where admin_uuid = '%s' order by id;""" % (uuid)
	if uuid == 'test':
		query = """SELECT * from groups""" 
	conn = sqlite3.connect('secretsanta.db')
	cursor= conn.cursor()
	cursor.execute(query)
	if cursor == None:
		return None
	rows = [x for x in cursor]
	cols = [x[0] for x in cursor.description]
	raw_data = []

	for row in rows:
		dataSingle = {}
		for prop, val in zip(cols, row):
			dataSingle[prop] = val
		raw_data.append(dataSingle)
	conn.close()
	print ("getGroups done successfully")
	return raw_data	

def getGroup(g_id, u_id):
	if not user_group_rights(g_id,u_id,None, False):
		return 201

	query1 = """SELECT id as group_id,group_name,sent,public,group_url_id from groups
	where group_url_id = '%s'""" % (g_id)
	query2 = """SELECT id as person_id,name,email,active,nots 
	from people where group_id = 
	(select id from groups where group_url_id = '%s')""" % (g_id)
	conn = sqlite3.connect('secretsanta.db')
	cursor= conn.cursor()
	cursor.execute(query1)
	group_info = cursor.fetchall()
	cursor.execute(query2)
	people_info = cursor.fetchall()
	conn.close()
	
	ret_data = {
		"group_id": group_info[0][0],
		"group_name": group_info[0][1],
		"sent": group_info[0][2],
		"public": group_info[0][3],
		"ugid":group_info[0][4]
	}

	people = []
	for personDetail in people_info:
		person = {
			'person_id':personDetail[0],
			'name': personDetail[1],
			'email': personDetail[2],
			'active': personDetail[3],
			'nots': personDetail[4] 
		}
		people.append(person)
	ret_data["people"] = people
	print ("getGroup done successfully")
	return ret_data

def get_people(g_id, u_id):
	if not user_group_rights(g_id,u_id,None, False):
		return 201
	query = """SELECT id,name,email,nots
	from people where group_id = 
	(select id from groups where group_url_id = '%s')""" % (g_id)
	conn = sqlite3.connect('secretsanta.db')
	cursor= conn.cursor()
	cursor.execute(query)
	people_info = cursor.fetchall()
	conn.close()
	return people_info

	
def group_sent(g_id):
	query = """UPDATE groups SET sent = 1
	where group_url_id = '%s'""" % (g_id)
	do_query(query)
	return 200
	

def addGroup(groupName, userInfo):
	uuid = userInfo["uuid"]
	broken_query = "error"
	if uniqueEntry("""select * from groups where group_name = '%s'""" % (groupName)):
		try:
			nowTime = '{:%Y-%m-%d}'.format(datetime.datetime.now())
			ugid = generate_uid()
			query = """insert into groups (group_name,date_created,last_update_date,admin_uuid,public,sent,group_url_id)
				values ('%s', '%s', '%s', '%s', 0,0,'%s');""" % (
					groupName,nowTime,nowTime,uuid,ugid
				)
			broken_query =query 
			do_query(query)
			return 200
		except:
			print("Error: add_group")
			print(broken_query)
			return 400
	return 400


def make_update_strings(vars):
	ret_string = ""
	for var in vars:
		ret_string = ret_string + "%s = '%s', " % (var, vars[var]) 
	return ret_string[:-2]


def update_person(vars, creds):
	id = vars.pop("person_id", None)
	vars.pop("uuid", None)
	update_string = make_update_strings(vars)
	if not user_group_rights(None,creds["uuid"],id, False):
		return 201
	
	query = """update people set %s where id = %s""" % (
				update_string, id
			)
	try:
		do_query(query)
		return 200
	except:
		print("Error: update_person")
		print(query)
		return 400

def update_group(vars, creds):
	id = vars.pop("ugid", None)
	vars.pop("uuid", None)
	vars['public'] = vars.pop("public_group")
	
	if not user_group_rights(id,creds["uuid"],None, False):
		return 201
	update_string = make_update_strings(vars)
	query = """update groups set %s where group_url_id = '%s'""" % (
				update_string, id
			)
	try:
		do_query(query)
		return 200
	except:
		print("Error: update_group")
		print(query)
		return 400

def delete_group(vars, creds):
	if vars["ugid"][0]:
		if not user_group_rights(vars["ugid"][0],creds["uuid"],None, True):
			return 201
		broken_query1 = "error"
		broken_query2 = "error"
		try:
			query1 = """delete from people where group_id =
			(select id from groups where group_url_id = '%s' and admin_uuid = '%s');""" % (
					vars["ugid"][0], creds["uuid"]
				)
			query2 = """delete from groups where group_url_id = '%s' and admin_uuid = '%s';""" % (
					vars["ugid"][0], creds["uuid"]
				)
			broken_query1 = query1
			broken_query2 = query2
			do_query(query1)
			do_query(query2)
			return 200
		except:
			print("Error: delete_group")
			print(broken_query1)
			print(broken_query2)
			return 400
	return 400

def add_person(vars,creds):
	if not user_group_rights(vars["ugid"],creds["uuid"], None,False):
			return 201
	new_name = vars["name"]
	new_email = vars["email"]
	query = """insert into people(group_id, name, email, active) values (
		(select id from groups where group_url_id = '%s')
		, '%s', '%s',%s)""" % (
				vars["ugid"], new_name, new_email,1
			)
	try:
		do_query(query)
		return 200
	except:
		print("Error: Adding person")
		print(query)
		return 400

def delete_person(vars, creds):
	if not user_group_rights(None,creds["uuid"],vars["id"][0], True):
		return 201
	if vars["id"][0]:
		try:
			query = """delete from people where id = %s""" % (
						vars["id"][0]
					)
			do_query(query)
			return 200
		except:
			return 400
	return 400


#Check if the current user has the rights for the action selected.
#Strict false means that if the group is public allow this right (does not apply to delete) 
def user_group_rights(gid, uid, pid,strict=True):
	try:
		query = None
		if gid:
			if strict:
				query = """select * from groups where group_url_id = '%s' and admin_uuid = '%s';""" % (
					gid, uid
				)
			else:
				query = """select * from groups where group_url_id = '%s' and (admin_uuid = '%s' or public=1);""" % (
					gid,uid
				)
		elif pid:
			if strict:
				query = """select * from groups where id = 
				(select group_id from people where id =%s) 
				and admin_uuid ='%s';""" % (
					pid, uid
				)
			else:
				query = """select * from groups where id = 
				(select group_id from people where id =%s) 
				and (admin_uuid ='%s' or public=1);""" % (
					pid, uid
				)
		if query == None:
			return False
		conn = sqlite3.connect('secretsanta.db')
		cursor= conn.cursor()
		cursor.execute(query)
		if cursor == None:
			return None
		rows = cursor.fetchall()
		conn.close()
		if len(rows) > 0:
			return True
		return False
	except:
		return False


def do_query(q):
	conn = sqlite3.connect('secretsanta.db')
	cursor = conn.cursor()
	cursor.execute(q)
	conn.commit()
	conn.close()