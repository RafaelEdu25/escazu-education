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
      frm.set_df_property('course', 'read_only', 0)
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
