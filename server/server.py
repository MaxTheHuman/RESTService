from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient

from flask.json import JSONEncoder
from bson import json_util

# define a custom encoder point to the json_util provided by pymongo (or its dependency bson)
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj): return json_util.default(obj)

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

api = Api(app)

client = MongoClient('mongodb', 27017)
db = client.tododb

# items = {
#     # 0: {"name": "default product", "category": 0}
# }
next_id = 1


class OnlineStore(Resource):

    def get(self):
        
        view_items_info = request.get_json()

        if view_items_info is None:
            _items = db.tododb.find()
            items = [item for item in _items]
            return jsonify(items)
        
        else:
            view_item_id = view_items_info["id"]
            searched_item = db.tododb.find_one({"_id": view_item_id})
            return jsonify(searched_item)

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
