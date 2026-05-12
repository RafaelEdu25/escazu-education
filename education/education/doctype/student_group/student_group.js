/**
 * UI Estándar para Student Group
 * Enfoque: Estabilidad y funcionalidad nativa de Frappe.
 */

frappe.ui.form.on('Student Group', {
  onload: function (frm) {
    // Consultas dinámicas
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
    if (!frm.is_new()) {
      // 1. Configurar Dashboard (Indicadores nativos)
      frm.trigger('setup_dashboard');

      // 2. Configurar Botones de Acción
      frm.trigger('setup_buttons');

      // 3. Mensaje de introducción nativo
      if (!frm.doc.students || frm.doc.students.length === 0) {
        frm.set_intro(__('Este grupo no tiene estudiantes. Use el botón "Obtener Estudiantes" para poblar la lista.'), 'orange');
      } else {
        frm.set_intro(null);
      }
    }

    // 4. Lógica de visibilidad
    frm.trigger('modality');
  },

  setup_dashboard: function (frm) {
    frm.dashboard.clear_indicators();

    // Indicador de Inscritos vs Capacidad
    if (frm.doc.max_strength > 0) {
      let percent = (frm.doc.enrolled_count / frm.doc.max_strength) * 100;
      let color = percent >= 100 ? 'red' : (percent >= 80 ? 'orange' : 'green');
      frm.dashboard.add_indicator(
        __('Cupos: {0}/{1}', [frm.doc.enrolled_count, frm.doc.max_strength]),
        color,
        'fa-users'
      );
    }

    // Indicador de Modalidad
    if (frm.doc.modality) {
      frm.dashboard.add_indicator(
        __('Modalidad: {0}', [frm.doc.modality]),
        'blue',
        frm.doc.modality === 'Virtual' ? 'fa-laptop' : 'fa-building'
      );
    }
  },

  setup_buttons: function (frm) {
    frm.clear_custom_buttons();

    // Herramientas Académicas
    frm.add_custom_button(__('Asistencias'), () => {
      frappe.set_route('Form', 'Student Attendance Tool', {
        based_on: 'Student Group',
        student_group: frm.doc.name
      });
    }, __('Herramientas'));

    frm.add_custom_button(__('Horarios'), () => {
      frappe.set_route('Form', 'Course Scheduling Tool', {
        student_group: frm.doc.name
      });
    }, __('Herramientas'));

    // Acciones de Comunicación
    frm.add_custom_button(__('Actualizar Correos Tutores'), () => {
      frappe.call({
        method: 'education.education.api.update_email_group',
        args: { doctype: 'Student Group', name: frm.doc.name },
        freeze: true,
        callback: () => frappe.show_alert({ message: __('Lista de correos actualizada'), indicator: 'blue' })
      });
    }, __('Acciones'));

    // Acción de Cancelar
    if (frm.doc.status !== 'Cancelado') {
      frm.add_custom_button(__('Cancelar Oferta'), () => {
        frappe.confirm(__('¿Estás seguro de que deseas cancelar esta oferta?'), () => {
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
      }, __('Acciones'));
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
      frappe.msgprint(__('Para grupos por Actividad, agregue estudiantes manualmente.'));
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
      freeze_message: __('Buscando estudiantes...'),
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
          frappe.show_alert({ message: __('Estudiantes importados'), indicator: 'green' });
        }
      },
    });
  }
});

// Tabla de Instructores
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