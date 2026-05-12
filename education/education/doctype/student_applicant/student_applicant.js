// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Applicant', {
  refresh: function (frm) {
    if (!frm.is_new()) {
      frm.trigger('setup_dashboard');
    }

    frm.set_query('academic_term', function () {
      return {
        filters: { academic_year: frm.doc.academic_year },
      };
    });

    if (!frm.is_new()) {
      const status = frm.doc.application_status;
      if (status === 'Applied') {
        frm.add_custom_button(__('Approve'), () => {
          frm.set_value('application_status', 'Approved');
          frm.save();
        }, 'Actions');
        frm.add_custom_button(__('Reject'), () => {
          frm.set_value('application_status', 'Rejected');
          frm.save();
        }, 'Actions');
      }
      if (status === 'Approved') {
        frm.add_custom_button(__('Enroll'), () => frm.events.enroll(frm));
        frm.add_custom_button(__('Reject'), () => {
          frm.set_value('application_status', 'Rejected');
          frm.save();
        }, 'Actions');
      }
    }

    frappe.db.get_value('Education Settings', { name: 'Education Settings' }, 'user_creation_skip', (r) => {
      if (r && cint(r.user_creation_skip) !== 1) {
        frm.set_df_property('student_email_id', 'reqd', 1);
      }
    });
  },

  enroll: function (frm) {
    frappe.model.open_mapped_doc({
      method: 'education.education.api.enroll_student',
      frm: frm,
    });
  },

  setup_dashboard: function (frm) {
    frm.dashboard.clear_indicators();
    if (frm.doc.program) {
      frm.dashboard.add_indicator(__('Programa: {0}', [frm.doc.program]), 'purple', 'fa-graduation-cap');
    }
    if (frm.doc.academic_year) {
      frm.dashboard.add_indicator(__('Año: {0}', [frm.doc.academic_year]), 'blue', 'fa-calendar');
    }
  },

  // --- VALIDACIÓN CORREGIDA ---

  program: function (frm) {
    console.log("Cambio en programa detectado");
    frm.trigger('check_eligibility');
  },

  date_of_birth: function (frm) {
    console.log("Cambio en fecha detectado");
    frm.trigger('check_eligibility');
  },

  program: function (frm) { frm.trigger('check_eligibility'); },
  date_of_birth: function (frm) { frm.trigger('check_eligibility'); },

  check_eligibility: function (frm) {
    if (frm.doc.program && frm.doc.date_of_birth) {
      console.log("Enviando validación para:", frm.doc.program, frm.doc.date_of_birth);

      frappe.call({
        method: 'education.education.eligibility.check_program_eligibility',
        args: {
          program: frm.doc.program,
          date_of_birth: frm.doc.date_of_birth,
          applicant: frm.doc.name,
          is_new: frm.is_new() ? 1 : 0
        },
        callback: function (r) {
          console.log("Respuesta del servidor:", r.message);
          if (r.message && r.message.eligible === false) {
            // Usamos msgprint con indicator para que sea muy visible
            frappe.msgprint({
              title: __('Incompatibilidad Detectada'),
              indicator: 'red',
              message: r.message.message
            });
          }
        }
      });
    }
  }
});