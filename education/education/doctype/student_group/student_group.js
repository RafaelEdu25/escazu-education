/**
 * UI Mejorada para Student Group
 * Enfoque: Experiencia de Usuario Premium, Diseño de Tarjetas y Feedback Visual.
 */

frappe.ui.form.on('Student Group', {
  onload: function (frm) {
    // Consultas dinámicas optimizadas
    frm.set_query('academic_term', () => ({
      filters: { academic_year: frm.doc.academic_year }
    }));

    frm.set_query('program_module', () => ({
      filters: { program: frm.doc.program }
    }));

    if (!frm.is_new()) {
      frm.trigger('setup_student_query');
    }
  },

  refresh: function (frm) {
    // 1. Renderizar Interfaz Visual (Banner y CSS)
    frm.trigger('render_custom_ui');

    if (!frm.is_new()) {
      // 2. Configurar Dashboard (Indicadores)
      frm.trigger('setup_dashboard');

      // 3. Configurar Botones de Acción (Agrupados lógicamente)
      frm.trigger('setup_buttons');

      // 4. RF-21/22: Consultar estado de matrícula y mostrar advertencia
      frm.trigger('check_enrollment_status');

      // 5. Mensaje de introducción dinámico
      if (!frm.doc.students || frm.doc.students.length === 0) {
        frm.set_intro(__('Este grupo no tiene estudiantes. Use el botón "Obtener Estudiantes" para poblar la lista.'), 'orange');
      } else {
        frm.set_intro(null);
      }
    }

    // 6. Aplicar lógica de visibilidad inicial
    frm.trigger('modality');
  },

  // --- LÓGICA DE INTERFAZ (UI) ---

  render_custom_ui: function (frm) {
    // Inyectar CSS Pro (Solo una vez)
    if (!$('style#student-group-pro-css').length) {
      $('<style id="student-group-pro-css">').html(`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

        /* Fondo y Contenedor Principal */
        body[data-route^="Form/Student Group"] {
            background-color: #f1f5f9 !important;
        }
        body[data-route^="Form/Student Group"] * {
            font-family: 'Outfit', sans-serif !important;
        }
        body[data-route^="Form/Student Group"] .page-container {
            max-width: 1200px !important;
            margin: 30px auto !important;
            background: transparent !important;
        }
        body[data-route^="Form/Student Group"] .layout-main-section {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        body[data-route^="Form/Student Group"] .form-page {
            background: transparent !important;
            border: none !important;
        }

        /* Tarjetas Flotantes Gigantes (Section Breaks) */
        body[data-route^="Form/Student Group"] .frappe-control[data-fieldtype="Section Break"] {
            background: #ffffff !important;
            border-radius: 20px !important;
            padding: 40px !important;
            margin-bottom: 35px !important;
            box-shadow: 0 20px 40px rgba(0,0,0,0.03), 0 1px 3px rgba(0,0,0,0.05) !important;
            border: 1px solid rgba(226,232,240, 0.8) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        }
        body[data-route^="Form/Student Group"] .frappe-control[data-fieldtype="Section Break"]:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 30px 60px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.05) !important;
        }

        /* Títulos de Sección Impresionantes */
        body[data-route^="Form/Student Group"] .section-head {
            font-size: 26px !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            letter-spacing: -0.5px !important;
            border-bottom: 3px solid #f1f5f9 !important;
            margin-bottom: 30px !important;
            padding-bottom: 15px !important;
        }

        /* Ocultar tarjetas para HTML y Tab Breaks */
        body[data-route^="Form/Student Group"] .frappe-control[data-fieldtype="HTML"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin-bottom: 35px !important;
        }

        /* Inputs de Texto Premium */
        body[data-route^="Form/Student Group"] .form-control, 
        body[data-route^="Form/Student Group"] .awesomplete > input {
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
        body[data-route^="Form/Student Group"] .form-control:focus, 
        body[data-route^="Form/Student Group"] .awesomplete > input:focus {
            background-color: #ffffff !important;
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15) !important;
            outline: none !important;
        }

        /* Etiquetas de Campos (Labels) Modernas */
        body[data-route^="Form/Student Group"] .control-label {
            font-size: 14px !important;
            font-weight: 700 !important;
            color: #64748b !important;
            text-transform: uppercase !important;
            letter-spacing: 0.8px !important;
            margin-bottom: 8px !important;
            display: block !important;
        }

        /* Selects especiales (Select) */
        body[data-route^="Form/Student Group"] select.form-control {
            appearance: none !important;
            cursor: pointer !important;
        }

        /* Checkboxes rediseñados */
        body[data-route^="Form/Student Group"] .checkbox .label-area {
            font-size: 16px !important;
            font-weight: 600 !important;
            color: #334155 !important;
        }

        /* Tablas incrustadas */
        body[data-route^="Form/Student Group"] .grid-body {
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
        }

        /* Botón Obtener Estudiantes - Estilo Primario */
        body[data-route^="Form/Student Group"] [data-fieldname="get_students"] .btn-default {
            background-color: #6366f1 !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 10px !important;
            font-size: 16px !important;
            box-shadow: 0 4px 6px rgba(99, 102, 241, 0.2) !important;
        }
        
        body[data-route^="Form/Student Group"] [data-fieldname="get_students"] .btn-default:hover {
            background-color: #4f46e5 !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(99, 102, 241, 0.3) !important;
        }
      `).appendTo('head');
    }

    // Renderizar Banner HTML
    if (frm.fields_dict.custom_header) {
      const status_configs = {
        'Activo': { bg: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', icon: 'fa-check-circle' },
        'Borrador': { bg: 'linear-gradient(135deg, #64748b 0%, #475569 100%)', icon: 'fa-file-text' },
        'Inactivo': { bg: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', icon: 'fa-pause-circle' },
        'Cancelado': { bg: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', icon: 'fa-times-circle' }
      };

      const config = status_configs[frm.doc.status] || { bg: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)', icon: 'fa-graduation-cap' };
      const title = frm.doc.student_group_name || __('Nuevo Grupo de Estudiantes');
      const detail = [frm.doc.program, frm.doc.academic_term].filter(Boolean).join(' | ') || __('Complete los campos para comenzar');

      let html = `
                <div style="background: ${config.bg}; border-radius: 14px; padding: 30px; color: white; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 10px 20px -5px rgba(0,0,0,0.15); margin-bottom: 25px;">
                    <div style="display: flex; align-items: center;">
                        <div style="background: rgba(255,255,255,0.2); width: 60px; height: 60px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-right: 20px; font-size: 28px;">
                            <i class="fa ${config.icon}"></i>
                        </div>
                        <div>
                            <h2 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">${title}</h2>
                            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px; font-weight: 500;">${detail}</p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: rgba(255,255,255,0.2); padding: 8px 18px; border-radius: 50px; font-weight: 700; font-size: 12px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.4);">
                            ${frm.doc.status || 'Borrador'}
                        </span>
                    </div>
                </div>
            `;
      $(frm.fields_dict.custom_header.wrapper).html(html);
    }
  },

  setup_dashboard: function (frm) {
    frm.dashboard.clear_indicators();

    // Indicador de Inscritos vs Capacidad
    if (frm.doc.max_strength > 0) {
      let percent = (frm.doc.enrolled_count / frm.doc.max_strength) * 100;
      let color = percent >= 100 ? 'red' : (percent >= 80 ? 'orange' : 'green');
      frm.dashboard.add_indicator(
        __('Cupos: {0}/{1}', [frm.doc.enrolled_count, frm.doc.max_strength]),
        color
      );
    }

    // Indicador de Modalidad
    if (frm.doc.modality) {
      frm.dashboard.add_indicator(
        __('Modalidad: {0}', [frm.doc.modality]),
        'blue'
      );
    }
  },

  check_enrollment_status: function (frm) {
    if (!frm.doc.academic_term) return;

    frm.call('get_enrollment_status').then(r => {
      if (!r || !r.message) return;
      const status = r.message;

      // RF-21: Indicador de matrícula en dashboard
      if (status.open) {
        frm.dashboard.add_indicator(
          __('Matrícula Abierta: {0} — {1}', [
            frappe.datetime.str_to_user(status.enrollment_start_date),
            frappe.datetime.str_to_user(status.enrollment_end_date),
          ]),
          'green'
        );
        // RF-22: Advertencia de restricción de edición
        frm.set_intro(
          __('⚠️ El período de matrícula está activo ({0} al {1}). Solo un Administrador del Sistema puede editar esta oferta.', [
            frappe.datetime.str_to_user(status.enrollment_start_date),
            frappe.datetime.str_to_user(status.enrollment_end_date),
          ]),
          'orange'
        );
      } else if (status.enrollment_start_date) {
        frm.dashboard.add_indicator(
          __('Matrícula Cerrada'),
          'grey'
        );
      }
    });
  },

  setup_buttons: function (frm) {
    frm.clear_custom_buttons();

    // Grupo: Gestión Académica (Lo más usado)
    frm.add_custom_button(__('<i class="fa fa-calendar-check-o"></i> Asistencias'), () => {
      frappe.set_route('Form', 'Student Attendance Tool', {
        based_on: 'Student Group',
        student_group: frm.doc.name
      });
    }, __('Tools'));

    frm.add_custom_button(__('<i class="fa fa-clock-o"></i> Horarios'), () => {
      frappe.set_route('Form', 'Course Scheduling Tool', {
        student_group: frm.doc.name
      });
    }, __('Tools'));

    // Grupo: Comunicación
    frm.add_custom_button(__('Actualizar Correos Tutores'), () => {
      frappe.call({
        method: 'education.education.api.update_email_group',
        args: { doctype: 'Student Group', name: frm.doc.name },
        freeze: true,
        callback: () => frappe.show_alert({ message: __('Lista de correos actualizada'), indicator: 'blue' })
      });
    }, __('Actions'));

    frm.add_custom_button(__('Ver Newsletters'), () => {
      frappe.set_route('List', 'Newsletter', {
        'Newsletter Email Group.email_group': frm.doc.name
      });
    }, __('View'));

    // Acción de Peligro: Cancelar
    if (frm.doc.status !== 'Cancelado') {
      frm.add_custom_button(__('Cancelar Oferta'), () => {
        frappe.confirm(__('¿Estás seguro de que deseas <b>cancelar</b> esta oferta?'), () => {
          frm.call({
            method: 'cancel_offer',
            callback: (r) => {
              if (!r.exc) {
                frappe.show_alert({ message: __('Oferta Cancelada'), indicator: 'red' });
                frm.reload_doc();
              }
            }
          });
        });
      }, __('Actions'));

      $(`[data-label='${__("Cancelar Oferta")}']`).addClass('btn-danger').css('color', 'white');
    }
  },

  // --- LÓGICA DE NEGOCIO ---

  group_based_on: function (frm) {
    const is_batch = frm.doc.group_based_on === 'Batch';
    const is_course = frm.doc.group_based_on === 'Course';

    if (is_batch) frm.set_value('course', null);

    frm.set_df_property('program', 'reqd', is_batch ? 1 : 0);
    frm.set_df_property('course', 'reqd', is_course ? 1 : 0);
  },

  modality: function (frm) {
    // UX: Ocultar classroom si es virtual
    frm.toggle_display('classroom', frm.doc.modality !== 'Virtual');
    if (frm.doc.modality === 'Virtual' && frm.doc.classroom) {
      frm.set_value('classroom', null);
    }
  },

  setup_student_query: function (frm) {
    frm.set_query('student', 'students', () => {
      let filters = { group_based_on: frm.doc.group_based_on };
      if (frm.doc.group_based_on !== 'Activity') {
        Object.assign(filters, {
          academic_year: frm.doc.academic_year,
          academic_term: frm.doc.academic_term,
          program: frm.doc.program,
          batch: frm.doc.batch,
          student_category: frm.doc.student_category,
          course: frm.doc.course,
          student_group: frm.doc.name,
        });
      }
      return {
        query: 'education.education.doctype.student_group.student_group.fetch_students',
        filters: filters,
      };
    });
  },

  get_students: function (frm) {
    if (!['Batch', 'Course'].includes(frm.doc.group_based_on)) {
      frappe.msgprint(__('Para grupos por <b>Actividad</b>, agregue estudiantes manualmente.'));
      return;
    }

    if (!frm.doc.academic_year) {
      frappe.throw(__('Por favor, seleccione un Año Académico.'));
    }

    frappe.call({
      method: 'education.education.doctype.student_group.student_group.get_students',
      args: {
        academic_year: frm.doc.academic_year,
        academic_term: frm.doc.academic_term,
        group_based_on: frm.doc.group_based_on,
        program: frm.doc.program,
        batch: frm.doc.batch,
        student_category: frm.doc.student_category,
        course: frm.doc.course,
      },
      freeze: true,
      freeze_message: __('Buscando estudiantes coincidentes...'),
      callback: function (r) {
        if (r.message && r.message.length > 0) {
          let current_students = (frm.doc.students || []).map(s => s.student);
          let max_roll = Math.max(0, ...((frm.doc.students || []).map(s => s.group_roll_number || 0)));

          r.message.forEach(d => {
            if (!current_students.includes(d.student)) {
              let child = frm.add_child('students');
              child.student = d.student;
              child.student_name = d.student_name;
              child.active = d.active === 0 ? 0 : 1;
              child.group_roll_number = ++max_roll;
            }
          });
          frm.refresh_field('students');
          frm.save();
          frappe.show_alert({ message: __('Estudiantes importados con éxito'), indicator: 'green' });
        } else {
          frappe.msgprint(__('No se encontraron nuevos estudiantes para estos criterios.'));
        }
      },
    });
  },

  // Actualizar banner al cambiar campos clave
  student_group_name: function (frm) { frm.trigger('render_custom_ui'); },
  program: function (frm) { frm.trigger('render_custom_ui'); },
  status: function (frm) { frm.trigger('render_custom_ui'); },
  academic_year: function (frm) { frm.trigger('render_custom_ui'); },
  academic_term: function (frm) {
    frm.trigger('render_custom_ui');
    if (!frm.is_new()) frm.trigger('check_enrollment_status');
  }
});

// Mejora en Tabla de Instructores
frappe.ui.form.on('Student Group Instructor', {
  instructors_add: function (frm) {
    frm.fields_dict['instructors'].grid.get_field('instructor').get_query = (doc) => {
      let current = (doc.instructors || []).map(i => i.instructor).filter(Boolean);
      return {
        filters: [
          ['Instructor', 'name', 'not in', current],
          ['Instructor', 'status', '=', 'Active']
        ]
      };
    };
  }
});