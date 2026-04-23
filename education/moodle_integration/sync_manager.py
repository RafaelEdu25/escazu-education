"""
Gestor de Sincronización Frappe Education ↔ Moodle
"""

import frappe
from typing import Optional, Dict
from .moodle_client import MoodleClient


class SyncManager:
	"""Administra la sincronización entre Frappe y Moodle."""

	def __init__(self):
		if not frappe.db.exists("Moodle Integration Settings", "Moodle Integration Settings"):
			frappe.throw("Moodle Integration Settings no está configurado. Configure la integración primero.")

		self.settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")

		if not self.settings.enabled:
			frappe.throw("La integración con Moodle está deshabilitada.")

		if not self.settings.moodle_url or not self.settings.api_token:
			frappe.throw("Configure Moodle URL y API Token en Moodle Integration Settings.")

		self.moodle = MoodleClient(self.settings.moodle_url, self.settings.api_token)

	def get_client(self) -> MoodleClient:
		"""Retorna el cliente de Moodle."""
		return self.moodle

	def sync_course(self, course_name: str) -> Dict:
		"""Sincronizar curso a Moodle."""
		course = frappe.get_doc("Course", course_name)

		moodle_id = course.get("moodle_course_id")
		original_name = course.name

		if moodle_id:
			result = self._update_moodle_course_by_id(course, moodle_id)
			if result.get("status") == "updated" and original_name != course.course_name:
				self._update_frappe_course_name(original_name, course.course_name)
			return result
		else:
			result = self._create_moodle_course_from_course(course)
			if result.get("status") == "created" and original_name != course.course_name:
				self._update_frappe_course_name(original_name, course.course_name)
			return result

	def _update_frappe_course_name(self, old_name: str, new_name: str):
		"""Actualizar el 'name' del curso en Frappe cuando course_name cambia."""
		if not frappe.db.exists("Course", new_name):
			try:
				frappe.db.sql(
					"""
					UPDATE tabCourse 
					SET name = %s, course_name = %s 
					WHERE name = %s
				""",
					(new_name, new_name, old_name),
				)

				frappe.db.commit()
				frappe.logger().info(f"Updated course name: {old_name} -> {new_name}")
			except Exception as e:
				frappe.logger().error(f"Failed to update course name: {e}")

	def _create_moodle_course_from_course(self, course) -> Dict:
		"""Crear curso en Moodle desde Course de Frappe."""
		course_data = {
			"fullname": course.course_name,
			"shortname": course.name,
			"categoryid": self.settings.default_category_id or 1,
			"summary": course.description or "",
			"visible": 1,
		}

		try:
			result = self.moodle.create_courses([course_data])

			if result and isinstance(result, list) and len(result) > 0:
				if "exception" in result[0]:
					error_msg = result[0].get("message", "Error desconocido")
					return {"status": "error", "message": error_msg}

				moodle_course_id = result[0]["id"]
				frappe.db.set_value("Course", course.name, "moodle_course_id", moodle_course_id)

				return {
					"status": "created",
					"moodle_course_id": moodle_course_id,
					"course_name": result[0].get("fullname", course.course_name),
				}

			return {"status": "error", "message": "No se recibió respuesta válida"}

		except Exception as e:
			error_msg = str(e)
			return {"status": "error", "message": error_msg}



	def _update_moodle_course_by_id(self, course, moodle_course_id: int) -> Dict:
		"""Actualizar curso en Moodle usando moodle_course_id."""
		course_data = {
			"id": moodle_course_id,
			"fullname": course.course_name,
			"shortname": course.name,
			"summary": course.description or "",
		}

		frappe.logger().info(f"SYNC: Updating Moodle course {moodle_course_id} with data: {course_data}")

		try:
			result = self.moodle.update_courses([course_data])

			frappe.logger().info(f"SYNC: Moodle response: {result}")

			if result and isinstance(result, list) and len(result) > 0:
				if "exception" in result[0]:
					error_msg = result[0].get("message", "Error desconocido")
					return {"status": "error", "message": error_msg}

			return {"status": "updated", "moodle_course_id": moodle_course_id}

		except Exception as e:
			error_msg = str(e)
			return {"status": "error", "message": error_msg}


def get_moodle_client() -> Optional[MoodleClient]:
	"""Obtener cliente de Moodle (para uso en eventos)."""
	try:
		if not frappe.db.exists("Moodle Integration Settings", "Moodle Integration Settings"):
			return None

		settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")

		if not settings.enabled:
			return None

		if not settings.moodle_url or not settings.api_token:
			return None

		return MoodleClient(settings.moodle_url, settings.api_token)
	except:
		return None


def sync_moodle_to_frappe() -> dict:
	"""Sincronizar cursos de Moodle a Frappe (para scheduled tasks)."""
	client = get_moodle_client()
	if not client:
		return {"status": "skipped", "message": "Integration not configured"}

	moodle_courses = client.get_all_courses()
	if not moodle_courses or not isinstance(moodle_courses, list):
		return {"status": "skipped", "message": "No courses in Moodle"}

	created = 0
	updated = 0
	skipped = 0

	for mc in moodle_courses:
		moodle_id = mc.get("id")
		shortname = mc.get("shortname")
		fullname = mc.get("fullname")

		if not shortname:
			continue

		existing_course = None

		if moodle_id:
			existing_course = frappe.db.get_value(
				"Course", {"moodle_course_id": moodle_id}, "name", order_by="modified desc"
			)

		if not existing_course and shortname:
			existing_course = frappe.db.get_value(
				"Course", {"name": shortname}, "name", order_by="modified desc"
			)

		if existing_course:
			try:
				course = frappe.get_doc("Course", existing_course)
				changed = False

				if course.course_name != fullname and fullname:
					course.course_name = fullname
					changed = True

				old_desc = (course.description or "").strip()
				new_desc = (mc.get("summary", "")[:500] if mc.get("summary") else "").strip()
				if old_desc != new_desc:
					course.description = new_desc
					changed = True

				if not course.moodle_course_id and moodle_id:
					course.moodle_course_id = moodle_id
					changed = True

				if changed:
					course.save(ignore_permissions=True)
					updated += 1
				else:
					skipped += 1
			except Exception:
				skipped += 1
		else:
			try:
				course = frappe.get_doc(
					{
						"doctype": "Course",
						"course_name": fullname,
						"name": shortname,
						"moodle_course_id": moodle_id,
						"description": mc.get("summary", "")[:500] if mc.get("summary") else "",
					}
				)
				course.insert(ignore_permissions=True)
				created += 1
			except Exception:
				pass

	return {"status": "completed", "created": created, "updated": updated, "skipped": skipped}


@frappe.whitelist()
def sync_course(course_name: str, moodle_course_id: str = None) -> Dict:
	"""Sincronizar curso a Moodle (usable desde API)."""
	try:
		manager = SyncManager()

		if moodle_course_id:
			course = frappe.get_doc("Course", course_name)
			course.moodle_course_id = moodle_course_id
			course.save(ignore_permissions=True)
			return manager._update_moodle_course_by_id(course, int(moodle_course_id))

		return manager.sync_course(course_name)
	except Exception as e:
		return {"status": "error", "message": str(e)}
