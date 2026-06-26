import re

MOBILE_RE = re.compile(r"^[0-9]{10}$")
PINCODE_RE = re.compile(r"^[0-9]{6}$")
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]{3}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def clean(value):
    return (value or "").strip()


def upper(value):
    return clean(value).upper()


def is_valid_mobile(value):
    value = clean(value)
    return not value or bool(MOBILE_RE.match(value))


def is_valid_email(value):
    value = clean(value)
    return not value or bool(EMAIL_RE.match(value))


def is_valid_pan(value):
    value = upper(value)
    return not value or bool(PAN_RE.match(value))


def is_valid_gstin(value):
    value = upper(value)
    return not value or bool(GSTIN_RE.match(value))


def is_valid_pincode(value):
    value = clean(value)
    return not value or bool(PINCODE_RE.match(value))


def validate_mobile(value, required=False):
    value = clean(value)
    if not value and not required:
        return True, ""
    if not MOBILE_RE.match(value):
        return False, "Mobile number must contain numbers only and must be exactly 10 digits."
    return True, ""


def validate_email(value, required=False):
    value = clean(value)
    if not value and not required:
        return True, ""
    if not EMAIL_RE.match(value):
        return False, "Please enter a valid email address."
    return True, ""


def validate_pan(value, required=False):
    value = upper(value)
    if not value and not required:
        return True, ""
    if not PAN_RE.match(value):
        return False, "PAN must be in valid format like ABCDE1234F."
    return True, ""


def validate_gstin(value, required=False):
    value = upper(value)
    if not value and not required:
        return True, ""
    if not GSTIN_RE.match(value):
        return False, "GSTIN must be valid 15-character format like 29ABCDE1234F1Z5."
    return True, ""


def validate_pincode(value, required=False):
    value = clean(value)
    if not value and not required:
        return True, ""
    if not PINCODE_RE.match(value):
        return False, "Pincode must contain numbers only and must be exactly 6 digits."
    return True, ""


def collect_errors(*checks):
    errors = []
    for ok, message in checks:
        if not ok:
            errors.append(message)
    return errors


PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}$")


def validate_password(value, required=True):
    value = clean(value)
    if not value and not required:
        return True, ""
    if not PASSWORD_RE.match(value):
        return False, "Password must be minimum 8 characters with uppercase, lowercase, number and special character."
    return True, ""
