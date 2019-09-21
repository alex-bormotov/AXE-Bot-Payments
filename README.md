### Payment and license processing service (Bitcoin) for Axe-Bot. Frontend for https://github.com/alex-bormotov/AXE-Bot-Billing-open


> Replace billing_url and callback into run.py

> Put blockchain_API_KEY into run.py -> gen_payment()

> Put chat_id, id (telegram) or WEB_HOOK_URL (discord) into notification.py

> Install on Heroku or other serverless or:

```python
sudo apt install python3 -pip
```
```python
pip3 install -r requirements.txt
```
``` bash
gunicorn run:app
```

> Put xpubs into db

---

This is one of the parts of my second Python project (https://github.com/alex-bormotov/AXE-Bot-open)
If my code was useful for you may buy me coffee 3K9ocinkiUUqkBj9BqvFVsUgW2uMLqZFcP (bitcoin)
