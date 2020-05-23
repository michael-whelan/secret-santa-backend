import datetime

def log(msg):
	now_date = '{:%Y-%m-%d}'.format(datetime.datetime.now())
	now_date_time = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
	path = "logs/logs.%s.txt" % (now_date)
	message = "\n%s: %s" % (now_date_time, msg)
	f = open(path, "a+")
	f.write(message)
	f.close()
	print(msg)