import io
import os
import qrcode
import json
import requests
import urllib.parse
from secrets import token_urlsafe
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

from flask_sqlalchemy import SQLAlchemy

from flask import (
    Flask,
    request,
    abort,
    redirect,
    Response,
    url_for,
    render_template,
    jsonify,
)
from flask_restful import Resource, reqparse

from notification import notificator


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"
#####################################################################################################

# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://"
app.config["SQLALCHEMY_DATABASE_URI"] = "{}".format(os.getenv("DATABASE_URL"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "some-secret-string"

db = SQLAlchemy(app)


@app.before_first_request
def create_tables():
    db.create_all()


#####################################################################################################
class XpubKeys(db.Model):
    __tablename__ = "xpubs"

    id = db.Column(db.Integer, primary_key=True)
    wallet = db.Column(db.String())
    xpub = db.Column(db.String())
    used = db.Column(db.String())

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_on_db(self):
        db.session.commit()

    @classmethod
    def get_xpubs(cls):
        def to_json(x):
            return {"wallet": x.wallet, "xpub": x.xpub, "used": x.used}

        return {"xpubs": list(map(lambda x: to_json(x), XpubKeys.query.all()))}

    @classmethod
    def find_by_xpub(cls, xpub):
        return cls.query.filter_by(xpub=xpub).first()


#####################################################################################################
# log
# @app.before_request
# def log_request_info():
#    app.logger.debug('Headers: %s', request.headers)
#    app.logger.debug('Body: %s', request.get_data())
#####################################################################################################
def get_billig_url():
    url_1 = "https://axe-bill-app.axe-dev.com"
    url_2 = "https://axe-bill-app.herokuapp.com"

    try:
        if requests.get(url_1).status_code == 200:
            billing_api_url = url_1
            return billing_api_url

    except requests.exceptions.RequestException:
        if requests.get(url_2).status_code == 200:
            billing_api_url = url_2
            return billing_api_url


def login_on_billing_like_user(bot_id_from_form):
    billing_api_url = get_billig_url()
    billing_api_login_url = "/login"
    endpoint_for_login = billing_api_url + billing_api_login_url
    login_data_json = {"bot_id": bot_id_from_form}

    server_answer = requests.post(
        endpoint_for_login, json=login_data_json, verify=True
    ).json()

    return server_answer


def login_on_billing_like_bot(bot_id_from_form):

    secret_for_bot_login = "Jrp-_Xipu6xFdYrp_9RDK5Ur3wDUI16J0nc0spbRvE0="

    billing_api_url = get_billig_url()
    billing_api_login_url = "/botlogin"
    endpoint_for_login = billing_api_url + billing_api_login_url
    login_data_json = {
        "bot_id": bot_id_from_form,
        "secret_for_bot_login": secret_for_bot_login,
    }

    server_answer = requests.post(
        endpoint_for_login, json=login_data_json, verify=True
    ).json()

    return server_answer


def flush_bot_hash(bot_id_from_form):

    secret_for_flush_bot_hash = "qsh-pPXIvoK1L6sCTgI3JyyOw3U5GLcUSfCTS2sz3Vc="

    auth_token = login_on_billing_like_bot(bot_id_from_form)["access_token"]

    billing_api_url = get_billig_url()
    billing_api_write_licence_url = "/flushhash"
    endpoint_for_write_licence_time = billing_api_url + billing_api_write_licence_url

    auth_token_access_bearer = "Bearer " + auth_token
    headers_access = {"Authorization": auth_token_access_bearer}
    bot_id_dict = {
        "bot_id": bot_id_from_form,
        "bot_hash": None,
        "secret_for_flush_bot_hash": secret_for_flush_bot_hash,
    }

    x = requests.post(
        endpoint_for_write_licence_time,
        json=bot_id_dict,
        headers=headers_access,
        verify=True,
    ).json()
    return x


def write_bot_id_and_url_safe_to_db(bot_id_from_form, url_safe):

    secret_for_save_payment = "59rjZ73apdw833ucC2mJNpmX5gvrYmLPHHx-OYh9C3I="

    auth_token = login_on_billing_like_bot(bot_id_from_form)["access_token"]

    billing_api_url = get_billig_url()
    billing_api_payment = "/payments"
    endpoint_for_write_payment = billing_api_url + billing_api_payment

    auth_token_access_bearer = "Bearer " + auth_token
    headers_access = {"Authorization": auth_token_access_bearer}
    payment_dict = {
        "bot_id": bot_id_from_form,
        "url_safe": url_safe,
        "secret_for_save_payment": secret_for_save_payment,
    }

    x = requests.post(
        endpoint_for_write_payment,
        json=payment_dict,
        headers=headers_access,
        verify=True,
    ).json()

    return url_safe


def update_payment_data(
    bot_id_from_form,
    url_safe,
    transaction_hash,
    btc_address,
    value,
    callback_provider,
    currency,
):

    secret_for_update_payment = "jFjoALtajZzA6ZFXw_Yw7kRDbNNUuQa3_MzPL2d8BKY="

    auth_token = login_on_billing_like_bot(bot_id_from_form)["access_token"]

    billing_api_url = get_billig_url()
    billing_api_update_payment = "/updatepayment"
    endpoint_for_update_payment = billing_api_url + billing_api_update_payment

    auth_token_access_bearer = "Bearer " + auth_token
    headers_access = {"Authorization": auth_token_access_bearer}
    payment_update_dict = {
        "url_safe": url_safe,
        "transaction_hash": transaction_hash,
        "address": btc_address,
        "value": value,
        "callback_provider": callback_provider,
        "currency": currency,
        "secret_for_update_payment": secret_for_update_payment,
    }

    x = requests.post(
        endpoint_for_update_payment,
        json=payment_update_dict,
        headers=headers_access,
        verify=True,
    ).json()
    return x


def get_amount_for_one_month():
    one_month_cost = requests.get(
        "https://blockchain.info/tobtc?currency=USD&value=15"
    ).json()  # $15

    return one_month_cost


def get_xpub():
    xpub = XpubKeys.get_xpubs()

    try:
        t = []
        for i in xpub["xpubs"]:
            if i["used"] == None:
                print(i["xpub"])
                t.append(i["xpub"])

        # notificator(t[0])
        return t[0]
    except Exception as e:
        # notificator(str(e))
        notificator("All not used xPub's ended, put more to psql")


def set_used_to_xpub(xpub):

    try:
        xpub_to_set = XpubKeys.find_by_xpub(xpub)
        xpub_to_set.used = "yes"
        xpub_to_set.update_on_db()

        notificator("{} is used".format(xpub))
    except Exception as e:
        notificator(str(e))


def gen_payment(bot_id_from_form, url_safe, xpub):

    api_url = "https://api.blockchain.info/v2/receive"
    key = "blockchain_API_KEY"
    # xpub = "XPUB"

    # DON'T forget add /callback/ to URL
    callback = "https://axe-bot-payments.herokuapp.com/callback/{}/{}".format(
        bot_id_from_form, url_safe
    )

    get_dict_for_payment = requests.get(
        "{}?xpub={}&callback={}&key={}".format(
            api_url, xpub, urllib.parse.quote_plus(callback), key
        )
    ).json()

    return get_dict_for_payment


def get_url_safe_and_value_and_bot_id_from_bill(bot_id, url_safe):

    auth_token = login_on_billing_like_bot(bot_id)["access_token"]

    billing_api_url = get_billig_url()
    billing_api_getpayment = "/getpayment/"
    endpoint_for_getpayment = billing_api_url + billing_api_getpayment + url_safe

    auth_token_access_bearer = "Bearer " + auth_token
    headers_access = {"Authorization": auth_token_access_bearer}

    x = requests.get(
        endpoint_for_getpayment, headers=headers_access, verify=True
    ).json()
    return x


def gen_url_safe():
    url_safe = token_urlsafe(10)
    return url_safe


def check_login_data(login_data):
    login_data = str(login_data)
    if len(login_data) != 10:
        return "error"
    else:
        return login_data


def create_licence_time(bot_id_from_form):

    secret_for_encruption_licence_time = "CAQRzbEvyDxfy-h3Nk-fURRWlzuzneygxSCMLfv2vsY="

    licence_time_on_billing = login_on_billing_like_user(bot_id_from_form)[
        "licence_valid_until"
    ]

    if (
        login_on_billing_like_user(bot_id_from_form)["licence_valid_until"]
        != "licence doesn't exist"
    ):
        if datetime.utcnow() < datetime.fromisoformat(licence_time_on_billing):
            # add 1 month to exist time, if licence valid
            x = datetime.fromisoformat(licence_time_on_billing) + timedelta(
                1 * 365 / 12
            )  # 1 Month
            # x = datetime.fromisoformat(licence_time_on_billing) + timedelta(minutes=10080) # 7 days
            # x = datetime.fromisoformat(licence_time_on_billing) + timedelta(minutes=60) # 1 hour
    else:
        # if licence None or new
        x = datetime.utcnow() + timedelta(1 * 365 / 12)  # 1 Month
        # x = datetime.utcnow() + timedelta(minutes=10080) # 7 days
        # x = datetime.utcnow() + timedelta(minutes=60) # 1 hour

    x = str(x)
    x = x.encode()

    key = secret_for_encruption_licence_time + bot_id_from_form

    f = Fernet(key)
    encrypt_value = f.encrypt(x)
    encrypt_value = encrypt_value.decode()

    return encrypt_value


def write_licence_time(bot_id_from_form, bot_licence):

    secret_for_write_bot_licence = "JqeL56RwnbVgmrloN1Du-FkF0wAVSBZ6i55v5rN0eZU="

    auth_token = login_on_billing_like_bot(bot_id_from_form)["access_token"]

    billing_api_url = "https://axe-bill-app.herokuapp.com"
    billing_api_write_licence_url = "/writelicencetime"
    endpoint_for_write_licence_time = billing_api_url + billing_api_write_licence_url

    auth_token_access_bearer = "Bearer " + auth_token
    headers_access = {"Authorization": auth_token_access_bearer}
    bot_id_dict = {
        "bot_id": bot_id_from_form,
        "bot_licence": bot_licence,
        "secret_for_write_bot_licence": secret_for_write_bot_licence,
    }

    x = requests.post(
        endpoint_for_write_licence_time,
        json=bot_id_dict,
        headers=headers_access,
        verify=True,
    ).json()

    return x


#####################################################################################################
@app.route("/")
def index():
    return jsonify({"message": "Hello, World!"})


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/callback/<string:bot_id>/<string:url_safe>")
def callback(bot_id, url_safe):

    try:

        parser = reqparse.RequestParser()

        parser.add_argument("transaction_hash", help="", required=False)
        parser.add_argument("address", help="", required=False)
        parser.add_argument("confirmations", help="", required=False)
        parser.add_argument("value", help="", required=False)

        data = parser.parse_args()

        transaction_hash_from_callback = data["transaction_hash"]
        address_from_callback = data["address"]
        confirmations_from_callback = data["confirmations"]
        value_from_callback = data["value"]
        callback_provider = "blockchain.com"

        bot_id_from_bill = get_url_safe_and_value_and_bot_id_from_bill(
            bot_id, url_safe
        )["payments"][0]["bot_id"]
        url_safe_from_bill = get_url_safe_and_value_and_bot_id_from_bill(
            bot_id, url_safe
        )["payments"][0]["url_safe"]
        value_from_bill = get_url_safe_and_value_and_bot_id_from_bill(bot_id, url_safe)[
            "payments"
        ][0]["value"]
        transaction_hash_from_bill = get_url_safe_and_value_and_bot_id_from_bill(
            bot_id, url_safe
        )["payments"][0]["transaction_hash"]

        # from callback_provider value will be in satoshi !
        # satosh to btc 291300 / 100000000
        value_from_callback_btc = float(value_from_callback) / 100000000

        if (
            bot_id == bot_id_from_bill
            and url_safe == url_safe_from_bill
            and transaction_hash_from_bill == None
            and round(float(value_from_callback_btc), 8)
            == round(float(value_from_bill), 8)
            and int(confirmations_from_callback) >= 2
        ):
            write_licence_time(bot_id, create_licence_time(bot_id))
            update_payment_data(
                bot_id,
                url_safe,
                transaction_hash_from_callback,
                None,
                None,
                callback_provider,
                None,
            )

            # Callback domains which appear dead or never return the "*ok*" response may be blocked from the service.
            # https://www.blockchain.com/api/api_receive
            return "*ok*", 200

        else:
            # return jsonify(data)
            return "*ok*", 200

    except:
        return "not *ok*", 405
    # except Exception as e:
    # return str(e)


@app.route("/make-payment", methods=["GET", "POST"])
def make_payment():
    if request.method == "POST" and request.form["bot_id"] != None:
        bot_id_from_form = request.form["bot_id"]

        if check_login_data(bot_id_from_form) != "error":
            billing_api_answer = login_on_billing_like_user(bot_id_from_form)
            if "exist" not in billing_api_answer["message"]:

                url_safe = write_bot_id_and_url_safe_to_db(
                    bot_id_from_form, gen_url_safe()
                )

                xpub = get_xpub()

                btc_address_dict = gen_payment(bot_id_from_form, url_safe, xpub)
                if "message" not in btc_address_dict:
                    btc_address = btc_address_dict["address"]
                    value = get_amount_for_one_month()

                    update_payment_data(
                        bot_id_from_form,
                        url_safe,
                        None,
                        btc_address,
                        value,
                        None,
                        "BTC",
                    )
                    # return jsonify({"btc_address": btc_address, "btc_value": value})
                    # return "Send to " + str(btc_address) + " " + str(value) + " BTC"

                    # qr = qrcode.make(btc_address)
                    # qr_img = qr.get_image()
                    # heroku don't allow save file to it's disc, therefore we will don't save and show qr to user

                    return render_template(
                        "payment.html", btc_address=btc_address, value=value
                    )

                else:

                    set_used_to_xpub(xpub)

                    notificator(btc_address_dict)
                    # return jsonify(btc_address_dict)
                    error = "There is no BTC wallet address, try again later ... or pay with ETH ...."
                    return render_template("error.html", error=error)

            else:
                # return "id not found"
                error = "id not found"
                return render_template("error.html", error=error)

        else:
            return abort(401)
            # return redirect(url_for("login"))
    else:
        return render_template("make_payment.html")


@app.route("/flush-bot-hash", methods=["GET", "POST"])
def flush_hash():
    if request.method == "POST" and request.form["bot_id"] != None:
        bot_id_from_form = request.form["bot_id"]

        if check_login_data(bot_id_from_form) != "error":
            billing_api_answer = login_on_billing_like_user(bot_id_from_form)
            if "exist" not in billing_api_answer["message"]:

                return flush_bot_hash(bot_id_from_form)
            else:
                # return "id not found"
                error = "id not found"
                return render_template("error.html", error=error)

        else:
            return abort(401)
            # return redirect(url_for("login"))
    else:
        return render_template("flush_bot_hash.html")


@app.route("/licence-info", methods=["GET", "POST"])
def licence_info():
    if request.method == "POST" and request.form["bot_id"] != None:
        bot_id_from_form = request.form["bot_id"]

        if check_login_data(bot_id_from_form) != "error":
            billing_api_answer = login_on_billing_like_user(bot_id_from_form)
            if "exist" not in billing_api_answer["message"]:
                if "exist" not in billing_api_answer["licence_valid_until"]:
                    # return "Licence valid until " + billing_api_answer["licence_valid_until"]
                    licence_info = (
                        "Licence valid until "
                        + billing_api_answer["licence_valid_until"]
                    )
                    return render_template(
                        "licence_info_render.html", licence_info=licence_info
                    )
                else:
                    # return "Licence not found"
                    error = "Licence not found"
                    return render_template("error.html", error=error)
            else:
                # return "Bot id not found"
                error = "Bot id not found"
                return render_template("error.html", error=error)

        else:
            return abort(401)
            # return redirect(url_for("login"))
    else:
        return render_template("licence_info.html")


# if __name__ == '__main__':
#    app.run(host='127.0.0.1', port=5000, threaded=True, debug=True)
