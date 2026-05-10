frappe.ui.form.on('Course', {

  theory_hours: function (frm) { calcular_horas_curso(frm); },
  practical_hours: function (frm) { calcular_horas_curso(frm); },

  refresh: function (frm) {
    if (!frm.doc.__islocal) {
      frm.add_custom_button(__('Add to Programs'), function () {
        frm.trigger('add_course_to_programs')
      })

      // RF-26 / RF-27: botones de cambio de estado
      const status = frm.doc.course_status

      if (status === 'Inactivo') {
        frm.add_custom_button(__('Activar Curso'), () => {
          set_course_status(frm, 'Activo')
        }, __('Estado'))
      }

      if (status === 'Activo') {
        frm.add_custom_button(__('Desactivar Curso'), () => {
          set_course_status(frm, 'Inactivo')
        }, __('Estado'))
      }

      if (status !== 'Cancelado') {
        frm.add_custom_button(__('Cancelar Curso'), () => {
          frappe.confirm(
            __('¿Está seguro de cancelar este curso? Esta acción no puede revertirse si no existen estudiantes matriculados y conservará el registro como histórico.'),
            () => set_course_status(frm, 'Cancelado')
          )
        }, __('Estado'))
      }

      // El campo siempre es read-only: el cambio de estado solo se hace por los botones del grupo Estado
      frm.set_df_property('course_status', 'read_only', 1)
    }

    frm.set_query('default_grading_scale', function () {
      return { filters: { docstatus: 1 } }
    })
    toggle_plan_estudios(frm)
    if (frm.fields_dict.course_documents) {
      setup_documents_grid(frm)
    }
  },

  after_save: function (frm) {
    
    let _orig = frappe.msgprint.bind(frappe)
    frappe.msgprint = function (opts) {
      let msg = typeof opts === 'string' ? opts : (opts?.message || '')
      let parsed = msg
      try { parsed = typeof msg === 'string' ? JSON.parse(msg) : msg } catch(e) {}
      let actual_msg = typeof parsed === 'object' ? (parsed.message || '') : parsed
      
      if (!actual_msg || actual_msg === 'Saved') return
      return _orig(opts)
    }

    if (frm.doc.moodle_course_id) {
      sync_course_to_moodle(frm)
    }
  },

  course_type: function (frm) {
    toggle_plan_estudios(frm)
  },

  add_course_to_programs: function (frm) {
    get_programs_without_course(frm.doc.name).then((r) => {
      if (r.message && r.message.length) {
        frappe.prompt(
          [
            {
              fieldname: 'programs',
              label: __('Programs'),
              fieldtype: 'MultiSelectPills',
              get_data: function () { return r.message },
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
                if (!r.exc) frm.reload_doc()
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


frappe.ui.form.on('Course Topic', {
  topics_add: function (frm) {
    frm.fields_dict['topics'].grid.get_field('topic').get_query = function (doc) {
      let topics_list = []
      if (!doc.__islocal) topics_list.push(doc.name)
      $.each(doc.topics, function (idx, val) {
        if (val.topic) topics_list.push(val.topic)
      })
      return { filters: [['Topic', 'name', 'not in', topics_list]] }
    }
  },
})


// RF-17: patch toggle_view para interceptar apertura del grid form nativo
;(function patch_grid_prototype() {
  function try_patch() {
    let GridClass = frappe.ui?.form?.Grid
    if (!GridClass) { setTimeout(try_patch, 100); return }
    if (GridClass.prototype._rf17_patched) return
    GridClass.prototype._rf17_patched = true

    let _orig = GridClass.prototype.toggle_view

    GridClass.prototype.toggle_view = function (show, callback) {
      if (show && this.doctype === 'Course Document') {
        let frm_doc = this.frm

        let row_data = null
        let cdn = this.open_grid_row?.doc?.name
          || this.grid_form?.doc?.name
          || this.get_selected()?.[0]

        if (cdn && frm_doc?.doc?.course_documents) {
          row_data = frm_doc.doc.course_documents.find(r => r.name === cdn)
        }

        setTimeout(() => open_document_dialog(frm_doc, row_data || null), 0)
        if (typeof callback === 'function') callback()
        return
      }
      return _orig.call(this, show, callback)
    }
  }
  try_patch()
})()


function setup_documents_grid(frm) {
  let grid = frm.fields_dict.course_documents.grid

  if (!grid._rf17_click_interceptor) {
    grid._rf17_click_interceptor = true

    frm.fields_dict.course_documents.$wrapper[0].addEventListener('click', function (e) {
   
      let node = e.target
      while (node && node !== this) {
    
        if (node.tagName === 'A' && node.href) {
          e.stopImmediatePropagation()
          e.preventDefault()
          window.open(node.href, '_blank')
          return
        }
       
        if (node.dataset?.fieldname === 'document_file') {
          e.stopImmediatePropagation()
          e.preventDefault()
       
          let link = node.querySelector('a[href]')
          if (link) window.open(link.href, '_blank')
          return
        }
        node = node.parentElement
      }

      // Dejar pasar controles propios, cabecera y footer
      let $t = $(e.target)
      if ($t.closest('.btn-add-documento, .grid-footer, .grid-heading-row, .grid-toolbar, .row-check').length) return

      // Solo filas de datos
      let $row = $t.closest('.grid-row')
      if (!$row.length) return

      e.stopImmediatePropagation()
      e.preventDefault()

      let row_name = $row.attr('data-name')
      let row_data = null
      if (row_name && frm.doc.course_documents) {
        row_data = frm.doc.course_documents.find(r => r.name === row_name)
      }
      if (!row_data && frm.doc.course_documents) {
        let idx = $row.attr('data-idx')
        if (idx !== undefined) {
          row_data = frm.doc.course_documents.find(r => String(r.idx) === String(idx))
        }
      }

      open_document_dialog(frm, row_data || null)

    }, true)
  }

  if (!grid._observer_rf17) {
    grid._observer_rf17 = new MutationObserver(function () {
      apply_grid_controls(frm)
    })
    grid._observer_rf17.observe(grid.wrapper[0], { childList: true, subtree: true })
  }

  apply_grid_controls(frm)
}

function apply_grid_controls(frm) {
  let grid = frm.fields_dict.course_documents?.grid
  if (!grid) return

  let $w = grid.wrapper

  // Ocultar controles nativos que no queremos
  $w.find([
    '.grid-add-row',
    '.grid-duplicate-row',
    '.grid-insert-row-below',
    '.grid-insert-row',
    '.grid-download',
    '.grid-upload',
    '.grid-bulk-actions',
    '.row-actions',
  ].join(', ')).hide()

  $w.find('button').each(function () {
    let txt = $(this).text().trim()
    if (txt === 'Duplicate row') $(this).hide()
  })

  $w.find('.grid-remove-rows').hide()

  if (!$w.find('.btn-add-documento').length) {
    let $footer = $w.find('.grid-footer')

    let $toolbar = $('<div class="rf17-footer-toolbar" style="display:flex; gap:8px; margin-top:10px;"></div>')

    let $add_btn = $(
      `<button class="btn btn-xs btn-secondary btn-add-documento">
        + ${__('Agregar Documento')}
      </button>`
    )
    $add_btn.on('click', function (e) {
      e.stopPropagation()
      open_document_dialog(frm, null)
    })

    let $del_btn = $(
      `<button class="btn btn-xs btn-danger btn-delete-documentos" style="display:none;">
        🗑 ${__('Eliminar seleccionados')}
      </button>`
    )
  $del_btn.on('click', function (e) {
    e.stopPropagation()
    let selected = grid.get_selected()
    if (!selected.length) return

  frappe.confirm(
    __('¿Eliminar {0} documento(s) seleccionado(s)?', [selected.length]),
    function () {
      selected.forEach(name => {
        frm.get_field('course_documents').grid.grid_rows_by_docname[name]?.remove()
      })
      frm.refresh_field('course_documents')
      frm.dirty()

      grid.selected_children = {}
      if (grid.header_row) {
        grid.header_row.$check?.prop('checked', false)
      }

      setTimeout(() => {
        toggle_delete_btn($w, grid, $del_btn)
      }, 100)

      frappe.show_alert({
        message: __('Documento(s) eliminado(s). Recuerda guardar.'),
        indicator: 'orange'
      })
    }
  )
  })

    $toolbar.append($add_btn).append($del_btn)
    $footer.prepend($toolbar)

    let $grid_body = $w.find('.grid-body')
    let _checkbox_observer = new MutationObserver(function () {
      toggle_delete_btn($w, grid, $del_btn)
    })
    _checkbox_observer.observe($grid_body[0], { attributes: true, subtree: true, attributeFilter: ['class'] })

    $w[0].addEventListener('change', function (e) {
      if ($(e.target).is(':checkbox')) {
        toggle_delete_btn($w, grid, $del_btn)
      }
    }, true)
  }
}

function toggle_delete_btn($w, grid, $del_btn) {
  let selected = grid.get_selected ? grid.get_selected() : []
  if (selected.length > 0) {
    $del_btn.show()
    $del_btn.text(`🗑 ${__('Eliminar')} (${selected.length})`)
  } else {
    $del_btn.hide()
  }
}

function open_document_dialog(frm, existing_row) {
  let is_edit   = !!existing_row
  let btn_label = is_edit ? __('Guardar') : __('Agregar')
  let pending_file = is_edit ? (existing_row.document_file || '') : ''

  let dialog = new frappe.ui.Dialog({
    title: is_edit ? __('Editar Documento') : __('Agregar Documento'),
    fields: [
      {
        fieldname: 'document_type',
        fieldtype: 'Select',
        label: __('Tipo'),
        options: 'Guia de aprendizaje\nPlan de estudios\nMaterial didáctico\nEvaluación\nOtro',
        reqd: 1,
        default: is_edit ? existing_row.document_type : 'Guia de aprendizaje',
      },
      {
        fieldname: 'document_name',
        fieldtype: 'Data',
        label: __('Nombre'),
        reqd: 1,
        default: is_edit ? existing_row.document_name : '',
      },
      {
        fieldname: 'document_file',
        fieldtype: 'Attach',
        label: __('Archivo'),
        reqd: 1,
        default: is_edit ? existing_row.document_file : '',
      },
      {
        fieldname: 'notes',
        fieldtype: 'Small Text',
        label: __('Notas'),
        default: is_edit ? existing_row.notes : '',
      },
    ],
  })

  dialog.set_primary_action(btn_label, function () {
    let values = dialog.get_values(true)
    if (!values) return

    let archivo = pending_file || values.document_file

    if (!values.document_type) {
      frappe.msgprint({ message: __('El campo <b>Tipo</b> es obligatorio.'), indicator: 'red' })
      return
    }
    if (!values.document_name?.trim()) {
      frappe.msgprint({ message: __('El campo <b>Nombre</b> es obligatorio.'), indicator: 'red' })
      return
    }
    if (!archivo) {
      frappe.msgprint({ message: __('Debe adjuntar un <b>Archivo</b>.'), indicator: 'red' })
      return
    }

    if (is_edit) {
      frappe.model.set_value(existing_row.doctype, existing_row.name, 'document_type', values.document_type)
      frappe.model.set_value(existing_row.doctype, existing_row.name, 'document_name', values.document_name.trim())
      frappe.model.set_value(existing_row.doctype, existing_row.name, 'document_file', archivo)
      frappe.model.set_value(existing_row.doctype, existing_row.name, 'notes',         values.notes || '')
    } else {
      let new_row           = frm.add_child('course_documents')
      new_row.document_type = values.document_type
      new_row.document_name = values.document_name.trim()
      new_row.document_file = archivo
      new_row.notes         = values.notes || ''
    }

    frm.refresh_field('course_documents')
    dialog.hide()

    frappe.show_alert({
      message: is_edit
        ? __('Documento actualizado. Recuerda guardar el curso.')
        : __('Documento agregado. Recuerda guardar el curso.'),
      indicator: 'blue',
    })
  })

  dialog.set_secondary_action_label(__('Cancelar'))
  dialog.set_secondary_action(function () { dialog.hide() })

  let field_file = dialog.fields_dict.document_file
  let orig_set_input = field_file.set_input.bind(field_file)
  field_file.set_input = function (val) {
    orig_set_input(val)
    if (val) {
      pending_file = val
      setTimeout(() => {
        let name_val = dialog.get_value('document_name')
        if (!name_val) {
          let clean = val.split('/').pop()
            .replace(/\.[^/.]+$/, '')
            .replace(/[_-]/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase())
          dialog.set_value('document_name', clean)
        }
      }, 100)
    }
  }

  dialog.show()
}


function toggle_plan_estudios(frm) {
  const es_modular_tecnico = ['Modular', 'Técnico'].includes(frm.doc.course_type)
  frm.toggle_display('study_plan_section', es_modular_tecnico)
  frm.toggle_display('study_cycle', es_modular_tecnico)
  frm.toggle_display('approval_criteria', es_modular_tecnico)
}


function sync_course_to_moodle(frm) {
  frappe.call({
    method: 'education.moodle_integration.api.sync_course_to_moodle',
    args: { course_name: frm.doc.name },
    callback: function (r) {
      if (!r.message || typeof r.message !== 'object') return
      if (r.message.status === 'created' || r.message.status === 'updated') {
        frappe.show_alert({ message: __('✓ Curso sincronizado con Moodle'), indicator: 'green' })
      } else if (r.message.status === 'error') {
        frappe.show_alert({
          message: __('✗ Error al sincronizar: ') + r.message.message,
          indicator: 'red',
        })
      }
    },
  })
}


let get_programs_without_course = function (course) {
  return frappe.call({
    type: 'GET',
    method: 'education.education.doctype.course.course.get_programs_without_course',
    args: { course: course },
  })
}
// RF-26 / RF-27: cambia el estado del curso y guarda
function set_course_status(frm, new_status) {
  frappe.model.set_value(frm.doctype, frm.docname, 'course_status', new_status)
  frm.save().then(() => {
    const indicator = new_status === 'Activo' ? 'green'
      : new_status === 'Cancelado' ? 'red'
      : 'gray'
    frappe.show_alert({ message: __('Estado del curso actualizado a: {0}', [__(new_status)]), indicator })
  })
}


function calcular_horas_curso(frm) {
  const theory = frm.doc.theory_hours || 0;
  const practical = frm.doc.practical_hours || 0;
  frappe.model.set_value(frm.doctype, frm.docname, "total_hours", theory + practical);
}
