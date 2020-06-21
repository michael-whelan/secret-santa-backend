import sqlite3
import uuid
import hashlib
import calendar
import time
from logger import log
from socket import gethostname
import local_settings
import mysql.connector

#dbpath= '/home/MichaelWhelan/secret-santa-backend/secretsanta.db'
#if local_settings.environment == 'dev':
#	dbpath= 'secretsanta.db'

config = {
	'username': local_settings.sql_user,
	'password': local_settings.sql_pass,
	'host': local_settings.sql_host,
	'database': local_settings.sql_db,
	'raise_on_warnings': True
}

def connect_db():
	conn = None
	if local_settings.environment == 'dev':
		conn = sqlite3.connect('secretsanta.db')
	else:
		conn = mysql.connector.connect(**config)
	return conn

def get_tables():
	cnx = connect_db()
	query = ("show tables")
	cursor = cnx.cursor()
	cursor.execute(query)
	data=cursor.fetchall()
	cnx.close()
	return data


def generate_uid():
	return uuid.uuid1().hex

def uniqueEntry(q):
	conn = sqlite3.connect(dbpath)
	#query = "SELECT %s from %s where %s = '%s'" % (sel, tbl,sel,email)
	cursor = conn.execute(q)
	data = cursor.fetchall()
	conn.close()
	if not data:
		return True
	else:
		return False

def getGroups(uuid):
	#query = """SELECT * from groups where admin = (select id from users where uuid = '%s');""" % (uuid)
	#query = """SELECT g.id as group_id,g.group_name,g.sent, p.id as person_id,p.name,p.email,p.active, p.nots from groups g inner join
	#people p where g.id = p.group_id and g.admin_uuid = '%s' order by p.group_id;""" % (uuid)
	query = """SELECT id as group_id,group_name,sent, public, group_url_id from groups 
	where admin_uuid = '%s' order by id;""" % (uuid)
	if uuid == 'test':
		query = """SELECT * from groups""" 
	conn = sqlite3.connect(dbpath)
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
	return raw_data	

def _get_group(g_id, u_id):
	if not user_group_rights(g_id,u_id,None, False):
		return 401

	query1 = """SELECT id as group_id,group_name,sent,public,group_url_id from groups
	where group_url_id = '%s'""" % (g_id)
	query2 = """SELECT id as person_id,name,email,active,nots 
	from people where group_id = 
	(select id from groups where group_url_id = '%s')""" % (g_id)
	conn = sqlite3.connect(dbpath)
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
	return ret_data

def get_people(g_id, u_id):
	if not user_group_rights(g_id,u_id,None, False):
		return 401
	query = """SELECT id,name,email,nots
	from people where group_id = 
	(select id from groups where group_url_id = '%s')""" % (g_id)
	conn = sqlite3.connect(dbpath)
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
	

def _add_group(groupName, uuid):
	broken_query = "error"
	if uniqueEntry("""select * from groups where group_name = '%s'""" % (groupName)):
		try:
			nowTime = calendar.timegm(time.gmtime())
			ugid = generate_uid()
			query = """insert into groups (group_name,date_created,last_update_date,admin_uuid,public,sent,group_url_id)
				values ('%s', '%s', '%s', '%s', 0,0,'%s');""" % (
					groupName,nowTime,nowTime,uuid,ugid
				)
			broken_query =query 
			do_query(query)
			return 200
		except:
			print("Error: add_group. "+broken_query)
			log("Error: add_group. "+broken_query)
			return 400
	return 400


def make_update_strings(vars):
	ret_string = ""
	for var in vars:
		ret_string = ret_string + "%s = '%s', " % (var, vars[var]) 
	return ret_string[:-2]


def _update_person(vars,uuid):
	id = vars.pop("person_id", None)
	update_string = make_update_strings(vars)
	if not user_group_rights(None,uuid,id, False):
		return 401
	
	query = """update people set %s where id = %s""" % (
				update_string, id
			)
	try:
		do_query(query)
		return 200
	except:
		log("Error: update_person. "+query)
		return 400

def _update_group(vars, uuid):
	id = vars.pop("ugid", None)
	if 'public_group' in vars:
		vars['public'] = vars.pop("public_group")
	if not user_group_rights(id,uuid,None, False):
		return 401
	update_string = make_update_strings(vars)
	query = """update groups set %s where group_url_id = '%s'""" % (
				update_string, id
			)
	try:
		do_query(query)
		record_update(id)
		return 200
	except:
		log("Error: update_group. "+query)
		return 400

def _delete_group(ugid, uuid):
	if ugid:
		if not user_group_rights(ugid,uuid,None, True):
			return 401
		broken_query1 = "error"
		broken_query2 = "error"
		try:
			query1 = """delete from people where group_id =
			(select id from groups where group_url_id = '%s' and admin_uuid = '%s');""" % (
					ugid, uuid
				)
			query2 = """delete from groups where group_url_id = '%s' and admin_uuid = '%s';""" % (
					ugid, uuid
				)
			broken_query1 = query1
			broken_query2 = query2
			do_query(query1)
			do_query(query2)
			return 200
		except:
			log("Error: delete_group")
			log(broken_query1)
			log(broken_query2)
			return 400
	return 400

def _add_person(vars):
	if not user_group_rights(vars["ugid"],vars["uuid"], None,False):
		return 401
	new_name = vars["name"]
	new_email = vars["email"]
	query = """insert into people(group_id, name, email, active) values (
		(select id from groups where group_url_id = '%s')
		, '%s', '%s',%s)""" % (
				vars["ugid"], new_name, new_email,1
			)
	try:
		do_query(query)
		record_update(vars["ugid"])
		return 200
	except:
		log("Error: Adding person. "+query)
		return 400

def _delete_person(pid, uuid):
	if not user_group_rights(None,uuid,pid, True):
		return 401
	if pid:
		try:
			query = """delete from people where id = %s""" % (
						pid
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
		conn = sqlite3.connect(dbpath)
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

def record_update(ugid):
	nowTime = calendar.timegm(time.gmtime())
	query = """update groups set last_update_date = '%s' where 
	group_url_id = '%s'""" % (nowTime,ugid)
	try:
		do_query(query)
	except:
		log("Error updating group update time. "+query)

def do_query(q):
	conn = sqlite3.connect(dbpath)
	cursor = conn.cursor()
	cursor.execute(q)
	conn.commit()
	conn.close()