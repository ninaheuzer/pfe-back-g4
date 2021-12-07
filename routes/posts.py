from flask import jsonify, abort, request, Blueprint

import db.couchDB_service as db

posts_route = Blueprint('posts-route', __name__)


def get_blueprint():
    """Return the blueprint for the main app module"""
    return posts_route


@posts_route.route('/', methods=['GET'])
def get_all():
    category = request.args.get('category')
    campus = request.args.get('campus')
    print(category, campus)
    if campus and category:
        return jsonify(db.get_post_by_campus_and_category(campus, category))
    elif campus:
        return jsonify(db.get_post_by_campus(campus))
    elif category:
        return jsonify(db.get_post_by_category(category))

    return jsonify(db.get_posts())


@posts_route.route('/pending', methods=['GET'])
def get_all_pending():
    return jsonify(db.get_pending_posts())


@posts_route.route('/<string:_id>', methods=['GET'])
def get_with_id(_id):
    # code ...
    return jsonify(db.get_post_by_id(_id))


@posts_route.route('/', methods=['POST'])
def add_one():
    if not request.get_json():
        abort(400)

    data = request.get_json(force=True)

    return jsonify(db.create_post())


@posts_route.route('/<string:_id>', methods=['DELETE'])
def delete_one(_id):
    # code ...
    return jsonify(db.delete_post(_id))


@posts_route.route('/<string:_id>', methods=['PUT'])
def edit_one(_id):
    if not request.get_json():
        abort(400)

    data = request.get_json(force=True)

    return jsonify(db.edit_post())