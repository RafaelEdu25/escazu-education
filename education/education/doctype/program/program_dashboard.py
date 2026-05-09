from frappe import _


def get_data():
	return {
		"fieldname": "program",
		"transactions": [
			{
				"label": _("Módulos"),
				"items": ["Program Module"],
			},
			{
				"label": _("Admission and Enrollments"),
				"items": ["Student Applicant", "Program Enrollment"],
			},
			{
				"label": _("Student Activity"),
				"items": ["Student Group", "Student Log"],
			},
			{
				"label": _("Assessment"),
				"items": ["Assessment Plan", "Assessment Result"],
			},
			{
				"label": _("Fee"),
				"items": ["Fee Structure", "Fee Schedule"],
			},
		],
	}
