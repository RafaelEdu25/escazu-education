"""
Script de seed para el Centro Municipal de Formación para el Empleo (CMFE) — Escazú.
Inserta datos reales de programas, módulos, cursos e instructores.

Uso:
    bench --site education.localhost execute education.education.seed_cmfe.run

Para limpiar todos los datos insertados por el seed:
    bench --site education.localhost execute education.education.seed_cmfe.teardown
"""

import frappe


def run():
    frappe.set_user("Administrator")

    _make_academic_year()
    _make_academic_terms()
    _make_instructors()
    _make_cursos_libres()
    _make_programa_asistente_administrativo()
    _make_programa_comunicacion_datos()

    frappe.db.commit()
    print("\n✅ Seed CMFE completado exitosamente.\n")


# ------------------------------------------------------------------
# Año académico
# ------------------------------------------------------------------

def _make_academic_year():
    if not frappe.db.exists("Academic Year", "2026"):
        frappe.get_doc({
            "doctype": "Academic Year",
            "academic_year_name": "2026",
            "year_start_date": "2026-01-01",
            "year_end_date": "2026-12-31",
        }).insert(ignore_permissions=True)
        print("  ✔ Academic Year 2026")


# ------------------------------------------------------------------
# Términos académicos (trimestres) con ventanilla de matrícula
# ------------------------------------------------------------------

# Estructura del CMFE: 3 trimestres por año académico
# Trimestre I: enero–abril   | matrícula: 15 dic – 10 ene
# Trimestre II: mayo–agosto  | matrícula: 15 abr – 10 may
# Trimestre III: sep–dic     | matrícula: 15 ago – 10 sep
ACADEMIC_TERMS = [
    {
        "term_name": "Trimestre I",
        "term_start_date": "2026-01-12",
        "term_end_date": "2026-04-30",
        "enrollment_open": 1,
        "enrollment_start_date": "2025-12-15",
        "enrollment_end_date": "2026-01-10",
    },
    {
        "term_name": "Trimestre II",
        "term_start_date": "2026-05-04",
        "term_end_date": "2026-08-28",
        # Ventanilla abierta: el período de matrícula incluye hoy (2026-05-10)
        "enrollment_open": 1,
        "enrollment_start_date": "2026-05-04",
        "enrollment_end_date": "2026-05-30",
    },
    {
        "term_name": "Trimestre III",
        "term_start_date": "2026-09-07",
        "term_end_date": "2026-12-18",
        "enrollment_open": 0,
        "enrollment_start_date": "2026-08-15",
        "enrollment_end_date": "2026-09-05",
    },
]


def _make_academic_terms():
    for t in ACADEMIC_TERMS:
        # Frappe genera el name como "{academic_year} ({term_name})"
        title = f"2026 ({t['term_name']})"
        if frappe.db.exists("Academic Term", title):
            # Actualizar enrollment_open en caso de que haya cambiado
            frappe.db.set_value("Academic Term", title, {
                "enrollment_open": t["enrollment_open"],
                "enrollment_start_date": t["enrollment_start_date"],
                "enrollment_end_date": t["enrollment_end_date"],
            })
            estado = "🟢 ABIERTA" if t["enrollment_open"] else "🔴 cerrada"
            print(f"  ↻  Academic Term actualizado: {title} — ventanilla {estado}")
            continue
        frappe.get_doc({
            "doctype": "Academic Term",
            "academic_year": "2026",
            "term_name": t["term_name"],
            "term_start_date": t["term_start_date"],
            "term_end_date": t["term_end_date"],
            "enrollment_open": t["enrollment_open"],
            "enrollment_start_date": t["enrollment_start_date"],
            "enrollment_end_date": t["enrollment_end_date"],
        }).insert(ignore_permissions=True)
        estado = "🟢 ABIERTA" if t["enrollment_open"] else "🔴 cerrada"
        print(f"  ✔ Academic Term: {title} — ventanilla {estado}")


def _get_term(term_name):
    """Retorna el name del Academic Term dado su term_name en el año 2026.
    Frappe construye el name como '{year} ({term_name})'."""
    return f"2026 ({term_name})"


# ------------------------------------------------------------------
# Instructores del CMFE
# ------------------------------------------------------------------

def _make_instructors():
    instructores = [
        {
            "instructor_name": "María Elena González Monge",
            "last_name": "González Monge",
            "cedula": "109890123",
            "phone": "22616175",
            "email_id": "instructor1@gmail.com",
            "specialty": "Administración",
        },
        {
            "instructor_name": "Carlos Solís Esquivel",
            "last_name": "Solís Esquivel",
            "cedula": "205550100",
            "phone": "22616176",
            "email_id": "instructor2@gmail.com",
            "specialty": "Redes y Telecomunicaciones",
        },
        {
            "instructor_name": "Patricia Vargas Solano",
            "last_name": "Vargas Solano",
            "cedula": "304440200",
            "phone": "22616177",
            "email_id": "instructor3@gmail.com",
            "specialty": "Servicios al Cliente",
        },
        {
            "instructor_name": "Roberto Jiménez Bravo",
            "last_name": "Jiménez Bravo",
            "cedula": "403330300",
            "phone": "22616178",
            "email_id": "instructor4@gmail.com",
            "specialty": "Contabilidad",
        },
        {
            "instructor_name": "Karina Blanco Mora",
            "last_name": "Blanco Mora",
            "cedula": "502220400",
            "phone": "22616179",
            "email_id": "instructor5@gmail.com",
            "specialty": "Gestión Secretarial",
        },
        {
            "instructor_name": "Fabio Chacón Núñez",
            "last_name": "Chacón Núñez",
            "cedula": "601110500",
            "phone": "22616180",
            "email_id": "instructor6@gmail.com",
            "specialty": "Manipulación de Alimentos",
        },
    ]

    for data in instructores:
        existing = frappe.db.get_value("Instructor", {"instructor_name": data["instructor_name"]}, "name")
        if existing:
            print(f"  ⏭  Instructor ya existe: {data['instructor_name']}")
            continue
        data["doctype"] = "Instructor"
        data["naming_series"] = "INST-"
        data["supplier_company"] = _get_or_create_supplier()
        frappe.get_doc(data).insert(ignore_permissions=True)
        print(f"  ✔ Instructor: {data['instructor_name']}")


def _get_or_create_supplier():
    name = "Municipalidad de Escazú"
    if not frappe.db.exists("Supplier", name):
        frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": name,
            "supplier_group": _get_or_create_supplier_group(),
            "supplier_type": "Company",
        }).insert(ignore_permissions=True)
    return name


def _get_or_create_supplier_group():
    name = "Servicios"
    if not frappe.db.exists("Supplier Group", name):
        frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": name}).insert(ignore_permissions=True)
    return name


# ------------------------------------------------------------------
# Cursos Libres del CMFE
# ------------------------------------------------------------------

def _make_cursos_libres():
    cursos = [
        # Negocios y Finanzas
        ("Contabilidad Básica", "Libre", 24, 8),
        ("Excel Financiero", "Libre", 16, 16),
        ("Finanzas Personales", "Libre", 24, 8),
        ("Formulación de Proyectos", "Libre", 32, 16),
        ("Inicio de Emprendimiento", "Libre", 24, 16),
        ("Gestión de Equipos", "Libre", 24, 8),
        # Tecnología
        ("Principios de Ciberseguridad", "Libre", 24, 16),
        ("MS Access", "Libre", 16, 16),
        ("Herramientas de Comunicación a Distancia", "Libre", 16, 16),
        ("Marketing Web", "Libre", 24, 16),
        # Gastronomía
        ("Cocina Fusión", "Libre", 16, 32),
        ("Cocina Mexicana", "Libre", 16, 32),
        ("Cocina Saludable", "Libre", 16, 32),
        ("Manipulación de Alimentos", "Libre", 16, 8),
        ("Asado Básico", "Libre", 8, 24),
        # Hospitalidad
        ("Servicio al Cliente", "Libre", 24, 8),
        # Artesanía y Eventos
        ("Arreglos Florales", "Libre", 24, 16),
        ("Artículos para Fiestas", "Libre", 16, 24),
        ("Decoración de Eventos Especiales", "Libre", 24, 24),
        # Otros
        ("Huertos Orgánicos Urbanos", "Libre", 16, 24),
    ]

    for nombre, tipo, horas_t, horas_p in cursos:
        if frappe.db.exists("Course", nombre):
            print(f"  ⏭  Curso ya existe: {nombre}")
            continue
        frappe.get_doc({
            "doctype": "Course",
            "course_name": nombre,
            "course_status": "Activo",
            "course_type": tipo,
        }).insert(ignore_permissions=True)
        frappe.db.set_value("Course", nombre, {
            "theory_hours": horas_t,
            "practical_hours": horas_p,
            "total_hours": horas_t + horas_p,
        })
        print(f"  ✔ Curso Libre: {nombre} ({horas_t}h t + {horas_p}h p)")


# ------------------------------------------------------------------
# Programa: Asistente Administrativo (Plan Modular)
# ------------------------------------------------------------------

def _make_programa_asistente_administrativo():
    prog_name = "Asistente Administrativo"

    # Cursos modulares del programa
    cursos_mod = [
        ("Ofimática Empresarial", "Modular", 32, 16),
        ("Redacción Comercial y Ortografía", "Modular", 24, 8),
        ("Gestión de Archivo y Correspondencia", "Modular", 16, 8),
        ("Atención al Público y Protocolo", "Modular", 24, 8),
        ("Contabilidad Aplicada a la Empresa", "Modular", 32, 16),
        ("Planillas y Legislación Laboral", "Modular", 24, 16),
    ]
    for nombre, tipo, ht, hp in cursos_mod:
        if not frappe.db.exists("Course", nombre):
            frappe.get_doc({
                "doctype": "Course",
                "course_name": nombre,
                "course_status": "Activo",
                "course_type": tipo,
            }).insert(ignore_permissions=True)
            frappe.db.set_value("Course", nombre, {
                "theory_hours": ht,
                "practical_hours": hp,
                "total_hours": ht + hp,
            })
            print(f"  ✔ Curso Modular: {nombre}")

    # Coordinadora del programa
    coordinadora = frappe.db.get_value(
        "Instructor", {"instructor_name": "María Elena González Monge"}, "name"
    ) or frappe.db.get_value("Instructor", {}, "name")

    # Programa
    if not frappe.db.exists("Program", prog_name):
        frappe.get_doc({
            "doctype": "Program",
            "program_name": prog_name,
            "program_code": "ASIST-ADM",
            "program_type": "Modular",
            "program_status": "Activo",
            "coordinator": coordinadora,
            "min_age": 18,
            "max_age": 55,
            "min_education_level": "Secundaria",
        }).insert(ignore_permissions=True)
        print(f"  ✔ Programa: {prog_name}")
    else:
        print(f"  ⏭  Programa ya existe: {prog_name}")

    # Módulo I — Fundamentos de Administración (Trimestre I)
    mod1_name = _upsert_module(
        "Módulo I: Fundamentos de Administración",
        prog_name,
        theory_hours=56, practical_hours=24,
        min_grade=70, min_attendance=80,
        order_no=1,
    )
    mod1_doc = frappe.get_doc("Program Module", mod1_name)
    _append_course_if_missing(mod1_doc, "Ofimática Empresarial", 1)
    _append_course_if_missing(mod1_doc, "Redacción Comercial y Ortografía", 1)
    mod1_doc.save(ignore_permissions=True)
    print(f"  ✔ Módulo I — {mod1_doc.total_hours}h")

    # Módulo II — Gestión Administrativa (Trimestre II), prerrequisito: Módulo I
    mod2_name = _upsert_module(
        "Módulo II: Gestión Administrativa",
        prog_name,
        theory_hours=40, practical_hours=16,
        min_grade=70, min_attendance=80,
        order_no=2,
    )
    mod2_doc = frappe.get_doc("Program Module", mod2_name)
    _append_course_if_missing(mod2_doc, "Gestión de Archivo y Correspondencia", 1)
    _append_course_if_missing(mod2_doc, "Atención al Público y Protocolo", 1)
    if not any(r.prerequisite_module == mod1_name for r in mod2_doc.prerequisites):
        mod2_doc.append("prerequisites", {
            "prerequisite_module": mod1_name,
            "prerequisite_type": "Aprobación",
        })
    mod2_doc.save(ignore_permissions=True)
    print(f"  ✔ Módulo II — {mod2_doc.total_hours}h (prerreq: Módulo I)")

    # Módulo III — Contabilidad y Nómina (Trimestre III), prerrequisito: Módulo II
    # requires_certification=1: este módulo emite certificado al aprobarse
    mod3_name = _upsert_module(
        "Módulo III: Contabilidad y Nómina",
        prog_name,
        theory_hours=56, practical_hours=32,
        min_grade=70, min_attendance=80,
        order_no=3,
        requires_certification=1,
    )
    mod3_doc = frappe.get_doc("Program Module", mod3_name)
    _append_course_if_missing(mod3_doc, "Contabilidad Aplicada a la Empresa", 1)
    _append_course_if_missing(mod3_doc, "Planillas y Legislación Laboral", 1)
    if not any(r.prerequisite_module == mod2_name for r in mod3_doc.prerequisites):
        mod3_doc.append("prerequisites", {
            "prerequisite_module": mod2_name,
            "prerequisite_type": "Aprobación",
        })
    mod3_doc.save(ignore_permissions=True)
    print(f"  ✔ Módulo III — {mod3_doc.total_hours}h (prerreq: Módulo II)")

    duration = frappe.db.get_value("Program", prog_name, "program_duration")
    print(f"  📊 Duración total {prog_name}: {duration}h")

    # Student Groups por módulo — cada uno vinculado al trimestre correspondiente
    ay = "2026"
    term1 = _get_term("Trimestre I")
    term2 = _get_term("Trimestre II")
    term3 = _get_term("Trimestre III")
    _upsert_student_group(
        "Asistente Administrativo — Módulo I (2026)",
        prog_name, "Ofimática Empresarial", mod1_name, ay, coordinadora,
        academic_term=term1,
    )
    _upsert_student_group(
        "Asistente Administrativo — Módulo II (2026)",
        prog_name, "Gestión de Archivo y Correspondencia", mod2_name, ay, coordinadora,
        academic_term=term2,
    )
    _upsert_student_group(
        "Asistente Administrativo — Módulo III (2026)",
        prog_name, "Contabilidad Aplicada a la Empresa", mod3_name, ay, coordinadora,
        academic_term=term3,
    )


# ------------------------------------------------------------------
# Programa: Comunicación de Datos (Técnico)
# ------------------------------------------------------------------

def _make_programa_comunicacion_datos():
    prog_name = "Comunicación de Datos"

    cursos_tec = [
        ("Fundamentos de Redes y Telecomunicaciones", "Técnico", 50, 30),
        ("Sistemas Operativos de Red", "Técnico", 40, 24),
        ("Seguridad Informática", "Técnico", 48, 32),
        ("Enrutamiento y Switching", "Técnico", 48, 32),
        ("Administración de Servidores", "Técnico", 48, 40),
        ("Proyecto Integrador de Redes", "Técnico", 24, 48),
    ]
    for nombre, tipo, ht, hp in cursos_tec:
        if not frappe.db.exists("Course", nombre):
            frappe.get_doc({
                "doctype": "Course",
                "course_name": nombre,
                "course_status": "Activo",
                "course_type": tipo,
            }).insert(ignore_permissions=True)
            frappe.db.set_value("Course", nombre, {
                "theory_hours": ht,
                "practical_hours": hp,
                "total_hours": ht + hp,
            })
            print(f"  ✔ Curso Técnico: {nombre}")

    coordinador = frappe.db.get_value(
        "Instructor", {"instructor_name": "Carlos Solís Esquivel"}, "name"
    ) or frappe.db.get_value("Instructor", {}, "name")

    if not frappe.db.exists("Program", prog_name):
        frappe.get_doc({
            "doctype": "Program",
            "program_name": prog_name,
            "program_code": "COM-DATOS",
            "program_type": "Técnico",
            "program_status": "Activo",
            "coordinator": coordinador,
            "min_age": 18,
            "max_age": 45,
            "min_education_level": "Secundaria",
        }).insert(ignore_permissions=True)
        print(f"  ✔ Programa: {prog_name}")
    else:
        print(f"  ⏭  Programa ya existe: {prog_name}")

    # Módulo I — Infraestructura de Redes
    mod1_name = _upsert_module(
        "Módulo I: Infraestructura de Redes",
        prog_name, theory_hours=90, practical_hours=54,
        min_grade=75, min_attendance=85, order_no=1,
    )
    mod1_doc = frappe.get_doc("Program Module", mod1_name)
    _append_course_if_missing(mod1_doc, "Fundamentos de Redes y Telecomunicaciones", 1)
    _append_course_if_missing(mod1_doc, "Sistemas Operativos de Red", 1)
    mod1_doc.save(ignore_permissions=True)
    print(f"  ✔ Módulo I — {mod1_doc.total_hours}h")

    # Módulo II — Seguridad y Enrutamiento
    mod2_name = _upsert_module(
        "Módulo II: Seguridad y Enrutamiento",
        prog_name, theory_hours=96, practical_hours=64,
        min_grade=75, min_attendance=85, order_no=2,
    )
    mod2_doc = frappe.get_doc("Program Module", mod2_name)
    _append_course_if_missing(mod2_doc, "Seguridad Informática", 1)
    _append_course_if_missing(mod2_doc, "Enrutamiento y Switching", 1)
    if not any(r.prerequisite_module == mod1_name for r in mod2_doc.prerequisites):
        mod2_doc.append("prerequisites", {"prerequisite_module": mod1_name, "prerequisite_type": "Aprobación"})
    mod2_doc.save(ignore_permissions=True)
    print(f"  ✔ Módulo II — {mod2_doc.total_hours}h (prerreq: Módulo I)")

    # Módulo III — Proyecto Final: emite título técnico al aprobarse
    mod3_name = _upsert_module(
        "Módulo III: Administración y Proyecto Final",
        prog_name, theory_hours=72, practical_hours=88,
        min_grade=75, min_attendance=85, order_no=3,
        requires_certification=1,
    )
    mod3_doc = frappe.get_doc("Program Module", mod3_name)
    _append_course_if_missing(mod3_doc, "Administración de Servidores", 1)
    _append_course_if_missing(mod3_doc, "Proyecto Integrador de Redes", 1)
    if not any(r.prerequisite_module == mod2_name for r in mod3_doc.prerequisites):
        mod3_doc.append("prerequisites", {"prerequisite_module": mod2_name, "prerequisite_type": "Aprobación"})
    mod3_doc.save(ignore_permissions=True)
    print(f"  ✔ Módulo III — {mod3_doc.total_hours}h (prerreq: Módulo II)")

    duration = frappe.db.get_value("Program", prog_name, "program_duration")
    print(f"  📊 Duración total {prog_name}: {duration}h")

    ay = "2026"
    term1 = _get_term("Trimestre I")
    term2 = _get_term("Trimestre II")
    term3 = _get_term("Trimestre III")
    _upsert_student_group(
        "Comunicación de Datos — Módulo I (2026)",
        prog_name, "Fundamentos de Redes y Telecomunicaciones", mod1_name, ay, coordinador,
        academic_term=term1,
    )
    _upsert_student_group(
        "Comunicación de Datos — Módulo II (2026)",
        prog_name, "Seguridad Informática", mod2_name, ay, coordinador,
        academic_term=term2,
    )
    _upsert_student_group(
        "Comunicación de Datos — Módulo III (2026)",
        prog_name, "Administración de Servidores", mod3_name, ay, coordinador,
        academic_term=term3,
    )


# ------------------------------------------------------------------
# Utilidades internas
# ------------------------------------------------------------------

def _upsert_module(module_name, program, theory_hours, practical_hours,
                   min_grade=70, min_attendance=80, order_no=1, requires_certification=0):
    existing = frappe.db.get_value(
        "Program Module", {"module_name": module_name, "program": program}, "name"
    )
    if existing:
        mod = frappe.get_doc("Program Module", existing)
        mod.theory_hours = theory_hours
        mod.practical_hours = practical_hours
        mod.min_grade = min_grade
        mod.min_attendance = min_attendance
        mod.order_no = order_no
        mod.requires_certification = requires_certification
        mod.save(ignore_permissions=True)
        return existing
    return frappe.get_doc({
        "doctype": "Program Module",
        "module_name": module_name,
        "program": program,
        "status": "Activo",
        "theory_hours": theory_hours,
        "practical_hours": practical_hours,
        "min_grade": min_grade,
        "min_attendance": min_attendance,
        "order_no": order_no,
        "requires_certification": requires_certification,
    }).insert(ignore_permissions=True).name


def _append_course_if_missing(mod_doc, course_name, is_mandatory=1):
    existing = [r.course for r in mod_doc.courses_in_module]
    if course_name not in existing:
        mod_doc.append("courses_in_module", {
            "course": course_name,
            "is_mandatory": is_mandatory,
        })


def _upsert_student_group(sg_name, program, course, program_module,
                          academic_year, instructor, academic_term=None):
    if frappe.db.exists("Student Group", sg_name):
        # Actualizar academic_term si falta
        if academic_term and not frappe.db.get_value("Student Group", sg_name, "academic_term"):
            frappe.db.set_value("Student Group", sg_name, "academic_term", academic_term)
            print(f"  ↻  Student Group actualizado con término: {sg_name}")
        return
    try:
        frappe.get_doc({
            "doctype": "Student Group",
            "student_group_name": sg_name,
            "group_based_on": "Course",
            "academic_year": academic_year,
            "academic_term": academic_term or "",
            "program": program,
            "course": course,
            "program_module": program_module,
            "instructors": [{"instructor": instructor}] if instructor else [],
        }).insert(ignore_permissions=True)
        term_label = f" [{academic_term}]" if academic_term else ""
        print(f"  ✔ Student Group: {sg_name}{term_label}")
    except Exception as e:
        print(f"  ⚠  Student Group omitido ({sg_name}): {e}")


# ------------------------------------------------------------------
# Teardown — elimina todos los datos insertados por el seed
# ------------------------------------------------------------------

# Nombres exactos de todo lo creado por el seed (en orden de eliminación)
_STUDENT_GROUPS = [
    "Asistente Administrativo — Módulo I (2026)",
    "Asistente Administrativo — Módulo II (2026)",
    "Asistente Administrativo — Módulo III (2026)",
    "Comunicación de Datos — Módulo I (2026)",
    "Comunicación de Datos — Módulo II (2026)",
    "Comunicación de Datos — Módulo III (2026)",
]

_PROGRAMS = ["Asistente Administrativo", "Comunicación de Datos"]

_COURSES = [
    # Cursos libres
    "Contabilidad Básica", "Excel Financiero", "Finanzas Personales",
    "Formulación de Proyectos", "Inicio de Emprendimiento", "Gestión de Equipos",
    "Principios de Ciberseguridad", "MS Access", "Herramientas de Comunicación a Distancia",
    "Marketing Web", "Cocina Fusión", "Cocina Mexicana", "Cocina Saludable",
    "Manipulación de Alimentos", "Asado Básico", "Servicio al Cliente",
    "Arreglos Florales", "Artículos para Fiestas", "Decoración de Eventos Especiales",
    "Huertos Orgánicos Urbanos",
    # Cursos Asistente Administrativo
    "Ofimática Empresarial", "Redacción Comercial y Ortografía",
    "Gestión de Archivo y Correspondencia", "Atención al Público y Protocolo",
    "Contabilidad Aplicada a la Empresa", "Planillas y Legislación Laboral",
    # Cursos Comunicación de Datos
    "Fundamentos de Redes y Telecomunicaciones", "Sistemas Operativos de Red",
    "Seguridad Informática", "Enrutamiento y Switching",
    "Administración de Servidores", "Proyecto Integrador de Redes",
]

_INSTRUCTOR_EMAILS = [
    "instructor1@gmail.com", "instructor2@gmail.com", "instructor3@gmail.com",
    "instructor4@gmail.com", "instructor5@gmail.com", "instructor6@gmail.com",
]

_ACADEMIC_TERM_NAMES = ["2026 (Trimestre I)", "2026 (Trimestre II)", "2026 (Trimestre III)"]


def teardown():
    """
    Elimina todos los datos insertados por el seed en el orden correcto
    para respetar las restricciones de clave foránea.

    Uso:
        bench --site education.localhost execute education.education.seed_cmfe.teardown
    """
    frappe.set_user("Administrator")

    # 1. Student Groups
    for sg in _STUDENT_GROUPS:
        if frappe.db.exists("Student Group", sg):
            frappe.delete_doc("Student Group", sg, ignore_permissions=True, force=True)
            print(f"  🗑  Student Group eliminado: {sg}")

    # 2. Módulos (Program Module) — deben ir antes que los programas
    for prog_name in _PROGRAMS:
        modules = frappe.db.get_all(
            "Program Module", filters={"program": prog_name}, pluck="name"
        )
        for mod in modules:
            frappe.delete_doc("Program Module", mod, ignore_permissions=True, force=True)
            print(f"  🗑  Program Module eliminado: {mod}")

    # 3. Programas
    for prog in _PROGRAMS:
        if frappe.db.exists("Program", prog):
            frappe.delete_doc("Program", prog, ignore_permissions=True, force=True)
            print(f"  🗑  Program eliminado: {prog}")

    # 4. Cursos
    for course in _COURSES:
        if frappe.db.exists("Course", course):
            frappe.delete_doc("Course", course, ignore_permissions=True, force=True)
            print(f"  🗑  Course eliminado: {course}")

    # 5. Instructores y sus Users
    for email in _INSTRUCTOR_EMAILS:
        inst = frappe.db.get_value("Instructor", {"email_id": email}, "name")
        if inst:
            frappe.delete_doc("Instructor", inst, ignore_permissions=True, force=True)
            print(f"  🗑  Instructor eliminado: {inst} ({email})")
        if frappe.db.exists("User", email):
            frappe.db.delete("Has Role", {"parent": email})
            frappe.db.delete("User", {"name": email})
            print(f"  🗑  User eliminado: {email}")

    # 6. Academic Terms
    for term in _ACADEMIC_TERM_NAMES:
        if frappe.db.exists("Academic Term", term):
            frappe.delete_doc("Academic Term", term, ignore_permissions=True, force=True)
            print(f"  🗑  Academic Term eliminado: {term}")

    # 7. Academic Year
    if frappe.db.exists("Academic Year", "2026"):
        frappe.delete_doc("Academic Year", "2026", ignore_permissions=True, force=True)
        print("  🗑  Academic Year 2026 eliminado")

    frappe.db.commit()
    print("\n✅ Teardown CMFE completado.\n")
