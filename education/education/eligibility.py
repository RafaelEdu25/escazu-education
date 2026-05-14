# Copyright (c) 2026, Antigravity and contributors
import frappe
from frappe import _
# Importamos cint y otras herramientas necesarias
from frappe.utils import getdate, today, date_diff, cint

@frappe.whitelist()
def check_program_eligibility(program, date_of_birth=None, applicant=None, is_new=0):
    # Ahora 'cint' ya funcionará porque lo importamos arriba
    is_new = cint(is_new)
    
    if not program or not date_of_birth:
        return {"eligible": True}

    try:
        prog_doc = frappe.get_doc("Program", program)
    except frappe.DoesNotExistError:
        return {"eligible": False, "message": _("El programa seleccionado no existe.")}

    errors = []

    # 1. Validación de Edad
    try:
        # Convertimos la fecha que viene del JS a objeto fecha de Python
        dob = getdate(date_of_birth)
        age = date_diff(today(), dob) / 365.25
        
        if prog_doc.min_age > 0 and age < prog_doc.min_age:
            errors.append(_("Edad insuficiente: El programa requiere {0} años y el aplicante tiene {1:.1f}.").format(prog_doc.min_age, age))
            
        if prog_doc.max_age > 0 and age > prog_doc.max_age:
            errors.append(_("Excede la edad máxima: El límite es {0} años y el aplicante tiene {1:.1f}.").format(prog_doc.max_age, age))
    except Exception as e:
        # Si la fecha no es válida, no bloqueamos, pero podrías loguear el error
        pass

    # 2. Validaciones adicionales si el registro ya existe en la DB
    if not is_new and applicant:
        if frappe.db.exists("Student Applicant", applicant):
            subject_doc = frappe.get_doc("Student Applicant", applicant)
            
            # Ejemplo: Nivel de estudios previos
            if prog_doc.min_education_level:
                levels = ["", "Primaria", "Secundaria", "Bachiller", "Técnico", "Licenciatura", "Ingeniería"]
                stu_level = getattr(subject_doc, "custom_estudios_previos", "")
                
                if stu_level in levels and levels.index(stu_level) < levels.index(prog_doc.min_education_level):
                    errors.append(_("Nivel de estudios insuficiente. Requerido: {0}.").format(prog_doc.min_education_level))

    if errors:
        return {"eligible": False, "message": " | ".join(errors)}
    
    return {"eligible": True}