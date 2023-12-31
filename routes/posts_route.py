from flask import jsonify, abort, request, Blueprint

import services.posts_service as service
from models.Post import Post, PostStates
from services.addresses_service import get_address_by_id
from services.categories_service import get_category_by_id
from services.users_service import get_user_by_id
from utils.utils import admin_token_required, token_required, token_welcome, upload_files, remove_file

posts_route = Blueprint('posts-route', __name__)


def get_blueprint():
    """Return the blueprint for the main app module"""
    return posts_route


@posts_route.route('/', methods=['GET'])
def get_all():
    category = request.args.get('category')
    campus = request.args.get('campus')
    order = request.args.get('order', None)
    if campus and category:
        return jsonify(service.get_posts_by_campus_and_category(campus, category, order))
    elif campus:
        return jsonify(service.get_posts_by_campus(campus, order))
    elif category:
        return jsonify(service.get_posts_by_category(category, order))

    return jsonify(service.get_posts(order))


@posts_route.route('/closedpostsamount', methods=['GET'])
def get_closed_posts_amount():
    return jsonify(service.get_closed_posts_amount())


@posts_route.route('/withoutfavourites', methods=['GET'])
@token_welcome
def get_without_favourites(_current_user):
    if _current_user:
        return jsonify(
            [post for post in service.get_posts_as_dicts() if post['_id'] not in _current_user["favorites"]])
    else:
        return jsonify([post for post in service.get_posts()])


@posts_route.route('/closed', methods=['GET'])
@admin_token_required
def get_closed(_current_user):
    return jsonify(service.get_closed_posts())


@posts_route.route('/pending', methods=['GET'])
@admin_token_required
def get_pending(_current_user):
    return jsonify(service.get_pending_posts())


@posts_route.route('/rejected', methods=['GET'])
@admin_token_required
def get_rejected(_current_user):
    return jsonify(service.get_rejected_posts())


@posts_route.route('/myposts', methods=['GET'])
@token_required
def get_all_my_posts(_current_user):
    return jsonify(service.get_all_my_posts(_current_user['_id']))


@posts_route.route('/<string:_id>', methods=['GET'])
@token_welcome
def get_with_id(_current_user, _id):
    post = service.get_post_by_id(_id)
    if post:
        if post.state != PostStates.APPROVED.value:
            if _current_user:
                if _current_user['is_admin'] or (post['seller_id'] == _current_user['_id']):
                    return jsonify(post.get_data())
            else:
                return abort(401, "Vous n'avez pas accès à cette annonce.")
        else:
            return jsonify(post.get_data())

    return abort(404, "Cette annonce n'existe pas/plus.")


@posts_route.route('/favourites', methods=['GET'])
@token_required
def get_favourites(_current_user):
    return jsonify(service.get_favourites(_current_user))


@posts_route.route('/<string:_id>/fulldetails', methods=['GET'])
@token_welcome
def get_full_details(_current_user, _id):
    post = service.get_post_by_id(_id)
    seller = get_user_by_id(post['seller_id'])
    addresses = [get_address_by_id(add).get_data() for add in post['places']]

    full_details_logged_in = dict(post=post.get_data(), seller=seller.get_data(), addresses=addresses)
    if not post:
        return abort(404, "Cette annonce n'existe pas/plus.")

    else:
        if post.state != PostStates.APPROVED.value:
            if _current_user:
                if _current_user['is_admin'] or (post['seller_id'] == _current_user['_id']):
                    return jsonify(full_details_logged_in)
            else:
                return abort(401, "Vous n'avez pas accès à cette annonce.")

        else:
            if _current_user:
                return jsonify(full_details_logged_in)
            else:
                del post["seller_id"]
                full_details_logged_off = dict(post=post.get_data(), addresses=addresses)
                return jsonify(full_details_logged_off)


@posts_route.route('/', methods=['POST'])
@token_required
def add_one(_current_user):
    if not request.form:
        abort(400, "La requête est vide")

    data = request.form
    print(data)
    post_nature = data.get('post_nature')
    title = data.get('title')
    description = data.get('description')
    price = 0
    if post_nature == 'À vendre':
        price = data.get('price')
        if float(price) <= 0:
            return abort(401, "Vous ne pouvez pas mettre ce prix-là.")
    places = data.get('places').split(',')
    seller_id = _current_user['_id']
    category_id = data.get('category_id')
    if not post_nature:
        abort(400, "Le champ 'post_nature' doit être présent et non vide")
    if not title:
        abort(400, "Le champ 'title' doit être présent et non vide")
    if not description:
        abort(400, "Le champ 'description' doit être présent et non vide")
    if not isinstance(places, list):
        abort(400, "Le champ 'places' doit être une liste")
    if not seller_id:
        abort(400, "Le champ 'seller_id' doit être présent et non vide")
    if not category_id:
        abort(400, "Le champ 'category_id' doit être présent et non vide")

    files = request.files.getlist("files")
    images, video = upload_files(files)

    post = Post(post_nature=post_nature,
                title=title,
                description=description,
                price=price,
                places=places,
                seller_id=seller_id,
                category_id=category_id,
                images=images,
                video=video
                )

    res = service.create_post(post)
    return jsonify(res) if res else abort(500, "Il y a eu un problème.")


@posts_route.route('/<string:_id>', methods=['DELETE'])
@token_required
def delete_one(_current_user, _id):
    try:
        res = service.delete_post(_id)
    except FileNotFoundError:
        abort(404, "Cette annonce n'existe pas/plus.")
    return jsonify(res)


@posts_route.route('/<string:_id>', methods=['PUT'])
@token_required
def edit_one(_current_user, _id):
    if not request.json:
        abort(400, "La requête est vide")

    data = request.json
    post = service.get_post_by_id(_id)
    if post['seller_id'] != _current_user['_id'] and not _current_user['is_admin']:
        abort(401,
              "Vous ne pouvez pas modifier cette annonce.")

    post_nature = data.get('post_nature', post['post_nature'])
    title = data.get('title', post['title'])
    description = data.get('description', post['description'])

    price = 0
    if post_nature != 'À donner':
        price = data.get('price', post['price'])
    places = data.get('places', post['places'])
    category_id = data.get('category_id', post['category_id'])
    images = data.get('images', post['images'])
    video = data.get('video', post['video'])
    if get_category_by_id(category_id):
        post = Post(_id=_id,
                    post_nature=post_nature,
                    title=title,
                    description=description,
                    price=price,
                    places=places,
                    category_id=category_id,
                    images=images,
                    video=video
                    )

    return jsonify(service.edit_post(post, _id))


@posts_route.route('/<string:_id>/stateChange', methods=['POST'])
@admin_token_required
def change_state(_current_user, _id):
    if not request.json:
        abort(400, "La requête est vide")
    data = request.json

    state = data['state']
    if state != PostStates.CLOSED.value and state != PostStates.PENDING.value and \
            state != PostStates.APPROVED.value and state != PostStates.REJECTED.value:
        abort(400,
              f"Les états valides sont {PostStates.PENDING.value}, {PostStates.APPROVED.value}"
              f", {PostStates.REJECTED.value}, et {PostStates.CLOSED.value}")
    return jsonify(service.change_state(_id, state))


@posts_route.route('/<string:_id>/sell', methods=['POST'])
@token_required
def sell_one(_current_user, _id):
    post = service.get_post_by_id(_id)
    if post['seller_id'] != _current_user['_id'] and not _current_user['is_admin']:
        return abort(401,
                     "Vous ne pouvez pas clôturer cette annonce.")

    if post['state'] == PostStates.REJECTED.value:
        return abort(401,
                     "Vous ne pouvez pas clôturer une annonce refusée.")
    return jsonify(service.sell_one(_id))


@posts_route.route('/<string:_id>/file/<string:_id_file>', methods=['DELETE'])
@token_required
def delete_one_file(_current_user, _id, _id_file):
    post = service.get_post_by_id(_id)
    if not post:
        return abort(404, "L'annonce n'existe pas")
    if post['seller_id'] != _current_user['_id'] and not _current_user['is_admin']:
        return abort(401,
                     "Vous ne pouvez pas supprimer d'image pour cette annonce")
    try:
        service.delete_file(post, _id_file)
    except AttributeError as e:
        abort(404, e)

    return jsonify(remove_file(_id_file))
