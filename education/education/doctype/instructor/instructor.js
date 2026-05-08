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
			method: 'education.education.doctype.instructor.instructor.get_active_assignments',
			args: { instructor: frm.doc.name },
			callback: function (r) {
				const data = r.message || {}
				const horarios = data.schedules || []
				const grupos = data.groups || []
				const total = horarios.length + grupos.length

				if (total === 0) return

				// Revertir el campo status — no permitir guardar con Inactive si hay asignaciones
				frappe.model.set_value(frm.doctype, frm.docname, 'status', 'Active')
				frm.refresh_field('status')

				let filas = horarios.map(c => `<tr>
					<td><span class="badge" style="background:#3498db;color:#fff">Horario</span></td>
					<td>${c.course}</td>
					<td>${frappe.datetime.str_to_user(c.schedule_date)}</td>
					<td><a href="/app/course-schedule/${c.name}" target="_blank">${c.name}</a></td>
				</tr>`).join('')

				filas += grupos.map(g => `<tr>
					<td><span class="badge" style="background:#8e44ad;color:#fff">Grupo</span></td>
					<td>${g.course || '—'}</td>
					<td>—</td>
					<td><a href="/app/student-group/${g.parent}" target="_blank">${g.parent}</a></td>
				</tr>`).join('')

				const tabla = `
					<p>Este instructor tiene <strong>${total} asignación(es) activa(s)</strong>:</p>
					<table class="table table-bordered table-sm" style="margin-top:10px">
						<thead>
							<tr><th>Tipo</th><th>Curso</th><th>Fecha</th><th>Referencia</th></tr>
						</thead>
						<tbody>${filas}</tbody>
					</table>
					<p style="color:#e74c3c; margin-top:12px">
						<strong>⚠️ Debe reasignar un instructor a estas asignaciones antes de poder desactivar este perfil.</strong>
					</p>
				`

				frappe.msgprint({
					title: __('Advertencia: Instructor con Cursos Activos'),
					message: tabla,
					indicator: 'red',
				})
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