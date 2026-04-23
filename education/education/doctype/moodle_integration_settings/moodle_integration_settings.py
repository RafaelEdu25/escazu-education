# Copyright (c) 2025, Education and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
from requests.adapters import HTTPAdapter


class MoodleIntegrationSettings(Document):
	pass


@frappe.whitelist()
def test_connection():
	settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")
	target_url = settings.moodle_url

	if not target_url:
		frappe.throw("Moodle URL is not configured.")

	session = requests.Session()
	session.trust_env = False

	adapter = HTTPAdapter(max_retries=0)
	session.mount("http://", adapter)
	session.mount("https://", adapter)

	ws_url = target_url.rstrip("/") + "/webservice/rest/server.php"

	token = frappe.db.get_value("Moodle Integration Settings", "Moodle Integration Settings", "api_token")
	if not token:
		frappe.throw("API Token not configured in Moodle Integration Settings")

	data = {
		"wstoken": token,
		"moodlewsrestformat": "json",
		"wsfunction": "core_course_get_courses_by_field",
		"field": "shortname",
		"value": "test",
	}

	r = session.post(ws_url, data=data, timeout=10)

	if r.status_code == 200:
		resp = r.json()
		if "exception" in resp:
			frappe.throw(f"Moodle error: {resp.get('message', resp['exception'])}")
		else:
			frappe.msgprint("✓ Connected to Moodle!", indicator="green", alert=True)
			return {"status": "success", "message": "Connected to Moodle!"}
	else:
		frappe.throw(f"HTTP: {r.status_code}")


@frappe.whitelist()
def sync_program(program_name: str):
	"""Sync a single program to Moodle."""
	settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")
	target_url = settings.moodle_url
	token = frappe.db.get_value("Moodle Integration Settings", "Moodle Integration Settings", "api_token")

	if not target_url:
		frappe.throw("Moodle URL not configured in Moodle Integration Settings")

	if not token:
		frappe.throw("API Token not configured in Moodle Integration Settings")

	program_name = program_name.strip()
	program_name = program_name.strip('"').strip("'")

	frappe.publish_realtime(event="msgprint", message=f"Syncing '{program_name}'...")

	session = requests.Session()
	session.trust_env = False
	adapter = HTTPAdapter(max_retries=0)
	session.mount("http://", adapter)

	ws_url = target_url.rstrip("/") + "/webservice/rest/server.php"

	data = {
		"wstoken": token,
		"moodlewsrestformat": "json",
		"wsfunction": "core_course_create_courses",
		"courses[0][fullname]": program_name,
		"courses[0][shortname]": program_name,
		"courses[0][categoryid]": 1,
	}

	r = session.post(ws_url, data=data, timeout=15)

	if r.status_code == 200:
		resp = r.json()
		if "exception" in resp:
			frappe.publish_realtime(
				event="msgprint", message=f"Moodle error: {resp.get('message', resp['exception'])}"
			)
			frappe.throw(f"Moodle error: {resp.get('message', resp['exception'])}")
		elif isinstance(resp, list) and len(resp) > 0 and "id" in resp[0]:
			moodle_course_id = resp[0].get("id")
			frappe.msgprint(
				f"✓ Course created in Moodle (ID: {moodle_course_id})", indicator="green", alert=True
			)
			frappe.publish_realtime(
				event="msgprint",
				message=f"✓ Course '{program_name}' created in Moodle (ID: {moodle_course_id})!",
			)
			return {"status": "success", "moodle_course_id": moodle_course_id}
		else:
			frappe.msgprint(f"Course created: {str(resp)[:100]}", indicator="green", alert=True)
			frappe.publish_realtime(event="msgprint", message=f"✓ Course synced!")
			return {"status": "success", "message": str(resp)}
	else:
		frappe.throw(f"HTTP: {r.status_code}")


# @frappe.whitelist()
# def sync_all_programs():
# 	"""Sincronizar todos los cursos de Frappe a Moodle (crear y actualizar)."""
# 	settings = frappe.get_doc("Moodle Integration Settings", "Moodle Integration Settings")
# 	target_url = settings.moodle_url
# 	token = frappe.db.get_value("Moodle Integration Settings", "Moodle Integration Settings", "api_token")
#
# 	if not target_url:
# 		frappe.throw("Moodle URL not configured in Moodle Integration Settings")
#
# 	if not token:
# 		frappe.throw("API Token not configured in Moodle Integration Settings")
#
# 	courses = frappe.get_all("Course", fields=["name", "course_name", "moodle_course_id"], limit=50)
#
# 	if not courses:
# 		return {"status": "success", "message": "No courses."}
#
# 	session = requests.Session()
# 	session.trust_env = False
#
# 	adapter = HTTPAdapter(max_retries=0)
# 	session.mount("http://", adapter)
# 	session.mount("https://", adapter)
#
# 	ws_url = target_url.rstrip("/") + "/webservice/rest/server.php"
#
# 	created = 0
# 	updated = 0
# 	errors = 0
#
# 	for course in courses:
# 		moodle_id = course.get("moodle_course_id")
#
# 		try:
# 			if moodle_id:
# 				data = {
# 					"wstoken": token,
# 					"moodlewsrestformat": "json",
# 					"wsfunction": "core_course_update_courses",
# 					"courses[0][id]": moodle_id,
# 					"courses[0][fullname]": course.course_name,
# 					"courses[0][shortname]": course.name,
# 				}
# 				r = session.post(ws_url, data=data, timeout=15, allow_redirects=True)
#
# 				if r.status_code == 200:
# 					resp = r.json()
# 					if "exception" in resp:
# 						if "not found" in str(resp.get("message", "")).lower():
# 							data = {
# 								"wstoken": token,
# 								"moodlewsrestformat": "json",
# 								"wsfunction": "core_course_create_courses",
# 								"courses[0][fullname]": course.course_name,
# 								"courses[0][shortname]": course.name,
# 								"courses[0][categoryid]": 1,
# 							}
# 							r = session.post(ws_url, data=data, timeout=15, allow_redirects=True)
# 							if r.status_code == 200:
# 								resp = r.json()
# 								if isinstance(resp, list) and len(resp) > 0 and "id" in resp[0]:
# 									new_id = resp[0].get("id")
# 									frappe.db.set_value("Course", course.name, "moodle_course_id", new_id)
# 									created += 1
# 						else:
# 							errors += 1
# 					else:
# 						updated += 1
# 				else:
# 					errors += 1
# 			else:
# 				data = {
# 					"wstoken": token,
# 					"moodlewsrestformat": "json",
# 					"wsfunction": "core_course_create_courses",
# 					"courses[0][fullname]": course.course_name,
# 					"courses[0][shortname]": course.name,
# 					"courses[0][categoryid]": 1,
# 				}
# 				r = session.post(ws_url, data=data, timeout=15, allow_redirects=True)
#
# 				if r.status_code == 200:
# 					resp = r.json()
# 					if isinstance(resp, list) and len(resp) > 0 and "id" in resp[0]:
# 						new_id = resp[0].get("id")
# 						frappe.db.set_value("Course", course.name, "moodle_course_id", new_id)
# 						created += 1
# 					else:
# 						errors += 1
# 				else:
# 					errors += 1
# 		except Exception:
# 			errors += 1
#
# 	msg = f"Created: {created}, Updated: {updated}, Errors: {errors}"
# 	frappe.msgprint(msg, indicator="green", alert=True)
# 	return {"status": "success", "message": msg}


# @frappe.whitelist()
# def import_moodle():
# 	"""Importar cursos desde Moodle a Frappe (crear y actualizar)."""
# 	frappe.msgprint("Starting import from Moodle...", alert=True)
#
# 	from education.moodle_integration.sync_manager import get_moodle_client
#
# 	client = get_moodle_client()
# 	if not client:
# 		frappe.throw("Moodle Integration not configured")
#
# 	moodle_courses = client.get_all_courses()
#
# 	if not moodle_courses or not isinstance(moodle_courses, list):
# 		return {"status": "success", "message": "No courses found in Moodle"}
#
# 	created = 0
# 	updated = 0
# 	skipped = 0
# 	errors = 0
#
# 	for mc in moodle_courses:
# 		moodle_id = mc.get("id")
# 		shortname = mc.get("shortname")
# 		fullname = mc.get("fullname")
#
# 		if not shortname:
# 			continue
#
# 		try:
# 			existing_course = None
#
# 			if moodle_id:
# 				existing_course = frappe.db.get_value(
# 					"Course", {"moodle_course_id": moodle_id}, "name", order_by="modified desc"
# 				)
#
# 			if not existing_course and shortname:
# 				existing_course = frappe.db.get_value(
# 					"Course", {"name": shortname}, "name", order_by="modified desc"
# 				)
#
# 			if existing_course:
# 				course = frappe.get_doc("Course", existing_course)
# 				changed = False
#
# 				if course.course_name != fullname and fullname:
# 					course.course_name = fullname
# 					changed = True
#
# 				old_desc = course.description or ""
# 				new_desc = mc.get("summary", "")[:500] if mc.get("summary") else ""
# 				if old_desc.strip() != new_desc.strip():
# 					course.description = new_desc
# 					changed = True
#
# 				if not course.moodle_course_id and moodle_id:
# 					course.moodle_course_id = moodle_id
# 					changed = True
#
# 				if changed:
# 					course.save(ignore_permissions=True)
# 					updated += 1
# 				else:
# 					skipped += 1
# 			else:
# 				course = frappe.get_doc(
# 					{
# 						"doctype": "Course",
# 						"course_name": fullname,
# 						"name": shortname,
# 						"moodle_course_id": moodle_id,
# 						"description": mc.get("summary", "")[:500] if mc.get("summary") else "",
# 					}
# 				)
# 				course.insert(ignore_permissions=True)
# 				created += 1
#
# 		except Exception as e:
# 			errors += 1
#
# 	msg = f"Created: {created}, Updated: {updated}, Skipped: {skipped}, Errors: {errors}"
# 	frappe.msgprint(msg, indicator="green", alert=True)
# 	return {"status": "success", "message": msg}


# @frappe.whitelist()
# def sync_moodle_auto():
# 	"""Sincronizar cursos desde Moodle a Frappe (crear y actualizar)."""
# 	from education.moodle_integration.sync_manager import get_moodle_client
#
# 	frappe.msgprint("Starting sync from Moodle...", alert=True)
#
# 	client = get_moodle_client()
# 	if not client:
# 		frappe.throw("Moodle Integration not configured")
#
# 	moodle_courses = client.get_all_courses()
#
# 	if not moodle_courses or not isinstance(moodle_courses, list):
# 		frappe.msgprint("No courses found in Moodle")
# 		return {"status": "success", "message": "No courses found in Moodle"}
#
# 	created = 0
# 	updated = 0
# 	skipped = 0
# 	errors = 0
#
# 	for mc in moodle_courses:
# 		moodle_id = mc.get("id")
# 		shortname = mc.get("shortname")
# 		fullname = mc.get("fullname")
#
# 		if not shortname:
# 			continue
#
# 		try:
# 			existing_course = None
#
# 			if moodle_id:
# 				existing_course = frappe.db.get_value(
# 					"Course", {"moodle_course_id": moodle_id}, "name", order_by="modified desc"
# 				)
#
# 			if not existing_course and shortname:
# 				existing_course = frappe.db.get_value(
# 					"Course", {"name": shortname}, "name", order_by="modified desc"
# 				)
#
# 			if existing_course:
# 				course = frappe.get_doc("Course", existing_course)
# 				changed = False
#
# 				if course.course_name != fullname and fullname:
# 					course.course_name = fullname
# 					changed = True
#
# 				old_desc = course.description or ""
# 				new_desc = mc.get("summary", "")[:500] if mc.get("summary") else ""
# 				if old_desc.strip() != new_desc.strip():
# 					course.description = new_desc
# 					changed = True
#
# 				if not course.moodle_course_id and moodle_id:
# 					course.moodle_course_id = moodle_id
# 					changed = True
#
# 				if changed:
# 					course.save(ignore_permissions=True)
# 					updated += 1
# 				else:
# 					skipped += 1
# 			else:
# 				course = frappe.get_doc(
# 					{
# 						"doctype": "Course",
# 						"course_name": fullname,
# 						"name": shortname,
# 						"moodle_course_id": moodle_id,
# 						"description": mc.get("summary", "")[:500] if mc.get("summary") else "",
# 					}
# 				)
# 				course.insert(ignore_permissions=True)
# 				created += 1
#
# 		except Exception as e:
# 			errors += 1
# 			frappe.publish_realtime(event="msgprint", message=f"Error: {str(e)[:50]}")
#
# 	msg = f"Created: {created}, Updated: {updated}, Skipped: {skipped}, Errors: {errors}"
# 	frappe.msgprint(msg, indicator="green", alert=True)
# 	return {"status": "success", "message": msg}
