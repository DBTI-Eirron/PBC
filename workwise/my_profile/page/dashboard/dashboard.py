from __future__ import unicode_literals
import frappe 
from frappe import _
from frappe.model.document import Document

class Dashboard(Document):
	def get_employee_gender_count_via_location(self):
		thecount = []

		return thecount


@frappe.whitelist()
def get_employee_locations():
	locations = []
	locationlist = frappe.db.sql("""SELECT location FROM `tabEmployee` GROUP BY location  """, as_dict=True)
	for l in locationlist:
		locs = l.locationlist
		locations.append(locs)

	return locations

@frappe.whitelist()
def get_test_data():
	test = """Manila, Cebu, Laguna """
	return test
