## The Python


The server side logic for the app is in two parts:

### 1. API

A simple rest server used for data management (groups + settings, people in those groups etc).
Using Flaskr to handle my REST requests:
```python
from flask import Flask, jsonify,abort,request

@app.route('/getgroups', methods=['GET'])
def get_groups():
	uuid = request.args.get('uuid')
	if not uuid:
		abort(401)
	else:
		return (jsonify(db.getGroups(uuid)),200)
```


Using React Router on the front end allowed the implementation of adding unique url ids for the groups. This makes public groups accessible through the URL. eg www.domain/group/12e333egwp where 12e333egwp is unique to a group.
This comined with Flasks request.args allows for easy retrieval of url variables.
This will make sending/sharing groups easier, simply passing a url and letting everyone add their own emails from there.


### 2. The Hat Sorter
The second part of the server logic is the actual hat sort function.
This is done in two ways. Depending on whether or not the group admin has added other people into _"not"_ fields.

- If the group contains the _"not"_ field the sorting is done from largest number of nots _N_ to the smallest _n_. This way the most likely problem selections will be handled first when there are the most options for choosing.
- If the _"not"_ field doesn't get filled out then the random selection is much easier. The simpler wqay to randomly sort people into pairs is just by randomising the list and assigning people the next person in the list and the last person the first. This way guarantees everyone is found a pair and it's the simplest pairing method.


Another aspect of the second part is the use of google account to send the emails from, simply creating a MIMEText message with sender/recipient/body and sending it through the account was fine. 


## The Database
The database model for secret santa is very simple. 

- A relational database (most likely MySQL) with just 3 Tables:

    **Groups**
        The set of groups created by different users. Creating a group sets the user as the admin of that group. This allows the user to see the group in full detail and set the group between private and public. The admin can also add people to a group.  

    **Users**
        A table containing all the users that access the site (via login). This keeps track of login details and uuids for quick temporary login

    **People**
        These are the people within groups. Much simpler than the users as they themselves don't log in and are just a name and email.
