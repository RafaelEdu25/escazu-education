// Copyright (c) 2015, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Program', {
  refresh: function (frm) {
    toggle_eligibility_fields(frm)
    if (!frm.doc.__islocal) {
      sync_modules(frm)
    }
  },

  program_type: function (frm) {
    toggle_eligibility_fields(frm)
  },

  accepts_disability: function (frm) {
    frm.toggle_display('disability_types', frm.doc.accepts_disability)
    if (!frm.doc.accepts_disability) {
      frm.clear_table('disability_types')
      frm.refresh_field('disability_types')
    }
  },

  after_save: function (frm) {
    sync_modules(frm)
  },
})

frappe.ui.form.on('Program Course', {
  courses_add: function (frm) {
    frm.fields_dict['courses'].grid.get_field('course').get_query = function (doc) {
      var courses_list = []
      $.each(doc.courses, function (idx, val) {
        if (val.course) courses_list.push(val.course)
      })
      return { filters: [['Course', 'name', 'not in', courses_list]] }
    }
  },
})

function toggle_eligibility_fields(frm) {
  const is_modular = ['Modular', 'Técnico'].includes(frm.doc.program_type)
  frm.toggle_display('section_break_modules', is_modular)
  frm.toggle_display('program_modules', is_modular)
  frm.toggle_display('disability_types', frm.doc.accepts_disability == 1)
}

function sync_modules(frm) {
  if (!['Modular', 'Técnico'].includes(frm.doc.program_type)) return
  frappe.call({
    method: 'frappe.client.get_list',
    args: {
      doctype: 'Program Module',
      filters: { program: frm.doc.name },
      fields: ['name', 'module_name', 'order_no', 'status', 'total_hours'],
      order_by: 'order_no asc',
    },
    callback: function (r) {
      if (!r.message) return
      frm.clear_table('program_modules')
      let total_hours = 0
      r.message.forEach(function (m) {
        frm.add_child('program_modules', {
          module: m.name,
          module_name: m.module_name,
          order_no: m.order_no,
          status: m.status,
          total_hours: m.total_hours || 0,
        })
        total_hours += m.total_hours || 0
      })
      frm.refresh_field('program_modules')
      frm.set_value('program_duration', total_hours)
    },
  })
}
