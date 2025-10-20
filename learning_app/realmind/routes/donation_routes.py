import uuid
import requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from learning_app.realmind.models import Donation
from flask_wtf.csrf import validate_csrf, generate_csrf, CSRFError

from learning_app.extensions import db

donation_bp = Blueprint('donation', __name__)

@donation_bp.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        try:
            token = request.form.get('csrf_token')
            validate_csrf(token)
        except CSRFError:
            abort(400, description="CSRF token is missing or invalid.")

        name = request.form['name']
        email = request.form['email']
        amount = int(request.form['amount']) * 100  # Convert to cedis
        reference = str(uuid.uuid4())

        donation = Donation(name=name, email=email, amount=amount, reference=reference)
        db.session.add(donation)
        db.session.commit()

        paystack_secret_key = current_app.config['PAYSTACK_SECRET_KEY']
        paystack_public_key = current_app.config['PAYSTACK_PUBLIC_KEY']
        initialize_url = current_app.config['PAYSTACK_INITIALIZE_URL']

        headers = {
            "Authorization": f"Bearer {paystack_secret_key}",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "amount": amount,
            "reference": reference,
            "callback_url": url_for('donation.donation_success', _external=True)
        }

        try:
            response = requests.post(initialize_url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            payment_url = response.json()['data']['authorization_url']
            return redirect(payment_url)

        except requests.exceptions.Timeout:
            flash("Request timed out. Please try again.", "warning")
            return render_template("errors/timeout.html"), 504

        except requests.exceptions.ConnectionError:
            flash("Could not connect to Paystack. Check your internet and try again.", "danger")
            return render_template("errors/connection_error.html"), 502

        except requests.exceptions.RequestException as e:
            flash("Something went wrong while initializing payment.", "danger")
            return render_template("errors/general_error.html", error=str(e)), 500

    return render_template('donate.html', csrf_token=generate_csrf())
@donation_bp.route('/donation-success')
def donation_success():
    return render_template('donation_success.html')
