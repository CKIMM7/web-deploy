from flask import Blueprint, jsonify, request

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return jsonify('Route / says hello'), 200
