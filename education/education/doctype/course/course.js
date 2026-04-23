frappe.ui.form.on('Course', {
  refresh: function (frm) {
    if (!frm.doc.__islocal) {
      frm.add_custom_button(__('Add to Programs'), function () {
        frm.trigger('add_course_to_programs')
      })
    }

    frm.set_query('default_grading_scale', function () {
      return {
        filters: {
          docstatus: 1,
        },
      }
    })
  },

  after_save: function (frm) {
    if (frm.doc.moodle_course_id) {
      sync_course_to_moodle(frm);
    }
  },

  add_course_to_programs: function (frm) {
    get_programs_without_course(frm.doc.name).then((r) => {
      if (r.message.length) {
        frappe.prompt(
          [
            {
              fieldname: 'programs',
              label: __('Programs'),
              fieldtype: 'MultiSelectPills',
              get_data: function () {
                return r.message
              },
            },
            {
              fieldtype: 'Check',
              label: __('Is Mandatory'),
              fieldname: 'mandatory',
            },
          ],
          function (data) {
            frappe.call({
              method: 'education.education.doctype.course.course.add_course_to_programs',
              args: {
                course: frm.doc.name,
                programs: data.programs,
                mandatory: data.mandatory,
              },
              callback: function (r) {
                if (!r.exc) {
                  frm.reload_doc()
                }
              },
              freeze: true,
              freeze_message: __('...Adding Course to Programs'),
            })
          },
          __('Add Course to Programs'),
          __('Add')
        )
      } else {
        frappe.msgprint(__('This course is already added to the existing programs'))
      }
    })
  },
})

function sync_course_to_moodle(frm) {
  frappe.call({
    method: 'education.moodle_integration.api.sync_course_to_moodle',
    args: { course_name: frm.doc.name },
    callback: function (r) {
      if (r.message && (r.message.status === 'created' || r.message.status === 'updated')) {
        frappe.show_alert({ message: __('✓ Curso sincronizado con Moodle'), indicator: 'green' });
      } else if (r.message && r.message.status === 'error') {
        frappe.show_alert({ message: __('✗ Error al sincronizar: ') + r.message.message, indicator: 'red' });
      }
    },
  });
}

frappe.ui.form.on('Course Topic', {
  topics_add: function (frm) {
    frm.fields_dict['topics'].grid.get_field('topic').get_query = function (doc) {
      var topics_list = []
      if (!doc.__islocal) topics_list.push(doc.name)
      $.each(doc.topics, function (idx, val) {
        if (val.topic) topics_list.push(val.topic)
      })
      return { filters: [['Topic', 'name', 'not in', topics_list]] }
    }
  },
})

let get_programs_without_course = function (course) {
  return frappe.call({
    type: 'GET',
    method: 'education.education.doctype.course.course.get_programs_without_course',
    args: { course: course },
  })
}
