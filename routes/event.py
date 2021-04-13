from flask import request, jsonify

from __main__ import app, db
from models.event import Events


@app.route('/api/create_event', methods=['PUT'])
def create_event():
    """
    JSON data with keys
        "user_card_id", "client_card_id" - string value
        "sum" - float value
    """
    try:
        event = Events.from_card_id(
            request.json['user_card_id'],
            request.json['client_card_id'],
            float(request.json['sum'])
        )
        db.session.add(event)
        db.session.commit()
        return jsonify(dict(status='success')), 200
    except AttributeError:
        return jsonify(dict(status='error', error="User or client with given id not found")), 400
    except Exception as e:
        return jsonify(dict(status='error', error=str(e))), 400
