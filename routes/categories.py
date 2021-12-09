import flask
from flask import jsonify, abort, request, Blueprint

import services.categories_service as service
from routes.authentication import admin_token_required

categories_route = Blueprint('categories-route', __name__)


def get_blueprint():
    """Return the blueprint for the main app module"""
    return categories_route


@categories_route.route('/', methods=['GET'])
def get_all():
    return jsonify(service.get_categories())


@categories_route.route('/<string:_id>', methods=['GET'])
def get_one(_id):
    category = service.get_category_by_id(_id)
    return jsonify(category.get_data()) if category else flask.abort(404, "Reference not found")


@categories_route.route('/', methods=['POST'])
@admin_token_required
def create_one(_current_user):
    if not request.json:
        abort(400, "The payload is empty")

    data = request.json

    if 'name' not in data:  # No data
        abort(400, "The payload need a field 'name'")

    if not data['name']:  # Empty data
        abort(400, "The field 'name' should not be empty")

    if 'parent' not in data:  # No data
        parent = None
    else:
        parent = data['parent']

    if 'sub_categories' not in data:  # No data
        sub_categories = []
    else:
        sub_categories = data['sub_categories'] if isinstance(data['sub_categories'], list) else []

    try:
        res = service.create_category(data['name'], parent, sub_categories)
    except AttributeError as e:
        abort(400, e)
    return jsonify(res)


@categories_route.route('/<string:_id>', methods=['DELETE'])
@admin_token_required
def delete_one(_current_user, _id):
    try:
        res = service.delete_category(_id)
    except AttributeError:
        abort(404, "Category not found")
    return jsonify(res)


@categories_route.route('/<string:_id>', methods=['PUT'])
@admin_token_required
def edit_one(_current_user, _id):
    if not request.json:
        abort(400, "The payload is empty")

    data = request.json
    if 'name' not in data:
        abort(400, "The payload need a field 'name'")
    if not data['name']:  # Empty data
        abort(400, "The field 'name' should not be empty")
    if 'parent' not in data:
        abort(400, "The payload need a field 'parent'")
    if 'sub_categories' not in data:
        abort(400, "The payload need a field 'sub_categories'")
    return jsonify(service.edit_category(_id, data['name'], data['parent'], data['sub_categories']))
