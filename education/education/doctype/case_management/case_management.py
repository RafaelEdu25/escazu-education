# Copyright (c) 2026, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe import _


class CaseManagement(Document):
	def before_submit(self):
		if not self.case_reported_by:
			frappe.throw(_("Case Reported By must be filled before submitting."))

		if not self.case_plan or not self.case_outcome:
			frappe.throw(_("Case Plan and Case Outcome must be filled before submitting."))

		if self.case_status != "Closed":
			frappe.throw(_("Case Status must be 'Closed' before submitting."))

	def on_submit(self):
		scholar_status = frappe.db.get_value("Case Type", self.case_type, "scholar_status")
		if not frappe.db.get_value("Scholar", self.scholar, "status") == scholar_status:
			frappe.db.set_value("Scholar", self.scholar, "status", scholar_status)
