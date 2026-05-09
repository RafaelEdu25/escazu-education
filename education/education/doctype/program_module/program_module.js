frappe.ui.form.on("Program Module", {
	refresh(frm) {
		recalcular_horas(frm);
	},
});

frappe.ui.form.on("Program Module Course", {
	theory_hours(frm) { recalcular_horas(frm); },
	practical_hours(frm) { recalcular_horas(frm); },

	course(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.course) return;

		// Bloquear cursos de tipo Libre
		frappe.db.get_value("Course", row.course, "course_type").then(({ message }) => {
			const tipo = message && message.course_type;
			if (tipo === "Libre") {
				frappe.msgprint(
					__("La asignatura '{0}' es de tipo Libre y no puede agregarse a un módulo.", [row.course])
				);
				frappe.model.set_value(cdt, cdn, "course", "");
				return;
			}

			// Bloquear duplicados
			const duplicado = frm.doc.courses_in_module.some(
				(r) => r.course === row.course && r.name !== cdn
			);
			if (duplicado) {
				frappe.msgprint(
					__("La asignatura '{0}' ya está en el módulo. Cada asignatura debe aparecer una sola vez.", [row.course])
				);
				frappe.model.set_value(cdt, cdn, "course", "");
			}
		});
	},
});

function recalcular_horas(frm) {
	let theory = 0, practical = 0;
	(frm.doc.courses_in_module || []).forEach((r) => {
		theory += r.theory_hours || 0;
		practical += r.practical_hours || 0;
	});
	frappe.model.set_value(frm.doctype, frm.docname, "theory_hours", theory);
	frappe.model.set_value(frm.doctype, frm.docname, "practical_hours", practical);
	frappe.model.set_value(frm.doctype, frm.docname, "total_hours", theory + practical);
}
