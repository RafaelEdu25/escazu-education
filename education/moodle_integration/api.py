"""
API Endpoints para sincronización manual con Moodle
"""

import frappe
from typing import Dict


@frappe.whitelist(allow_guest=True)
def setup_moodle_integration() -> Dict:
	"""Verificar si existe configuración de integración con Moodle."""
	try:
		if frappe.db.exists("Moodle Integration Settings", "Moodle Integration Settings"):
			settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")
			return {
				"status": "exists",
				"enabled": settings.enabled,
				"moodle_url": settings.moodle_url,
				"sync_on_create": settings.sync_on_create,
				"sync_on_update": settings.sync_on_update
			}
		else:
			return {"status": "not_found", "message": "Settings not configured. Please create manually in ERPNext."}
	except Exception as e:
		return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def webhook_ping() -> Dict:
	"""Endpoint de prueba para verificar conectividad desde Moodle."""
	frappe.logger().info("Moodle ping received!")
	return {"status": "ok", "message": "Pong from Frappe!"}



@frappe.whitelist(allow_guest=True)
def test_moodle_connection() -> Dict:
	"""Probar conexión con Moodle."""
	try:
		from education.moodle_integration.sync_manager import get_moodle_client

		client = get_moodle_client()
		if not client:
			return {"status": "error", "message": "Integration not configured"}

		info = client.get_site_info()

		if info and "sitename" in info:
			return {
				"status": "success",
				"site_name": info.get("sitename"),
				"version": info.get("version"),
				"user": info.get("username"),
			}

		return {"status": "error", "message": "Unexpected response"}
	except Exception as e:
		return {"status": "error", "message": str(e)}




@frappe.whitelist(allow_guest=True)
def webhook_moodle_course_updated(course_data: dict = None) -> Dict:
	"""Webhook para recibir notificaciones de Moodle cuando un curso se actualiza."""
	import json
	import hashlib
	import re

	frappe.publish_realtime(event="msgprint", message="WEBHOOK DEBUG: Starting webhook")

	raw_data = None
	try:
		raw_data = frappe.request.data
		frappe.logger().info(f"Moodle webhook raw data: {raw_data}")
	except Exception as e:
		frappe.logger().error(f"Moodle webhook - Error getting request data: {e}")

	if not course_data and raw_data:
		try:
			course_data = json.loads(raw_data)
			frappe.logger().info(f"Moodle webhook parsed data: {course_data}")
		except Exception as e:
			frappe.logger().error(f"Moodle webhook - JSON parse error: {e}")
			return {"status": "error", "message": f"JSON parse error: {e}"}

	if not course_data:
		frappe.logger().warning("Moodle webhook - No course data received")
		return {"status": "error", "message": "No course data provided"}

	moodle_id = course_data.get("id")
	shortname = course_data.get("shortname")
	fullname = course_data.get("fullname")
	summary = course_data.get("summary", "")[:500] if course_data.get("summary") else ""

	frappe.logger().info(
		f"Moodle webhook - Processing: shortname={shortname}, id={moodle_id}, fullname={fullname}"
	)

	if not moodle_id and not shortname and not fullname:
		return {"status": "error", "message": "No id, shortname, or fullname provided"}

	existing_course = None

	if moodle_id:
		existing_course = frappe.db.get_value(
			"Course", {"moodle_course_id": str(moodle_id)}, "name", order_by="modified desc"
		)

	if not existing_course and fullname:
		existing_course = frappe.db.get_value(
			"Course", {"course_name": fullname}, "name", order_by="modified desc"
		)

	if not existing_course and shortname:
		existing_course = frappe.db.get_value("Course", {"name": shortname}, "name", order_by="modified desc")

	frappe.logger().info(f"Moodle webhook - Found course: {existing_course}")

	def normalize_text(text):
		if not text:
			return ""
		text = re.sub(r"<[^>]+>", "", text)
		text = re.sub(r"\s+", " ", text)
		return text.strip().lower()

	if existing_course:
		changed = False
		update_details = []

		current_name = frappe.db.get_value("Course", existing_course, "course_name") or ""
		current_desc = frappe.db.get_value("Course", existing_course, "description") or ""
		current_moodle_id = frappe.db.get_value("Course", existing_course, "moodle_course_id") or ""
		current_db_name = existing_course

		incoming_norm = normalize_text(f"{fullname}|{summary}")
		current_norm = normalize_text(f"{current_name}|{current_desc}")

		frappe.logger().info(
			f"Moodle webhook - Normalized current: {current_norm}, incoming: {incoming_norm}"
		)

		if incoming_norm != current_norm:
			if fullname and normalize_text(current_name) != normalize_text(fullname):
				frappe.logger().info(
					f"Moodle webhook - Updating course_name: '{current_name}' -> '{fullname}'"
				)
				if not frappe.db.exists("Course", fullname):
					frappe.db.sql(
						"UPDATE tabCourse SET course_name = %s, name = %s WHERE name = %s",
						(fullname, fullname, current_db_name),
					)
					# frappe.db.sql(
					# 	"UPDATE `tabMoodle Course Mapping` SET course = %s WHERE course = %s",
					# 	(fullname, current_db_name),
					# )
					existing_course = fullname
				else:
					frappe.db.sql(
						"UPDATE tabCourse SET course_name = %s WHERE name = %s", (fullname, current_db_name)
					)
				changed = True
				update_details.append("course_name")

			new_desc = normalize_text(summary)
			current_desc_norm = normalize_text(current_desc)
			if current_desc_norm != new_desc:
				frappe.logger().info(f"Moodle webhook - Updating description")
				frappe.db.sql(
					"UPDATE tabCourse SET description = %s WHERE name = %s", (summary, existing_course)
				)
				changed = True
				update_details.append("description")

		if not current_moodle_id and moodle_id:
			frappe.logger().info(f"Moodle webhook - Setting moodle_course_id: {moodle_id}")
			frappe.db.sql(
				"UPDATE tabCourse SET moodle_course_id = %s WHERE name = %s",
				(str(moodle_id), existing_course),
			)
			changed = True
			update_details.append("moodle_course_id")

		if changed:
			frappe.db.commit()
			frappe.publish_realtime(event="msgprint", message=f"✓ Synced from Moodle: {existing_course}")
			frappe.logger().info(
				f"Moodle webhook - Updated course: {existing_course}, changes: {update_details}"
			)
			return {"status": "updated", "course": existing_course, "changes": update_details}
		else:
			frappe.logger().info(f"Moodle webhook - No changes needed for course: {existing_course}")
			return {"status": "skipped", "message": "No changes"}
	else:
		# Curso no existe, crear uno nuevo
		frappe.logger().info(
			f"Moodle webhook - Creating new course: shortname={shortname}, moodle_id={moodle_id}, fullname={fullname}"
		)

		try:
			# Usar el shortname como nombre del curso en Frappe, o fullname si no hay shortname
			course_name_to_use = shortname if shortname else fullname

			if not course_name_to_use:
				frappe.logger().error("Moodle webhook - Cannot create course without name")
				return {"status": "error", "message": "Cannot create course without shortname or fullname"}

			# Crear el nuevo curso
			new_course = frappe.get_doc({
				"doctype": "Course",
				"course_name": fullname if fullname else course_name_to_use,
				"name": course_name_to_use,
				"moodle_course_id": str(moodle_id) if moodle_id else None,
				"description": summary
			})
			new_course.insert(ignore_permissions=True)
			frappe.db.commit()

			frappe.publish_realtime(event="msgprint", message=f"✓ Created course from Moodle: {course_name_to_use}")
			frappe.logger().info(f"Moodle webhook - Created new course: {course_name_to_use}")

			return {
				"status": "created",
				"course": course_name_to_use,
				"moodle_id": moodle_id
			}
		except Exception as e:
			frappe.logger().error(f"Moodle webhook - Error creating course: {str(e)}")
			frappe.db.rollback()
			return {
				"status": "error",
				"message": f"Error creating course: {str(e)}"
			}


@frappe.whitelist(allow_guest=True)
def sync_course_to_moodle(course_name: str) -> Dict:
	"""Sync a course from Frappe to Moodle."""
	try:
		from education.moodle_integration.sync_manager import SyncManager

		manager = SyncManager()
		result = manager.sync_course(course_name)
		return result
	except Exception as e:
		frappe.logger().error(f"Error syncing course {course_name}: {str(e)}")
		return {"status": "error", "message": str(e)}
