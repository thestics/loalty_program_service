from flask import request, Blueprint

from controllers.pay import PayController
from controllers.get_balance import BalanceController

from models import PartnerLog


blueprint = Blueprint('main', __name__)


@blueprint.route("/", methods=["GET"])
def hello_world():
    return 'hello world'


@blueprint.route("/pay_registration", methods=["POST"])
def pay_registration():
    return PayController(request, db_logger=PartnerLog(log_type=LogType.Withdraw)).call()


@blueprint.route("/generate_new_address", methods=["POST"])
def generate_new_address():
    return InvoiceController(request, db_logger=PartnerLog(log_type=LogType.Invoice)).call()
