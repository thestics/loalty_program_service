from flask import request, jsonify

from exts import db
from models.event import Events


def create_event():
    """
    JSON data with keys
        "user_card_id", "client_card_id" - string value
        "sum" - float value
    """
    try:
        p_sum = float(request.json['sum'])

        if p_sum <= 0:
            return jsonify(dict(status='error', error="Negative or zero purchase")), 400

        event = Events.from_card_id(
            request.json['user_card_id'],
            request.json['client_card_id'],
            p_sum
        )

        db.session.add(event)
        db.session.commit()
        return jsonify(dict(status='success')), 200
    except AttributeError:
        return jsonify(dict(status='error', error="User or client with given id not found")), 400
    except Exception as e:
        return jsonify(dict(status='error', error=str(e))), 400
