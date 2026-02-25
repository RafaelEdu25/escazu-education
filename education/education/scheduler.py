import frappe


from ..education.doctype.scholarship_promotion_rule.scholarship_promotion_rule import (
	auto_promote_scholars_yearly,
)


@frappe.whitelist()
def auto_promote_scholars():
	settings = frappe.get_single("Education Settings")
	if not settings.auto_promote_scholars:
		return

	auto_promote_scholars_yearly()
