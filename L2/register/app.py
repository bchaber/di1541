import re, json, pickle
from flask import Flask
from flask import request
from flask import make_response
from datetime import datetime as dt
users = {}
app = Flask(__name__)

@app.route('/')
def index():
  return '''<!doctype html>
  <head><title>REGISTER endpoints</title></head>

  <ul>
  <li><a href='/user/bach'>Check if user `bach` has registered</a> works with HEAD and GET methods (has CORS enabled for all origins)</li>
  <li><a href='/register'>The endpoint for user registration</a> works with POST method</li>
  </ul>
  ''', 200

@app.route('/user/<username>', methods=['GET','OPTIONS','HEAD'])
def get(username):
  response = make_response('', 404)
  response.headers["Access-Control-Allow-Origin"] = "*"
  response.headers["Access-Control-Allow-Headers"] = "Content-Type"

  if username in users:
    response.body = json.dumps(users[username])
    response.status_code = 200

  return response

@app.route('/register', methods=['POST'])
def register():
  errors = []
  user = {}
  files= request.files
  data = request.form
  fields = ('firstname', 'lastname', 'password', 'birthdate', 'login', 'pesel', 'sex')
  for field in fields:
    if field not in data:
      errors.append("No '" + field + "' in data")
    elif not valid(field, data[field]):
      errors.append("Field '" + field + "' is invalid: " + requirements(field))
    else:
      user[field] = data[field]

  if len(files) == 0 or 'photo' not in files:
    errors.append("No 'photo' provided: are you sure the form encoding type is correct?")
  else:
    user['photo'] = files['photo'].filename

  login = user.get('login')
  if login in users:
    errors.append("User '{}' already registered".format(login))
 
  if login is None or len(errors) > 0:
    return "<ul><li>" + "</li>\n<li>".join(errors) + "</li></ul>", 400

  users[login] = user
  save_users()
  return json.dumps(user), 201

PL = 'ĄĆĘŁŃÓŚŹŻ'
pl = 'ąćęłńóśźż'
def valid(field, value):
  if field == 'firstname':
    return re.compile(f'[A-Z{PL}][a-z{pl}]+').match(value)
  if field == 'lastname':
    return re.compile(f'[A-Z{PL}][a-z{pl}]+').match(value)
  if field == 'password':
    return re.compile('[A-Za-z]{8,}').match(value)
  if field == 'birthdate':
    try:
      YYYYMMDD = '%Y-%m-%d'
      d = dt.strptime(value, YYYYMMDD)
      return d.year >= 1900
    except ValueError:
      return False
  if field == 'login':
    return re.compile('[a-z]{3,12}').match(value)
  if field == 'pesel':
    if len(value) != 11:
      return False
    wk, w = 0, [1,3,7,9]
    for i in range(10):
      wk = (wk + int(value[i])*w[i % 4]) % 10
    k = (10 - wk) % 10
    return int(value[10]) == k 
  if field == 'sex':
    return value in ('M', 'F')
  if field == 'photo':
    return True
  return False
  
def save_users():
  with open('/tmp/users.pkl', 'wb') as f:
    HIGHEST_PROTOCOL_PRIORITY = -1
    pickle.dump(users, f)
    app.logger.warning("Saved {} users".format(len(users)))

def load_users():
  save_users()
  with open('/tmp/users.pkl', 'rb') as f:
    users = pickle.load(f)
    app.logger.warning("Loaded {} users".format(len(users)))

def requirements(field):
  if field == 'firstname':
    return 'must begin with [A-Z] or a Polish character, followed by at least one lowercase [a-z] or a Polish character.'
  if field == 'lastname':
    return 'must begin with [A-Z] or a Polish character, followed by at least one lowercase [a-z] or a Polish character.'
  if field == 'password':
    return 'must be at least 8 characters of [A-Za-z]'
  if field == 'birthdate':
    return 'must be in format YYYY-MM-DD and year must be >= 1900'
  if field == 'login':
    return 'must be [a-z]{3,12}'
  if field == 'pesel':
    return 'must consist of 11 digits with correct checksum'
  if field == 'sex':
    return 'must be either "M" (male) or "F" (female)'
  if field == 'photo':
    return 'must be present'
  return '(no requirements)'
