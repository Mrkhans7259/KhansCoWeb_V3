ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_PARTNER = "partner"
ROLE_MANAGER = "manager"
ROLE_STAFF = "staff"
ROLE_CLIENT = "client"

ADMIN_ROLES = [
    ROLE_SUPER_ADMIN,
    ROLE_ADMIN,
    ROLE_PARTNER,
    ROLE_MANAGER
]

ROLE_LABELS = {
    ROLE_SUPER_ADMIN: "Super Admin",
    ROLE_ADMIN: "Admin",
    ROLE_PARTNER: "Partner",
    ROLE_MANAGER: "Manager",
    ROLE_STAFF: "Staff",
    ROLE_CLIENT: "Client",
}


def has_role(session, allowed_roles):
    return session.get("user_role") in allowed_roles


def is_admin_user(session):
    return session.get("user_role") in ADMIN_ROLES


def can_manage_clients(session):
    return session.get("user_role") in [
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_PARTNER,
        ROLE_MANAGER
    ]


def can_manage_staff(session):
    return session.get("user_role") in [
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_PARTNER
    ]


def can_view_activity_log(session):
    return session.get("user_role") in [
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_PARTNER
    ]


def can_manage_compliance(session):
    return session.get("user_role") in [
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_PARTNER,
        ROLE_MANAGER,
        ROLE_STAFF
    ]


def can_manage_settings(session):
    return session.get("user_role") in [
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_PARTNER
    ]
