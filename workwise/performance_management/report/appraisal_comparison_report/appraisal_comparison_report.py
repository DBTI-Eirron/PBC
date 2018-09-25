# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	result = get_result(filters)
	return columns, result

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)
	return result

def get_columns(filters):
	columns = [
		_("Goal") + "::200",
		_("Total Score (360-Degree)") + "::200",
		_("Total Score (Standard)") + "::200",
		_("Average") + "::200",
	]

	return columns

def get_data(filters):
	entries = []
	appr = frappe.db.sql("""SELECT `appraisal_template`
		FROM `tabAppraisal`
		WHERE employee = %(employee)s AND appraisal_dates = %(appraisal_date)s AND docstatus = '1' LIMIT 1""",{
			"employee": filters.employee,
			"appraisal_date": filters.appraisal_dates
		})

	if appr:
		template = appr[0][0]
	else:
		frappe.throw(_("No template for the selected criteria"))

	goals = frappe.db.sql("""SELECT kra
		FROM `tabAppraisal Template` AT
		INNER JOIN `tabAppraisal Template Goal` AG ON AT.`name` = AG.parent
		WHERE AT.`name` = %(template)s ORDER BY AG.idx """,{
			"template": template,
		}, as_dict=True)

	standard = frappe.db.sql("""SELECT kra, score_earned
		FROM `tabAppraisal` AT
		INNER JOIN `tabAppraisal Goal` AG ON AT.`name` = AG.parent
		WHERE AT.employee = %(employee)s AND AT.appraisal_dates = %(appraisal_date)s AND appraisal_type = 'Standard' """,{
			"employee": filters.employee,
			"appraisal_date": filters.appraisal_dates
		}, as_dict=True)
	
	degree = frappe.db.sql("""SELECT kra, score_earned
		FROM `tabAppraisal` AT
		INNER JOIN `tabAppraisal Goal` AG ON AT.`name` = AG.parent
		WHERE AT.employee = %(employee)s AND AT.appraisal_dates = %(appraisal_date)s AND appraisal_type = '360-Degree' """,{
			"employee": filters.employee,
			"appraisal_date": filters.appraisal_dates
		}, as_dict=True)	

	for g in goals:
		entry = {
			"goals": g.kra,
			"employee_score": 0.0,
			"supervisor_score": 0.0,
			"average": 0.0,
		}

		for st in standard:
			if st.kra == g.kra:
				entry['supervisor_score'] = st.score_earned

		for d in degree:
			if d.kra == g.kra:
				entry['employee_score'] = d.score_earned

		entry['average'] = (entry['supervisor_score'] + entry['employee_score']) / 2 

		entries.append(entry)

	return entries

def get_conditions(filters):
	conditions = []

	if filters.get("employee"):
		emp_name = filters.get("employee")
		conditions.append("TA.employee LIKE '%%"+emp_name+"%%' ")

	if filters.get("appraisal_dates"):
		app_dates = filters.get("appraisal_dates")
		conditions.append("TA.appraisal_dates LIKE '%%"+app_dates+"%%' ")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_result_as_list(data, filters):
	result = []
	for d in data:
		row = [
			d.get("goals"),
			d.get("employee_score"),
			d.get("supervisor_score"),
			d.get("average"),
		]

		result.append(row)

	return result