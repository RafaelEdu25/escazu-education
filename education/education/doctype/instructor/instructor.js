cur_frm.add_fetch('employee', 'department', 'department')
cur_frm.add_fetch('employee', 'image', 'image')

frappe.ui.form.on('Instructor', {
  
	employee: function (frm) {
		if (!frm.doc.employee) return
		frappe.db.get_value(
			'Employee',
			{ name: frm.doc.employee },
			'company',
			(d) => {
				frm.set_query('department', function () {
					return { filters: { company: d.company } }
				})
				frm.set_query('department', 'instructor_log', function () {
					return { filters: { company: d.company } }
				})
			}
		)
	},

	status: function (frm) {
		// Solo actuar si es un documento existente y se está pasando a Inactive
		if (frm.is_new() || frm.doc.status !== 'Inactive') return

		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Course Schedule',
				filters: {
					instructor: frm.doc.name,
					schedule_date: ['>=', frappe.datetime.get_today()],
				},
				fields: ['name', 'course', 'schedule_date'],
				order_by: 'schedule_date asc',
			},
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					const filas = r.message
						.map(c => `<tr>
							<td>${c.course}</td>
							<td>${frappe.datetime.str_to_user(c.schedule_date)}</td>
							<td><a href="/app/course-schedule/${c.name}" target="_blank">${c.name}</a></td>
						</tr>`)
						.join('')

					const tabla = `
						<p>Este instructor tiene <strong>${r.message.length} curso(s) activo(s)</strong> asignado(s):</p>
						<table class="table table-bordered table-sm" style="margin-top:10px">
							<thead>
								<tr>
									<th>Curso</th>
									<th>Fecha</th>
									<th>Horario</th>
								</tr>
							</thead>
							<tbody>${filas}</tbody>
						</table>
						<p style="color:#e74c3c; margin-top:10px">
							<strong>⚠️ Debe reasignar un instructor a estos cursos antes de confirmar la desactivación.</strong>
						</p>
					`

					frappe.msgprint({
						title: __('Advertencia: Instructor con Cursos Activos'),
						message: tabla,
						indicator: 'orange',
					})
				}
			},
		})
	},

	refresh: function (frm) {
		// --- Indicador visual de estado --- //
		if (frm.doc.status === 'Inactive') {
			frm.page.set_indicator(__('Inactivo'), 'red')
			frm.set_intro(
				__('Este instructor está desactivado y no puede ser asignado a nuevos cursos.'),
				'red'
			)
		} else if (frm.doc.status === 'Active') {
			frm.page.set_indicator(__('Activo'), 'green')
		}

		if (!frm.doc.__islocal) {
			frm.add_custom_button(
				__('As Examiner'),
				function () {
					frappe.new_doc('Assessment Plan', { examiner: frm.doc.name })
				},
				__('Assessment Plan')
			)
			frm.add_custom_button(
				__('As Supervisor'),
				function () {
					frappe.new_doc('Assessment Plan', { supervisor: frm.doc.name })
				},
				__('Assessment Plan')
			)

			// --- Botón: Ver cursos asignados --- //
			frm.add_custom_button(__('Ver Cursos Asignados'), function () {
				frappe.set_route('List', 'Course Schedule', {
					instructor: frm.doc.name,
				})
			})
		}

		// --- Queries originales --- //
		frm.set_query('employee', function (doc) {
			return { filters: { department: doc.department } }
		})

		frm.set_query('academic_term', 'instructor_log', function (_doc, cdt, cdn) {
			let d = locals[cdt][cdn]
			return { filters: { academic_year: d.academic_year } }
		})

		frm.set_query('course', 'instructor_log', function (_doc, cdt, cdn) {
			let d = locals[cdt][cdn]
			return {
				query:
					'education.education.doctype.program_enrollment.program_enrollment.get_program_courses',
				filters: { program: d.program },
			}
		})
	},

	before_save: function (frm) {
		// Validar email en cliente para feedback inmediato
		const email = frm.doc.email_id
		if (email) {
			const emailPattern = /^[\w\.-]+@[\w\.-]+\.\w{2,}$/
			if (!emailPattern.test(email)) {
				frappe.throw(__('El formato del correo electrónico no es válido: {0}', [email]))
			}
		}

		// Validar teléfono
		const phone = frm.doc.phone
		if (phone) {
			const cleanPhone = phone.replace(/[\s\-\(\)]/g, '')
			if (!/^\+?\d{7,15}$/.test(cleanPhone)) {
				frappe.throw(__('El formato del teléfono no es válido. Use solo números (7-15 dígitos).'))
			}
		}
	},
})