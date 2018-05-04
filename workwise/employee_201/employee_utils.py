# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def set_employee_name(doc):
	if frappe.session.user:
		frappe.db.get_value("Employee", doc.employee, "full_name")