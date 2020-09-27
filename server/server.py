from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient

from flask.json import JSONEncoder
from bson import json_util

import jwt
import datetime

from functools import wraps

# define a custom encoder point to the json_util provided by pymongo (or its dependency bson)
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj): return json_util.default(obj)

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

api = Api(app)

app.config['SECRET_KEY'] = 'k43enw395xlaj2AO_29dk'
app.config['REFRESH_SECRET_KEY'] = 'l39dke.083nk=5430mfs'
app.config['TOKEN_EXP_TIME'] = 15
app.config['REFRESH_TOKEN_EXP_TIME'] = 4 * 60


client = MongoClient('mongodb', 27017)

# db_to_drop = (client.database_names())[0]
# client.drop_database(db_to_drop)

db = client.tododb

# items = {
#     {"_id": 1, "name": "default product", "category": 0}
# }

next_id = 1

item_with_max_id = db.tododb.find().sort([("_id", -1)]).limit(1)
for helper_item in item_with_max_id:
    next_id = int(str(helper_item["_id"])) + 1


@app.route('/debug')
def debug():
    _items_with_max_id = db.tododb.find().sort([("_id", -1)]).limit(1)
    items_with_max_id = [item for item in _items_with_max_id]
    arr_length = len(items_with_max_id)
    arr_type = type(items_with_max_id)
    _items = db.tododb.find()
    items = [item for item in _items]
    return jsonify({"next_id": next_id,
        "items_with_max_id": items_with_max_id,
        "items": items})


@app.route('/register', methods=['POST'])
def register():
    global next_id
    login_info = request.get_json()

    username = login_info["username"]
    if not username:
            response = jsonify({'message': 'Username is missing'})
            response.status_code = 403
            return response

    password = login_info["password"]
    if not password:
            response = jsonify({'message': 'Password is missing'})
            response.status_code = 403
            return response

    searched_user = db.tododb.find_one({"username": username})
    if searched_user == None:
        new_user = {
                "_id": next_id,
                "username": username,
                "password": password,
                "token_pair_id": 0
            }
        db.tododb.insert_one(new_user)
        next_id += 1
        return jsonify({'message': 'User registered'})
    else:
        return jsonify({'message': 'User with this username is already registered'}), 401

@app.route('/auth', methods=['POST'])
def auth():
    login_info = request.get_json()

    username = login_info["username"]
    if not username:
            response = jsonify({'message': 'Username is missing'})
            response.status_code = 403
            return response

    password = login_info["password"]
    if not password:
            response = jsonify({'message': 'Password is missing'})
            response.status_code = 403
            return response
    
    searched_user = db.tododb.find_one({"username": username})
    if searched_user == None:
        return jsonify({'message': 'Register first'}), 402
    else:
        if password != searched_user["password"]:
            return jsonify({'message': 'Incorrect password'}), 401

    # if we get here we logged in

    curr_token_pair_id = searched_user['token_pair_id']
    db.tododb.update_one({"username": username}, {'$inc': {'token_pair_id': 1}})

    token = jwt.encode(
            {
            'user': username,
            'exp': datetime.datetime.utcnow() +
                    datetime.timedelta(minutes=app.config['TOKEN_EXP_TIME']),
            'token_pair_id': curr_token_pair_id + 1
            },
            app.config['SECRET_KEY']
        )
    refresh_token = jwt.encode(
            {
                'user': username,
                'exp': datetime.datetime.utcnow() +
                        datetime.timedelta(minutes=app.config['REFRESH_TOKEN_EXP_TIME']),
                'token_pair_id': curr_token_pair_id + 1
            },
            app.config['REFRESH_SECRET_KEY']
        )
    return jsonify(
        {
            'token': token.decode('UTF-8'),
            'refresh token': refresh_token.decode('UTF-8'),
        })

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_info = request.get_json()
        
        if 'username' in token_info:
            username = token_info['username']
        else:
            response = jsonify({'message': 'Username is missing'})
            response.status_code = 403
            return response

        if 'token' in token_info:
            token = token_info['token']
        else:
            response = jsonify({'message': 'Token is missing'})
            response.status_code = 403
            return response
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])

        except:
            response = jsonify({'message': 'Token is invalid. Try to refresh.'})
            response.status_code = 403
            return response

        searched_user = db.tododb.find_one({'username': username})
        curr_token_pair_id = searched_user['token_pair_id']

        if username != data['user']:
            response = jsonify({'message': 'Token username is incorrect.'})
            response.status_code = 403
            return response
        elif curr_token_pair_id > data['token_pair_id']:
            response = jsonify({'message': 'Token was refreshed.'})
            response.status_code = 403
            return response
        elif curr_token_pair_id < data['token_pair_id']:
            response = jsonify({'message': 'Token is invalid.'})
            response.status_code = 403
            return response

        return f(*args, **kwargs)

    return decorated

@app.route('/refresh_token', methods=['POST'])
def refresh_token():
    user_info = request.get_json()
    if 'username' in user_info:
        username = user_info["username"]
    else:
        response = jsonify({'message': 'Username is missing'})
        response.status_code = 403
        return response

    if 'refresh_token' in user_info:
        refresh_token = user_info["refresh_token"]
    else:
        response = jsonify({'message': 'Refresh token is missing'})
        response.status_code = 403
        return response

    searched_user = db.tododb.find_one({"username": username})

    try:
        data = jwt.decode(refresh_token, app.config['REFRESH_SECRET_KEY'])
    except:
        response = jsonify({'message': 'Refresh token is invalid. Reauthorize.'})
        response.status_code = 403
        return response

    curr_token_pair_id = searched_user['token_pair_id']
    if data['token_pair_id'] < curr_token_pair_id:
        response = jsonify({'message': 'Refresh token has been already used'})
        response.status_code = 403
        return response
    elif data['token_pair_id'] > curr_token_pair_id:
        response = jsonify({'message': 'Refresh token is invalid.'})
        response.status_code = 403
        return response

    #if we get here refresh token is valid

    db.tododb.update_one({"username": username}, {'$inc': {'token_pair_id': 1}})

    token = jwt.encode(
            {
            'user': username,
            'exp': datetime.datetime.utcnow() +
                    datetime.timedelta(minutes=app.config['TOKEN_EXP_TIME']),
            'token_pair_id': curr_token_pair_id + 1
            },
            app.config['SECRET_KEY']
        )
    refresh_token = jwt.encode(
            {
                'user': username,
                'exp': datetime.datetime.utcnow() +
                        datetime.timedelta(minutes=app.config['REFRESH_TOKEN_EXP_TIME']),
                'token_pair_id': curr_token_pair_id + 1
            },
            app.config['REFRESH_SECRET_KEY']
        )

    return jsonify(
        {
            'token': token.decode('UTF-8'),
            'refresh_token': refresh_token.decode('UTF-8')
        })

@app.route('/validate_token', methods=['POST'])
@token_required
def validate_token():
    
    return jsonify({'message': 'Token is valid'})

class OnlineStore(Resource):

    method_decorators = [token_required]

    def get(self):
        
        view_items_info = request.get_json()

        if 'id' in view_items_info:
            view_item_id = view_items_info['id']
            searched_item = db.tododb.find_one({"_id": view_item_id})
            if searched_item == None:
                return {"There is no item with id" : view_item_id}
            return jsonify(searched_item)

        else:
            _items = db.tododb.find({"category": {"$exists": True}})
            items = [item for item in _items]
            return jsonify(items)

    def post(self):
        global next_id

        new_item_info = request.get_json()
        new_item_name = new_item_info["name"]
        new_item_category = new_item_info["category"]
        new_item = {
                "_id": next_id,
                "name": new_item_name,
                "category": new_item_category
            }

        db.tododb.insert_one(new_item)
        next_id += 1

        return {
            'item added':
                {
                "id": next_id - 1,
                "info":
                    {
                    "name": new_item_name,
                    "category": new_item_category
                    }
                }
            }, 201


    def put(self):
        update_item_info = request.get_json()
        update_item_id = update_item_info["id"]
        update_item_name = update_item_info["name"]
        update_item_category = update_item_info["category"]
        update_item = {"name": update_item_name, "category": update_item_category}

        updatequery = { "_id": update_item_id }
        newvalues = { "$set": update_item }

        db.tododb.update_one(updatequery, newvalues)

        return {'item updated': {"id": update_item_id, "info": update_item}}, 202

    def delete(self):
        delete_item_info = request.get_json()
        delete_item_id = delete_item_info["id"]
        
        deletequery = { "_id": delete_item_id }
        deleted_item = db.tododb.find_one(deletequery)
        db.tododb.delete_one(deletequery) 

        return {'item deleted': {"id": delete_item_id, "info": deleted_item}}, 203

api.add_resource(OnlineStore, '/')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")
