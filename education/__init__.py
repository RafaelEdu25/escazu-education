import frappe
from frappe.utils.user import is_website_user
from frappe.utils.modules import get_modules_from_all_apps_for_user

__version__ = "16.0.0"


def check_app_permission():
    if frappe.session.user == "Administrator":
        return True

    allowed_modules = get_modules_from_all_apps_for_user()
    allowed_modules = [x["module_name"] for x in allowed_modules]

    if "Education" not in allowed_modules:
        return False

    roles = frappe.get_roles()
    if any(
        role
        in [
            "System Manager",
            "Student",
            "Instructor",
            "Education Manager",
            "Academic User",
        ]
        for role in roles
    ):
        return True

    return False
