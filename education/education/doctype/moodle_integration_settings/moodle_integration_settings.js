// Copyright (c) 2025, Education and contributors
// For license information, please see license.txt

frappe.ui.form.on("Moodle Integration Settings", {
	test_connection: function (frm) {
		frappe.msgprint("Test Connection clicked!");

		frappe.call({
			method: "education.education.doctype.moodle_integration_settings.moodle_integration_settings.test_connection",
			callback: function (r) {
				if (r.message) {
					frappe.msgprint(r.message);
				}
			},
			error: function (r) {
				frappe.msgprint("Error: " + r.exception);
			},
		});
	},

	sync_all: function (frm) {
		frappe.msgprint("Syncing all courses...");

		frappe.call({
			method: "education.education.doctype.moodle_integration_settings.moodle_integration_settings.sync_all_programs",
			callback: function (r) {
				if (r.message) {
					frappe.msgprint(r.message);
				}
			},
			error: function (r) {
				frappe.msgprint("Error: " + r.exception);
			},
		});
	},

	import_moodle: function (frm) {
		frappe.msgprint("Importing courses from Moodle...");

		frappe.call({
			method: "education.education.doctype.moodle_integration_settings.moodle_integration_settings.import_moodle",
			callback: function (r) {
				if (r.message) {
					frappe.msgprint(r.message);
				}
			},
			error: function (r) {
				frappe.msgprint("Error: " + r.exception);
			},
		});
	},

	sync_from_moodle_auto: function (frm) {
		frappe.msgprint("Syncing courses from Moodle to Frappe...");

		frappe.call({
			method: "education.education.doctype.moodle_integration_settings.moodle_integration_settings.sync_moodle_auto",
			callback: function (r) {
				if (r.message) {
					frappe.msgprint(r.message);
				}
			},
			error: function (r) {
				frappe.msgprint("Error: " + r.exception);
			},
		});
	},
});