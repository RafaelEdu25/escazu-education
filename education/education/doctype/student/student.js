// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student', {
  refresh: function (frm) {
    frm.set_query('user', function (doc) {
      return { filters: { ignore_user_type: 1 } };
    });

    if (!frm.is_new()) {
      frm.add_custom_button(__('Accounting Ledger'), function () {
        frappe.set_route('query-report', 'General Ledger', { party_type: 'Customer', party: frm.doc.customer });
      });
    }

    frappe.db.get_single_value('Education Settings', 'user_creation_skip').then((r) => {
        if (cint(r) !== 1) frm.set_df_property('student_email_id', 'reqd', 1);
    });

    // UX Premium
    frm.trigger('render_custom_ui');
    if (!frm.is_new()) {
      frm.trigger('setup_dashboard');
    }
  },

  // --- LÓGICA DE INTERFAZ (UI) ---

  render_custom_ui: function (frm) {
    if (!$('style#student-pro-css').length) {
      $('<style id="student-pro-css">').html(`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

        /* Fondo y Contenedor Principal */
        body[data-route^="Form/Student"] {
            background-color: #f1f5f9 !important;
        }
        body[data-route^="Form/Student"] * {
            font-family: 'Outfit', sans-serif !important;
        }
        body[data-route^="Form/Student"] .page-container {
            max-width: 1200px !important;
            margin: 30px auto !important;
            background: transparent !important;
        }
        body[data-route^="Form/Student"] .layout-main-section {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        body[data-route^="Form/Student"] .form-page {
            background: transparent !important;
            border: none !important;
        }

        /* Tarjetas Flotantes Gigantes (Section Breaks) */
        body[data-route^="Form/Student"] .frappe-control[data-fieldtype="Section Break"] {
            background: #ffffff !important;
            border-radius: 20px !important;
            padding: 40px !important;
            margin-bottom: 35px !important;
            box-shadow: 0 20px 40px rgba(0,0,0,0.03), 0 1px 3px rgba(0,0,0,0.05) !important;
            border: 1px solid rgba(226,232,240, 0.8) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        }
        body[data-route^="Form/Student"] .frappe-control[data-fieldtype="Section Break"]:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 30px 60px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.05) !important;
        }

        /* Títulos de Sección Impresionantes */
        body[data-route^="Form/Student"] .section-head {
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            letter-spacing: -0.5px !important;
            border-bottom: 3px solid #f1f5f9 !important;
            margin-bottom: 30px !important;
            padding-bottom: 15px !important;
        }

        /* Ocultar tarjetas para HTML y Tab Breaks */
        body[data-route^="Form/Student"] .frappe-control[data-fieldtype="HTML"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin-bottom: 35px !important;
        }

        /* Inputs de Texto Premium */
        body[data-route^="Form/Student"] .form-control, 
        body[data-route^="Form/Student"] .awesomplete > input {
            height: 52px !important;
            font-size: 16px !important;
            font-weight: 500 !important;
            color: #1e293b !important;
            border: 2px solid #e2e8f0 !important;
            border-radius: 12px !important;
            background-color: #f8fafc !important;
            padding: 10px 20px !important;
            transition: all 0.25s ease !important;
        }
        body[data-route^="Form/Student"] .form-control:focus, 
        body[data-route^="Form/Student"] .awesomplete > input:focus {
            background-color: #ffffff !important;
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15) !important;
            outline: none !important;
        }

        /* Etiquetas de Campos (Labels) Modernas */
        body[data-route^="Form/Student"] .control-label {
            font-size: 14px !important;
            font-weight: 700 !important;
            color: #64748b !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            margin-bottom: 8px !important;
            display: block !important;
        }

        /* Selects especiales (Select) */
        body[data-route^="Form/Student"] select.form-control {
            appearance: none !important;
            cursor: pointer !important;
        }

        /* Checkboxes rediseñados */
        body[data-route^="Form/Student"] .checkbox .label-area {
            font-size: 16px !important;
            font-weight: 600 !important;
            color: #334155 !important;
        }

        /* Tablas incrustadas */
        body[data-route^="Form/Student"] .grid-body {
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
        }
      `).appendTo('head');
    }

    if (frm.fields_dict.custom_header) {
      const is_active = frm.doc.enabled;
      const bg = is_active ? 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)' : 'linear-gradient(135deg, #64748b 0%, #475569 100%)';
      const icon = is_active ? 'fa-user' : 'fa-user-times';
      const status_text = is_active ? 'Activo' : 'Inactivo';
      
      const title = frm.doc.first_name ? `${frm.doc.first_name} ${frm.doc.last_name || ''}`.trim() : __('Nuevo Estudiante');
      const detail = [frm.doc.student_email_id, frm.doc.student_mobile_number].filter(Boolean).join(' | ') || __('Complete los datos personales');
      
      let avatar_html = `<i class="fa ${icon}"></i>`;
      if (frm.doc.image) {
          avatar_html = `<img src="${frm.doc.image}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;" />`;
      }

      let html = `
        <div style="background: ${bg}; border-radius: 14px; padding: 30px; color: white; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 10px 20px -5px rgba(0,0,0,0.15); margin-bottom: 25px;">
            <div style="display: flex; align-items: center;">
                <div style="background: rgba(255,255,255,0.2); width: 65px; height: 65px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-right: 20px; font-size: 28px; overflow: hidden; border: 2px solid rgba(255,255,255,0.5);">
                    ${avatar_html}
                </div>
                <div>
                    <h2 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">${title}</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px; font-weight: 500;">${detail}</p>
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(255,255,255,0.2); padding: 8px 18px; border-radius: 50px; font-weight: 700; font-size: 12px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.4);">
                    ${status_text}
                </span>
            </div>
        </div>
      `;
      $(frm.fields_dict.custom_header.wrapper).html(html);
    }
  },

  setup_dashboard: function(frm) {
      frm.dashboard.clear_indicators();
      if (frm.doc.date_of_birth) {
          const age = moment().diff(moment(frm.doc.date_of_birth), 'years');
          frm.dashboard.add_indicator(__('Edad: {0} años', [age]), 'blue', 'fa-calendar');
      }
      if (frm.doc.current_program) {
          frm.dashboard.add_indicator(__('Programa: {0}', [frm.doc.current_program]), 'purple', 'fa-graduation-cap');
      }
  },

  first_name: function(frm) { frm.trigger('render_custom_ui'); },
  last_name: function(frm) { frm.trigger('render_custom_ui'); },
  enabled: function(frm) { frm.trigger('render_custom_ui'); },
  image: function(frm) { frm.trigger('render_custom_ui'); }
});

frappe.ui.form.on('Student Guardian', {
  guardians_add: function (frm) {
    frm.fields_dict['guardians'].grid.get_field('guardian').get_query = function (doc) {
      let current = (doc.guardians || []).map(i => i.guardian).filter(Boolean);
      return { filters: [['Guardian', 'name', 'not in', current]] };
    };
  }
});
