# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.utils import flt


class FeeRequestPayment(Document):
	def before_save(self):
		if not self.fee_request:
			frappe.throw("Fee Request is mandatory.")

	def on_submit(self):
		fee_request_doc = frappe.get_doc("Fee Request", self.fee_request)
		if fee_request_doc.payment_status == "Paid":
			frappe.throw(
				"Fee Request for {0}-{1} is already marked as Paid.".format(
					self.scholar, self.student_name
				)
			)
		fee_request_doc.flags.ignore_validate_update_after_submit = True

		exists = any(row.fee_request_payment == self.name for row in fee_request_doc.payments)

		if not exists:
			fee_request_doc.append(
				"payments",
				{
					"fee_request_payment": self.name,
					"paid_amount": self.paid_amount,
					"payment_date": self.posting_date,
				},
			)

		total_paid = sum([flt(payment.paid_amount) for payment in fee_request_doc.payments])
		fee_request_doc.paid_amount = total_paid
		fee_request_doc.outstanding_amount = flt(fee_request_doc.total_amount) - total_paid

		if fee_request_doc.outstanding_amount <= 0:
			fee_request_doc.payment_status = "Paid"
		elif total_paid > 0:
			fee_request_doc.payment_status = "Partially Paid"
		else:
			fee_request_doc.payment_status = "Unpaid"

		fee_request_doc.save(ignore_permissions=True)

	def on_cancel(self):

		fee_request_doc = frappe.get_doc("Fee Request", self.fee_request)

		fee_request_doc.flags.ignore_validate_update_after_submit = True

		payment_row = next(
			(row for row in fee_request_doc.payments if row.fee_request_payment == self.name),
			None,
		)

		if payment_row:
			fee_request_doc.remove(payment_row)

		total_paid = sum([flt(payment.paid_amount) for payment in fee_request_doc.payments])
		fee_request_doc.paid_amount = total_paid
		fee_request_doc.outstanding_amount = flt(fee_request_doc.total_amount) - total_paid

		if fee_request_doc.outstanding_amount <= 0:
			fee_request_doc.payment_status = "Paid"
		elif total_paid > 0:
			fee_request_doc.payment_status = "Partially Paid"
		else:
			fee_request_doc.payment_status = "Unpaid"

		fee_request_doc.save(ignore_permissions=True)
