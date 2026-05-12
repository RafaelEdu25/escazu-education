// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student', {
  refresh: function (frm) {
    // Filtro para el campo Usuario
    frm.set_query('user', function (doc) {
      return { filters: { ignore_user_type: 1 } };
    });

    // Botón para ver Contabilidad (solo si el documento ya existe)
    if (!frm.is_new()) {
      frm.add_custom_button(__('Accounting Ledger'), function () {
        frappe.set_route('query-report', 'General Ledger', {
          party_type: 'Customer',
          party: frm.doc.customer
        });
      });

      // Cargar Dashboard nativo
      frm.trigger('setup_dashboard');
    }

    // Validación de Email obligatorio según configuración de Educación
    frappe.db.get_single_value('Education Settings', 'user_creation_skip').then((r) => {
      if (cint(r) !== 1) {
        frm.set_df_property('student_email_id', 'reqd', 1);
      }
    });
  },

  // Dashboard nativo de Frappe (Indicadores en la parte superior)
  setup_dashboard: function (frm) {
    frm.dashboard.clear_indicators();

    // Indicador de Edad
    if (frm.doc.date_of_birth) {
      const age = moment().diff(moment(frm.doc.date_of_birth), 'years');
      frm.dashboard.add_indicator(__('Edad: {0} años', [age]), 'blue', 'fa-calendar');
    }

    // Indicador de Programa Actual
    if (frm.doc.current_program) {
      frm.dashboard.add_indicator(__('Programa: {0}', [frm.doc.current_program]), 'purple', 'fa-graduation-cap');
    }

    // Indicador de Estado (Habilitado/Inhabilitado)
    if (frm.doc.enabled) {
      frm.dashboard.add_indicator(__('Activo'), 'green', 'fa-check');
    } else {
      frm.dashboard.add_indicator(__('Inactivo'), 'red', 'fa-times');
    }
  }
});

// Lógica para la tabla de Guardianes (Evitar duplicados)
frappe.ui.form.on('Student Guardian', {
  guardians_add: function (frm) {
    frm.fields_dict['guardians'].grid.get_field('guardian').get_query = function (doc) {
      let current = (doc.guardians || []).map(i => i.guardian).filter(Boolean);
      return {
        filters: [['Guardian', 'name', 'not in', current]]
      };
    };
  }
});