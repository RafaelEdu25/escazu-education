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

      // Botones estándar de Aprobación/Rechazo
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

      // --- Lógica para el botón de Notificar Corrección ---
      if (frm.fields_dict['custom_notificar_aspirante']) {
        frm.fields_dict['custom_notificar_aspirante'].$input.on('click', function () {
          frm.events.notificar_correccion_script(frm);
        });
      }
    }

    frappe.db.get_value('Education Settings', { name: 'Education Settings' }, 'user_creation_skip', (r) => {
      if (r && cint(r.user_creation_skip) !== 1) {
        frm.set_df_property('student_email_id', 'reqd', 1);
      }
    });
  },

  // Función que se ejecuta al presionar el botón de notificación
  notificar_correccion_script: function (frm) {
    if (!frm.doc.custom_documentos_incorrectos || frm.doc.custom_documentos_incorrectos.length === 0) {
      frappe.msgprint({
        title: __('Faltan datos'),
        indicator: 'orange',
        message: __('Por favor, seleccione al menos un documento en la lista de corrección.')
      });
      return;
    }

    frappe.confirm(__('¿Está seguro de que desea enviar la notificación de corrección al aspirante?'), () => {
      frappe.call({
        method: 'education.education.api.notificar_correccion',
        args: {
          docname: frm.doc.name
        },
        callback: function (r) {
          if (r.message) {
            frappe.show_alert({
              message: __('Notificación enviada correctamente'),
              indicator: 'green'
            });
            frm.reload_doc();
          }
        }
      });
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

  program: function (frm) {
    frm.trigger('check_eligibility');
  },

  date_of_birth: function (frm) {
    frm.trigger('check_eligibility');
  },

  check_eligibility: function (frm) {
    if (frm.doc.program && frm.doc.date_of_birth) {
      frappe.call({
        method: 'education.education.eligibility.check_program_eligibility',
        args: {
          program: frm.doc.program,
          date_of_birth: frm.doc.date_of_birth,
          applicant: frm.doc.name,
          is_new: frm.is_new() ? 1 : 0
        },
        callback: function (r) {
          if (r.message && r.message.eligible === false) {
            frappe.msgprint({
              title: __('Incompatibilidad Detectada'),
              indicator: 'red',
              message: r.message.message
            });
          }
        }
      });
    }
  },
  validate: function (frm) {
    if (!frm.doc.custom_acepta_términos || !frm.doc.custom_politicas_privacidad) {
      frappe.msgprint({
        title: __('Validación Requerida'),
        indicator: 'red',
        message: __('Debe leer y aceptar la Declaración Jurada y el Consentimiento Informado para continuar.')
      });
      frappe.validated = false;
    }
  }
});