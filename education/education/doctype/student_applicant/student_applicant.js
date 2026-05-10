// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Applicant', {
  refresh: function (frm) {
    // UX Premium
    frm.trigger('render_custom_ui');
    if (!frm.is_new()) {
      frm.trigger('setup_dashboard');
    }

    frm.set_query('academic_term', function (doc, cdt, cdn) {
      return {
        filters: {
          academic_year: frm.doc.academic_year,
        },
      }
    })

    if (!frm.is_new() && frm.doc.application_status === 'Applied') {
      frm.add_custom_button(
        __('Approve'),
        function () {
          frm.set_value('application_status', 'Approved')
          frm.save_or_update()
        },
        'Actions'
      )

      frm.add_custom_button(
        __('Reject'),
        function () {
          frm.set_value('application_status', 'Rejected')
          frm.save_or_update()
        },
        'Actions'
      )
    }

    if (!frm.is_new() && frm.doc.application_status === 'Approved') {
      frm.add_custom_button(__('Enroll'), function () {
        frm.events.enroll(frm)
      })

      frm.add_custom_button(
        __('Reject'),
        function () {
          frm.set_value('application_status', 'Rejected')
          frm.save_or_update()
        },
        'Actions'
      )
    }

    if (!frm.is_new() && frm.doc.application_status === 'Rejected') {
      frm.add_custom_button(
        __('Approve'),
        function () {
          frm.set_value('application_status', 'Approved')
          frm.save_or_update()
        },
        'Actions'
      )
    }

    frappe.realtime.on('enroll_student_progress', function (data) {
      if (data.progress) {
        frappe.hide_msgprint(true)
        frappe.show_progress(
          __('Enrolling student'),
          data.progress[0],
          data.progress[1]
        )
      }
    })

    frappe.db.get_value(
      'Education Settings',
      { name: 'Education Settings' },
      'user_creation_skip',
      (r) => {
        if (cint(r.user_creation_skip) !== 1) {
          frm.set_df_property('student_email_id', 'reqd', 1)
        }
      }
    )
  },

  enroll: function (frm) {
    frappe.model.open_mapped_doc({
      method: 'education.education.api.enroll_student',
      frm: frm,
    })
  },

  render_custom_ui: function (frm) {
    if (!$('style#applicant-pro-css').length) {
      $('<style id="applicant-pro-css">').html(`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

        /* Fondo y Contenedor Principal */
        body[data-route^="Form/Student Applicant"] {
            background-color: #f1f5f9 !important;
        }
        body[data-route^="Form/Student Applicant"] * {
            font-family: 'Outfit', sans-serif !important;
        }
        body[data-route^="Form/Student Applicant"] .page-container {
            max-width: 1200px !important;
            margin: 30px auto !important;
            background: transparent !important;
        }
        body[data-route^="Form/Student Applicant"] .layout-main-section {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Tarjetas Flotantes Gigantes (Section Breaks) */
        body[data-route^="Form/Student Applicant"] .frappe-control[data-fieldtype="Section Break"] {
            background: #ffffff !important;
            border-radius: 20px !important;
            padding: 40px !important;
            margin-bottom: 35px !important;
            box-shadow: 0 20px 40px rgba(0,0,0,0.03), 0 1px 3px rgba(0,0,0,0.05) !important;
            border: 1px solid rgba(226,232,240, 0.8) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        }
        body[data-route^="Form/Student Applicant"] .frappe-control[data-fieldtype="Section Break"]:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 30px 60px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.05) !important;
        }

        /* Títulos de Sección Impresionantes */
        body[data-route^="Form/Student Applicant"] .section-head {
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            letter-spacing: -0.5px !important;
            border-bottom: 3px solid #f1f5f9 !important;
            margin-bottom: 30px !important;
            padding-bottom: 15px !important;
        }

        /* Ocultar tarjetas para HTML y Tab Breaks */
        body[data-route^="Form/Student Applicant"] .frappe-control[data-fieldtype="HTML"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin-bottom: 35px !important;
        }

        /* Inputs de Texto Premium */
        body[data-route^="Form/Student Applicant"] .form-control, 
        body[data-route^="Form/Student Applicant"] .awesomplete > input {
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
        body[data-route^="Form/Student Applicant"] .form-control:focus, 
        body[data-route^="Form/Student Applicant"] .awesomplete > input:focus {
            background-color: #ffffff !important;
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15) !important;
            outline: none !important;
        }

        /* Etiquetas de Campos (Labels) Modernas */
        body[data-route^="Form/Student Applicant"] .control-label {
            font-size: 14px !important;
            font-weight: 700 !important;
            color: #64748b !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            margin-bottom: 8px !important;
            display: block !important;
        }

        /* Selects especiales (Select) */
        body[data-route^="Form/Student Applicant"] select.form-control {
            appearance: none !important;
            cursor: pointer !important;
        }

        /* Checkboxes rediseñados */
        body[data-route^="Form/Student Applicant"] .checkbox .label-area {
            font-size: 16px !important;
            font-weight: 600 !important;
            color: #334155 !important;
        }
      `).appendTo('head');
    }

    if (frm.fields_dict.custom_header) {
      const status = frm.doc.application_status;
      let bg = 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)';
      let status_label = 'Solicitado';

      if (status === 'Approved') { bg = 'linear-gradient(135deg, #10b981 0%, #059669 100%)'; status_label = 'Aprobado'; }
      if (status === 'Rejected') { bg = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'; status_label = 'Rechazado'; }
      if (status === 'Admitted') { bg = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'; status_label = 'Admitido'; }

      const title = frm.doc.first_name ? `${frm.doc.first_name} ${frm.doc.last_name || ''}`.trim() : __('Nuevo Aplicante');
      const detail = [frm.doc.student_email_id, frm.doc.student_mobile_number].filter(Boolean).join(' | ') || __('Complete los datos de la solicitud');

      let avatar_html = `<i class="fa fa-user-plus"></i>`;
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
                    ${status_label}
                </span>
            </div>
        </div>
      `;
      $(frm.fields_dict.custom_header.wrapper).html(html);
    }
  },

  setup_dashboard: function (frm) {
    frm.dashboard.clear_indicators();
    if (frm.doc.program) {
      frm.dashboard.add_indicator(__('Programa: {0}', [frm.doc.program]), 'purple', 'fa-graduation-cap');
    }
    if (frm.doc.academic_year) {
      frm.dashboard.add_indicator(__('Año: {0}', [frm.doc.academic_year]), 'blue', 'fa-calendar');
    }
    if (frm.doc.paid) {
      frm.dashboard.add_indicator(__('Pagado', []), 'green', 'fa-check-circle');
    } else {
      frm.dashboard.add_indicator(__('Pendiente de Pago', []), 'orange', 'fa-clock-o');
    }
  },

  first_name: function (frm) { frm.trigger('render_custom_ui'); },
  last_name: function (frm) { frm.trigger('render_custom_ui'); },
  application_status: function (frm) { frm.trigger('render_custom_ui'); },
  image: function (frm) { frm.trigger('render_custom_ui'); }
});
