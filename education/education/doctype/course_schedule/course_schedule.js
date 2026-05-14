frappe.ui.form.on('Course Schedule', {
  refresh: function (frm) {
    if (!frm.doc.__islocal) {
      frm.add_custom_button(__('Mark Attendance'), function () {
        frappe.route_options = {
          based_on: 'Course Schedule',
          course_schedule: frm.doc.name,
        }
        frappe.set_route('Form', 'Student Attendance Tool')
      })
    }
    if (frm.doc.student_group) {
      frm.events.get_instructors(frm)
    }
  },

  onload: (frm) => {
    frm.set_query('instructor', () => {
      const filters = { status: 'Active' }
      if (frm.instructors && frm.instructors.length) {
        filters.instructor_name = ['in', frm.instructors]
      }
      return { filters }
    })

    frm.events.set_course_query(frm)
  },

<<<<<<< HEAD
  before_save: function (frm) {
    // Si el usuario ya confirmó el forzado, permitimos guardar
    if (frm.doc.__forced_save) {
      delete frm.doc.__forced_save;
      return;
    }

    // Detenemos el guardado para validar
    frappe.validated = false;

    frappe.call({
      method: "education.education.doctype.course_schedule.course_schedule.check_conflicts",
      args: {
        doc_name: frm.doc.name,
        instructor: frm.doc.instructor,
        room: frm.doc.room,
        schedule_date: frm.doc.schedule_date,
        from_time: frm.doc.from_time,
        to_time: frm.doc.to_time
      },
      callback: function (r) {
        if (r.message && r.message.length > 0) {
          // Si hay conflictos, mostramos diálogo de confirmación
          let msg = __("Se han detectado los siguientes conflictos:") + "<br><ul>";
          r.message.forEach(warn => { msg += `<li>${warn}</li>`; });
          msg += "</ul><br>" + __("¿Desea forzar el registro de todas formas?");

          frappe.confirm(msg,
            () => {
              // Si el usuario acepta:
              frm.doc.__forced_save = true;
              frm.save();
            },
            () => {
              // Si el usuario cancela:
              frappe.msgprint(__("Guardado cancelado para corregir conflictos."));
            }
          );
        } else {
          // Si no hay conflictos, procedemos normalmente
          frm.doc.__forced_save = true;
          frm.save();
        }
      }
    });
  },

  set_course_query: (frm) => {
    if (frm.doc.student_group) {
      frappe.db.get_value('Student Group', frm.doc.student_group, ['course', 'group_based_on', 'program_module'], (r) => {
        if (r && r.course && r.group_based_on === 'Course') {
          // Grupo tipo Course: curso fijo, autocompletar y bloquear
          frm.set_value('course', r.course)
          frm.set_df_property('course', 'read_only', 1)
        } else if (r && r.program_module) {
          // Grupo con módulo definido: filtrar solo los cursos del módulo
          frm.set_df_property('course', 'read_only', 0)
          frm.set_query('course', () => ({
            query: 'education.education.doctype.course_schedule.course_schedule.get_courses_for_student_group',
            filters: { student_group: frm.doc.student_group },
          }))
        } else {
          // Sin módulo ni curso: selección libre
          frm.set_df_property('course', 'read_only', 0)
          frm.set_query('course', () => ({}))
        }
      })
    } else {

      frm.set_query('course', () => ({}))
    }
  },

  student_group: (frm) => {
    frm.events.get_instructors(frm)
    frm.events.set_course_query(frm)
  },

  get_instructors: (frm) => {
    frm.instructors = []
    frappe.call({
      method: 'education.education.api.get_instructors',
      args: {
        student_group: frm.doc.student_group,
      },
      callback: function (data) {
        frm.instructors = data.message
      },
    })
  },
})