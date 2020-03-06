from flask import Flask, request, jsonify
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

items = {
    # 0: {"name": "default product", "category": 0}
}
next_id = 1


class OnlineStore(Resource):

    '''
    Function get() is used to view items.
    If no body is passed with the request, respond will be an array of all items stored in shop.
    If json of format {"id": item_id} is passed, respond will contain only information about item
    with given id. At this stage there are no checks that id is valid, i.e. there is an item with
    given id.
    '''
    def get(self):
        view_items_info = request.get_json()
        if view_items_info is None:
            return jsonify(items)
        else:
            view_item_id = view_items_info["id"]
            return jsonify({"id": view_item_id, "info": items[view_item_id]})

        
    '''
    Function post() is used to add items.
    Body of this requests must be of given format:
    {"name": item_name, "category": item_category}
    Result of the function is item added to the store.
    '''
    def post(self):
        global next_id

        new_item_info = request.get_json()
        new_item_name = new_item_info["name"]
        new_item_category = new_item_info["category"]
        new_item = {"name": new_item_name, "category": new_item_category}

        items[next_id] = new_item
        next_id += 1

        return {'item added': {"id": next_id - 1, "info": new_item}}, 201

    '''
    Function put() is used to update items.
    Body of this requests must be of given format:
    {"id": id_of_item_to_update, "name": item_name, "category": item_category}
    Result of the function is item updated with new given values if it existed
    before call, otherwise item with given id and values will be added.
    '''
    def put(self):
        update_item_info = request.get_json()
        update_item_id = update_item_info["id"]
        update_item_name = update_item_info["name"]
        update_item_category = update_item_info["category"]
        update_item = {"name": update_item_name, "category": update_item_category}

        items[update_item_id] = update_item

        return {'item updated': {"id": update_item_id, "info": update_item}}, 202

    '''
    Function delete() is used to delete items.
    Body of this requests must contain json of format {"id": id_of_item_to_delete}
    Result of the function is item deleted from the store.
    At this stage there are no checks that item with given id exists.
    '''
    def delete(self):
        delete_item_info = request.get_json()
        delete_item_id = delete_item_info["id"]
        deleted_item = items.pop(delete_item_id)

        return {'item deleted': {"id": delete_item_id, "info": deleted_item}}, 203


api.add_resource(OnlineStore, '/')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")
