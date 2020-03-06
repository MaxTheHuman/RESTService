from flask import Flask, request, jsonify
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

items = {
    # 0: {"name": "default product", "category": 0}
}
next_id = 1


class OnlineStore(Resource):

    def get(self):
        view_items_info = request.get_json()
        if view_items_info is None:
            return jsonify(items)
        else:
            view_item_id = view_items_info["id"]
            return jsonify({"id": view_item_id, "info": items[view_item_id]})

    def post(self):
        global next_id

        new_item_info = request.get_json()
        new_item_name = new_item_info["name"]
        new_item_category = new_item_info["category"]
        new_item = {"name": new_item_name, "category": new_item_category}

        items[next_id] = new_item
        next_id += 1

        return {'item added': {"id": next_id - 1, "info": new_item}}, 201

    def put(self):
        update_item_info = request.get_json()
        update_item_id = update_item_info["id"]
        update_item_name = update_item_info["name"]
        update_item_category = update_item_info["category"]
        update_item = {"name": update_item_name, "category": update_item_category}

        items[update_item_id] = update_item

        return {'item updated': {"id": update_item_id, "info": update_item}}, 202

    def delete(self):
        delete_item_info = request.get_json()
        delete_item_id = delete_item_info["id"]
        deleted_item = items.pop(delete_item_id)

        return {'item deleted': {"id": delete_item_id, "info": deleted_item}}, 203


api.add_resource(OnlineStore, '/')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")
