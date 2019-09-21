import requests
import http.client


def notificator(notification):
    discord_send_message(notification)
    telegram_send_message(notification)


chat_id = "ID"
token = "TOKEN"
URL = "https://api.telegram.org/bot{}/".format(token)


def get_url(url):

    try:
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    except requests.exceptions.RequestException as e:
        if show_error == "YES":
            notificator(str(e))
    except Exception as e:
        if show_error == "YES":
            notificator(str(e))


def telegram_send_message(notification):
    url = URL + "sendMessage?text={}&chat_id={}".format(notification, chat_id)
    get_url(url)


def discord_send_message(notification):

    webhookurl = "WEB_HOOK_URL"

    formdata = (
        '------:::BOUNDARY:::\r\nContent-Disposition: form-data; name="content"\r\n\r\n'
        + notification
        + "\r\n------:::BOUNDARY:::--"
    )
    try:
        connection = http.client.HTTPSConnection("discordapp.com")
        connection.request(
            "POST",
            webhookurl,
            formdata,
            {
                "content-type": "multipart/form-data; boundary=----:::BOUNDARY:::",
                "cache-control": "no-cache",
            },
        )

        response = connection.getresponse()

    except requests.exceptions.RequestException as e:
        if show_error == "YES":
            notificator(str(e))
    except Exception as e:
        if show_error == "YES":
            notificator(str(e))
