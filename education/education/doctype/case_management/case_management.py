# Copyright (c) 2026, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe import _


class CaseManagement(Document):
	def validate(self):
		if not self.case_reported_by:
			self.case_reported_by = frappe.session.user

	def before_submit(self):
		validate_case_plan_outcome = frappe.db.get_single_value(
			"Education Settings", "validate_case_plan_outcome_on_submit"
		)
		if validate_case_plan_outcome:
			if not self.case_plan or not self.case_outcome:
				frappe.throw(_("Case Plan and Case Outcome must be filled before submitting."))

		if self.case_status != "Closed":
			frappe.throw(_("Case Status must be 'Closed' before submitting."))

	def on_submit(self):
		update_scholar_status_on_case_close = frappe.db.get_single_value(
			"Education Settings", "update_scholar_status_on_case_close"
		)
		if not update_scholar_status_on_case_close:
			return

		scholar_status = frappe.db.get_value("NL Case Type", self.case_type, "scholar_status")
		if not frappe.db.get_value("Scholar", self.scholar, "status") == scholar_status:
			frappe.db.set_value("Scholar", self.scholar, "status", scholar_status)
