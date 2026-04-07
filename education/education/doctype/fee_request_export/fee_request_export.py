# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FeeRequestExport(Document):
	@frappe.whitelist()
	def fetch_fee_requests(self):
		FR = frappe.qb.DocType("Fee Request")
		BA = frappe.qb.DocType("Bank Account")
		SC = frappe.qb.DocType("Scholar")
		CC = frappe.qb.DocType("County Coordinator Mapping Item")

		query = (
			frappe.qb.from_(FR)
			.join(SC)
			.on(FR.scholar == SC.name)
			.left_join(BA)
			.on(FR.official_school_name == BA.account_name)
			.left_join(CC)
			.on(SC.county == CC.county)
			.select(
				FR.name,
				SC.county,
				SC.guardian_contact,
				FR.official_school_name,
				FR.scholar,
				FR.student_name,
				FR.outstanding_amount,
				BA.custom_branch_name,
				BA.branch_code,
				BA.custom_bank_code,
				BA.bank_account_no,
				BA.bank,
				BA.account_name,
				CC.user,
			)
			.where(
				(FR.docstatus == 1)
				& (FR.academic_year == self.academic_year)
				& (FR.academic_term == self.academic_term)
				& (FR.company == self.company)
				& (FR.payment_status == "Unpaid")
			)
		)

		fee_requests = query.run(as_dict=True)

		if not fee_requests:
			frappe.throw("No fee requests found.")

		emails = frappe.db.get_value(
			"County Coordinator Mapping",
			"County Coordinator Mapping",
			["payable_email", "scholarship_email"],
			as_dict=True,
		)

		results = []
		if self.bank == "Standard Chartered":
			for fee_request in fee_requests:
				fee_request_details = {
					"fee_request": fee_request.name,
					"scholar": fee_request.scholar,
					"student_name": fee_request.student_name,
					"school_name": fee_request.official_school_name,
					"account_number": fee_request.bank_account_no,
					"bank_code": fee_request.custom_bank_code,
					"branch_code": fee_request.branch_code,
					"amount": fee_request.outstanding_amount,
					"email_address": f"{emails.payable_email},{emails.scholarship_email},{fee_request.user}",
				}
				results.append(fee_request_details)

		if self.bank == "KCB":
			company_account = frappe.db.get_value(
				"Bank Account",
				{"bank": "KCB", "is_company_account": 1},
				["bank_account_no", "branch_code"],
				as_dict=True,
			)

			for fee_request in fee_requests:
				fee_request_details = {
					"fee_request": fee_request.name,
					"scholar": fee_request.scholar,
					"student_name": fee_request.student_name,
					"debit_account": (
						company_account.get("bank_account_no") if company_account else None
					),
					"beneficiary_name": fee_request.official_school_name,
					"bank": fee_request.bank,
					"branch": fee_request.custom_branch_name,
					"branch_bicsort_code": (
						company_account.get("branch_code") if company_account else None
					),
					"bicsort_code": fee_request.branch_code,
					"account_number": fee_request.bank_account_no,
					"my_reference": fee_request.official_school_name,
					"sms_notification": fee_request.guardian_contact,
					"amount": fee_request.outstanding_amount,
					"email_notification": f"{emails.scholarship_email}",
				}
				results.append(fee_request_details)

		return results

	def on_submit(self):
		if self.bank == "Standard Chartered":
			for row in self.standard_chartered_fee_requests:
				if row.fee_request:
					frappe.db.set_value(
						"Fee Request",
						row.fee_request,
						{
							"exported_for_payment": 1,
							"exported_for_payment_on": self.name,
						},
					)

		if self.bank == "KCB":
			for row in self.kcb_fee_requests:
				if row.fee_request:
					frappe.db.set_value(
						"Fee Request",
						row.fee_request,
						{
							"exported_for_payment": 1,
							"exported_for_payment_on": self.name,
						},
					)

	def on_cancel(self):
		# self.ignore_linked_doctypes = (
		#     "Fee Request"
		# )
		if self.bank == "Standard Chartered":
			for row in self.standard_chartered_fee_requests:
				if row.fee_request:
					frappe.db.set_value(
						"Fee Request",
						row.fee_request,
						{
							"exported_for_payment": 0,
							"exported_for_payment_on": None,
						},
					)

		if self.bank == "KCB":
			for row in self.kcb_fee_requests:
				if row.fee_request:
					frappe.db.set_value(
						"Fee Request",
						row.fee_request,
						{
							"exported_for_payment": 0,
							"exported_for_payment_on": None,
						},
					)
