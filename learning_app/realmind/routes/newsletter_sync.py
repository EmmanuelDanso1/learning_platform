import os
import requests
from flask import current_app
from extensions import db
from learning_app.realmind.models import ExternalSubscriber


def sync_bookshop_subscribers():
    BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
    API_TOKEN = os.getenv("API_TOKEN")

    try:
        res = requests.get(
            f"{BOOKSHOP_API}/api/newsletter-subscribers",
            headers={'Authorization': f'Bearer {API_TOKEN}'},
            timeout=10
        )

        if res.status_code != 200:
            current_app.logger.error(
                f"Failed to fetch subscribers ({res.status_code})"
            )
            return

        emails = res.json().get('subscribers', [])

        new_count = 0
        for email in emails:
            exists = ExternalSubscriber.query.filter_by(email=email).first()
            if not exists:
                db.session.add(ExternalSubscriber(email=email))
                new_count += 1

        db.session.commit()

        current_app.logger.info(
            f"Synced {new_count} new bookshop subscribers"
        )

    except Exception as e:
        current_app.logger.exception(
            "Newsletter subscriber sync failed"
        )
