from app.database.models import User, Client, Staff


def check_client_duplicates(email=None, mobile=None, pan=None, gstin=None, exclude_client_id=None):
    errors = []

    def client_query(field, value):
        query = Client.query.filter(field == value)
        if exclude_client_id:
            query = query.filter(Client.id != exclude_client_id)
        return query.first()

    if email and client_query(Client.email, email):
        errors.append("Email already exists in Client Master.")

    if mobile and client_query(Client.mobile, mobile):
        errors.append("Mobile number already exists in Client Master.")

    if pan and client_query(Client.pan, pan):
        errors.append("PAN already exists in Client Master.")

    if gstin and client_query(Client.gstin, gstin):
        errors.append("GSTIN already exists in Client Master.")

    return errors


def check_user_signup_duplicates(email=None, mobile=None, pan=None, gstin=None):
    errors = []

    if email and User.query.filter_by(email=email).first():
        errors.append("Email already registered.")

    if mobile and User.query.filter_by(mobile=mobile).first():
        errors.append("Mobile number already registered.")

    if pan and User.query.filter_by(pan=pan).first():
        errors.append("PAN already registered.")

    if gstin and User.query.filter_by(gstin=gstin).first():
        errors.append("GSTIN already registered.")

    return errors


def check_staff_duplicates(email=None, mobile=None, exclude_staff_id=None):
    errors = []

    if email:
        query = Staff.query.filter_by(email=email)
        if exclude_staff_id:
            query = query.filter(Staff.id != exclude_staff_id)
        if query.first():
            errors.append("Staff email already exists.")

    if mobile:
        query = Staff.query.filter_by(mobile=mobile)
        if exclude_staff_id:
            query = query.filter(Staff.id != exclude_staff_id)
        if query.first():
            errors.append("Staff mobile number already exists.")

    return errors
