// Copyright (c) 2026, Navari and contributors
// For license information, please see license.txt

frappe.ui.form.on('Case Management', {
  refresh(frm) {
    if (frm.is_new()) {
      frm.set_value('case_manager', frappe.session.user)
    }
  },
})
