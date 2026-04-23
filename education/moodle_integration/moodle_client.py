"""
Moodle Web Services REST API Client
"""

import requests
from typing import Dict, List, Optional


class MoodleClient:
	"""Cliente para la API REST de Moodle."""

	def __init__(self, moodle_url: str, token: str):
		self.moodle_url = moodle_url.rstrip("/")
		self.token = token
		self.base_params = {
			"wstoken": token,
			"moodlewsrestformat": "json",
		}

	def _call(self, wsfunction: str, params: Optional[Dict] = None) -> Dict:
		"""Realizar llamada a la API de Moodle."""
		endpoint = f"{self.moodle_url}/webservice/rest/server.php"
		data = {**self.base_params, "wsfunction": wsfunction}
		if params:
			data.update(params)

		response = requests.post(endpoint, data=data, timeout=30)
		return response.json()

	def get_site_info(self) -> Dict:
		"""Obtener información del sitio Moodle."""
		return self._call("core_webservice_get_site_info")

	def create_users(self, users: List[Dict]) -> List[Dict]:
		"""Crear múltiples usuarios."""
		params = {}
		for i, user in enumerate(users):
			for key, value in user.items():
				params[f"users[{i}][{key}]"] = value
		return self._call("core_user_create_users", params)

	def update_users(self, users: List[Dict]) -> List[Dict]:
		"""Actualizar múltiples usuarios."""
		params = {}
		for i, user in enumerate(users):
			for key, value in user.items():
				params[f"users[{i}][{key}]"] = value
		return self._call("core_user_update_users", params)

	def get_users_by_field(self, field: str, values: List[str]) -> List[Dict]:
		"""Obtener usuarios por campo específico."""
		params = {"field": field}
		for i, value in enumerate(values):
			params[f"values[{i}]"] = value
		return self._call("core_user_get_users_by_field", params)

	def create_courses(self, courses: List[Dict]) -> List[Dict]:
		"""Crear múltiples cursos."""
		params = {}
		for i, course in enumerate(courses):
			for key, value in course.items():
				params[f"courses[{i}][{key}]"] = value
		return self._call("core_course_create_courses", params)

	def update_courses(self, courses: List[Dict]) -> List[Dict]:
		"""Actualizar múltiples cursos."""
		params = {}
		for i, course in enumerate(courses):
			for key, value in course.items():
				params[f"courses[{i}][{key}]"] = value
		return self._call("core_course_update_courses", params)

	def get_courses_by_field(self, field: str, value: str) -> List[Dict]:
		"""Obtener cursos por campo específico."""
		params = {"field": field, "value": value}
		return self._call("core_course_get_courses_by_field", params)

	def get_all_courses(self) -> List[Dict]:
		"""Obtener todos los cursos."""
		return self._call("core_course_get_courses")

	def delete_courses(self, course_ids: List[int]) -> List[Dict]:
		"""Eliminar cursos."""
		params = {}
		for i, cid in enumerate(course_ids):
			params[f"courseids[{i}]"] = cid
		return self._call("core_course_delete_courses", params)

	def enroll_users(self, enrolments: List[Dict]) -> List[Dict]:
		"""Inscribir usuarios en cursos."""
		params = {}
		for i, enrollment in enumerate(enrolments):
			for key, value in enrollment.items():
				params[f"enrolments[{i}][{key}]"] = value
		return self._call("enrol_manual_enrol_users", params)

	def unenrol_users(self, enrolments: List[Dict]) -> List[Dict]:
		"""Desinscribir usuarios de cursos."""
		params = {}
		for i, enrollment in enumerate(enrolments):
			for key, value in enrollment.items():
				params[f"enrolments[{i}][{key}]"] = value
		return self._call("enrol_manual_unenrol_users", params)

	def get_enrolled_users(self, course_id: int) -> List[Dict]:
		"""Obtener usuarios inscritos en un curso."""
		params = {"courseid": course_id}
		return self._call("core_enrol_get_enrolled_users", params)

	def get_course_contents(self, course_id: int) -> List[Dict]:
		"""Obtener contenidos de un curso."""
		params = {"courseid": course_id}
		return self._call("core_course_get_contents", params)

	def get_categories(self, criteria: Optional[Dict] = None) -> List[Dict]:
		"""Obtener categorías de cursos."""
		if criteria:
			params = {}
			for i, (key, value) in enumerate(criteria.items()):
				params[f"criteria[{i}][key]"] = key
				params[f"criteria[{i}][value]"] = value
			return self._call("core_course_get_categories", params)
		return self._call("core_course_get_categories")

	def create_categories(self, categories: List[Dict]) -> List[Dict]:
		"""Crear categorías."""
		params = {}
		for i, cat in enumerate(categories):
			for key, value in cat.items():
				params[f"categories[{i}][{key}]"] = value
		return self._call("core_course_create_categories", params)
