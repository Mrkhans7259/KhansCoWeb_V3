from flask import request, flash, redirect
from app.utils.validators import (
    clean,
    upper,
    is_valid_mobile,
    is_valid_email,
    is_valid_pan,
    is_valid_gstin,
    is_valid_pincode,
)


def init_validation_hooks(app):
    @app.before_request
    def validate_common_form_fields():
        if request.method != "POST":
            return None

        errors = []

        mobile = clean(request.form.get("mobile"))
        email = clean(request.form.get("email"))
        pan = upper(request.form.get("pan"))
        gstin = upper(request.form.get("gstin"))
        pincode = clean(request.form.get("pincode"))

        if "mobile" in request.form and not is_valid_mobile(mobile):
            errors.append("Mobile number must contain numbers only and must be exactly 10 digits.")

        if "email" in request.form and not is_valid_email(email):
            errors.append("Please enter a valid email address.")

        if "pan" in request.form and not is_valid_pan(pan):
            errors.append("PAN must be in valid format like ABCDE1234F.")

        if "gstin" in request.form and not is_valid_gstin(gstin):
            errors.append("GSTIN must be valid 15-character format like 29ABCDE1234F1Z5.")

        if "pincode" in request.form and not is_valid_pincode(pincode):
            errors.append("Pincode must contain numbers only and must be exactly 6 digits.")

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(request.referrer or "/")

        return None
