"""
Manejadores de eventos para sincronización automática con Moodle
"""

import frappe
import frappe.utils

from frappe.utils import now


def on_course_renamed(doc, method, old=None, new=None, merge=False):
	"""Se ejecuta después de renombrar un Curso (cambio de name/shortname)."""
	if not _is_integration_enabled():
		return

	moodle_id = doc.get("moodle_course_id") or getattr(doc, "moodle_course_id", None)
	if moodle_id:
		frappe.enqueue(
			"education.moodle_integration.events.sync_course_to_moodle",
			course_name=doc.name,
			queue="short",
			enqueue_after_commit=True,
		)


def on_course_created(doc, method):
	"""Se ejecuta después de crear un Curso (solo para nuevos)."""
	if not _is_integration_enabled() or not _should_sync_on_create():
		return

	# Sincronización asíncrona para no bloquear el guardado
	frappe.enqueue(
		"education.moodle_integration.events._try_sync_new_course",
		course_name=doc.name,
		queue="short",
	)


def on_course_saved(doc, method):
	"""Se ejecuta después de guardar un Curso (para actualizaciones)."""
	if method == "validate":
		return

	moodle_id = doc.get("moodle_course_id") or doc.moodle_course_id

	if not _is_integration_enabled():
		return

	if moodle_id:
		frappe.enqueue(
			"education.moodle_integration.events.sync_course_to_moodle",
			course_name=doc.name,
			queue="short",
			enqueue_after_commit=True,
		)
	elif _should_sync_on_create():
		frappe.enqueue(
			"education.moodle_integration.events._try_sync_new_course",
			course_name=doc.name,
			queue="short",
			enqueue_after_commit=True,
		)


def on_program_created(doc, method):
	"""Programs already don't sync - kept for backwards compatibility."""
	pass


def on_program_updated(doc, method):
	"""Programs already don't sync - kept for backwards compatibility."""
	pass


def on_course_updated(doc, method):
	"""Se ejecuta cuando se actualiza un Curso."""
	frappe.publish_realtime(
		event="msgprint",
		message=f"SYNC DEBUG: on_course_updated for {doc.name}, moodle_id={doc.get('moodle_course_id')}",
	)

	if not _is_integration_enabled():
		frappe.publish_realtime(event="msgprint", message="SYNC: Integration not enabled")
		return

	if not _should_sync_on_update():
		frappe.publish_realtime(event="msgprint", message="SYNC: sync_on_update disabled")
		return

	moodle_id = doc.get("moodle_course_id")
	frappe.publish_realtime(event="msgprint", message=f"SYNC: moodle_id={moodle_id}")

	if moodle_id:
		# Sincronización asíncrona inmediata (sin esperar commit)
		frappe.enqueue(
			"education.moodle_integration.events.sync_course_to_moodle",
			course_name=doc.name,
			queue="short",
		)
		frappe.publish_realtime(event="msgprint", message="SYNC: Enqueued sync_course_to_moodle")
	elif _should_sync_on_create():
		frappe.enqueue(
			"education.moodle_integration.events._try_sync_new_course",
			course_name=doc.name,
			queue="short",
		)


def sync_course_to_moodle(course_name: str):
	"""Sincronizar curso a Moodle."""
	try:
		from education.moodle_integration.sync_manager import SyncManager

		manager = SyncManager()
		result = manager.sync_course(course_name)

		if result.get("status") == "error":
			frappe.log_error(
				f"Failed to sync course {course_name}: {result.get('message')}", "Moodle Sync Error"
			)
		elif result.get("status") == "created":
			frappe.msgprint(
				f"✓ Course created in Moodle: {result.get('course_name')}", indicator="green", alert=True
			)
		elif result.get("status") == "updated":
			frappe.msgprint("✓ Course updated in Moodle", indicator="green", alert=True)
	except Exception as e:
		frappe.log_error(f"Failed to sync course {course_name}: {str(e)}", "Moodle Sync Error")


def _is_integration_enabled() -> bool:
	"""Verificar si la integración está habilitada."""
	try:
		if not frappe.db.exists("Moodle Integration Settings", "Moodle Integration Settings"):
			return False

		settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")
		return settings.enabled
	except:
		return False


def _should_sync_on_create() -> bool:
	"""Verificar si debe sincronizar al crear."""
	try:
		settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")
		return settings.sync_on_create
	except:
		return False


def _should_sync_on_update() -> bool:
	"""Verificar si debe sincronizar al actualizar."""
	try:
		settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")
		return settings.sync_on_update
	except:
		return False


def _try_sync_new_course(course_name: str):
	"""Intentar sincronizar un curso nuevo a Moodle."""
	try:
		from education.moodle_integration.sync_manager import SyncManager

		manager = SyncManager()
		result = manager.sync_course(course_name)

		if result.get("status") == "error":
			frappe.publish_realtime(event="msgprint", message=f"SYNC Error: {result.get('message')}")
			frappe.log_error(
				f"Failed to sync course {course_name}: {result.get('message')}", "Moodle Sync Error"
			)
		elif result.get("status") == "created":
			moodle_id = result.get("moodle_course_id")
			if moodle_id:
				frappe.db.set_value("Course", course_name, "moodle_course_id", moodle_id)
			frappe.msgprint(
				"✓ Course created in Moodle!", indicator="green", alert=True
			)
		elif result.get("status") == "updated":
			frappe.msgprint("✓ Course updated in Moodle", indicator="green", alert=True)
	except Exception as e:
		frappe.publish_realtime(event="msgprint", message=f"SYNC Error: {str(e)[:50]}")
		frappe.log_error(f"Failed to sync course {course_name}: {str(e)}", "Moodle Sync Error")
