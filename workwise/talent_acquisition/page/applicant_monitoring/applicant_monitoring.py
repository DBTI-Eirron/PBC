# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate, formatdate
from frappe.model.document import Document

class Modules(Document):
	pass

@frappe.whitelist()
def get_candidates(target_doc=None):
	info = {
		"candidates": "",
		"for_interview": "",
		"for_assessment": "",
		"job_offer": "",
		"for_employee": "",
		"ar": "",
	}
	info['candidates'] = frappe.db.sql("""SELECT * FROM `tabJob Applicant` WHERE docstatus = 0  AND apply_type = 'Candidate'""", as_dict=1)
	info['for_assessment'] = frappe.db.sql("""SELECT * FROM `tabJob Applicant` WHERE apply_type = 'For Assessment' AND docstatus = 1 """, as_dict=1)
	info['for_interview'] = frappe.db.sql("""SELECT * FROM `tabSchedules and Assessment` WHERE apply_type = 'For Interview' AND docstatus = 1 """, as_dict=1)
	info['job_offer'] = frappe.db.sql("""SELECT * FROM `tabInterview and Background` WHERE apply_type = 'Job Offer' AND docstatus = 1 """, as_dict=1)
	info['for_employee'] = frappe.db.sql("""SELECT * FROM `tabOffer Letter` WHERE status = 'Accepted' AND docstatus = 1 AND apply_type != 'Completed' """, as_dict=1)
	info['ar'] = frappe.db.sql("""SELECT * FROM `tabPersonnel Requisition` WHERE docstatus = 1 """, as_dict=1)
	
	return info

@frappe.whitelist()
def get_dashboard_info(target_doc=None):
	info = {
		"bday": "",
		"todo": "",
		"apps": "",
	}
	bday_today = datetime.date.strftime(getdate(nowdate()), '%b')
	info['bday'] = frappe.db.sql(""" SELECT full_name, profile_picture, DATE_FORMAT(birthday, '%%M %%d') as birthday FROM `tabEmployee` WHERE DATE_FORMAT(birthday, '%%b') = %s ORDER BY birthday """, (bday_today), as_dict=1)
	info['todo'] = frappe.db.sql("""SELECT * FROM `tabToDo` WHERE owner = %s """, (frappe.session.user), as_dict=1)
	info['post'] = frappe.db.sql("""SELECT P.post_description, E.profile_picture, E.full_name, P.creation FROM `tabPublic Post` P LEFT JOIN `tabEmployee` E ON E.user_id = P.owner ORDER BY P.creation DESC """, as_dict=1)

	employee_info = frappe.db.sql("""SELECT `name`, first_name, last_name, middle_name, profile_picture, birthday, full_name FROM `tabEmployee` WHERE user_id = %s LIMIT 1 """,( frappe.session.user ), as_dict=1)
	info['emp_info'] = employee_info 

	if employee_info:
		for emp in employee_info:
			app_type = ["Leave Application", "Overtime Application", "Official Business Application"]
			for d in app_type:
				sql = frappe.db.sql(""" SELECT `name`, full_name, from_date, '%s' as app_type FROM `tab%s` 
					WHERE workflow_state = "Pending" AND employee IN 
					( SELECT for_value FROM `tabUser Permission` ES WHERE `user` = '%s' 
					AND allow = 'Employee' AND for_value != '%s' ) """ % ( d, d, frappe.session.user, emp.name ), as_dict=1)

				if info['apps'] == "": 
					info['apps'] = sql
				else:
					info['apps'] += sql

	return info

@frappe.whitelist()
def post_dashboard(post_description):
	post = frappe.new_doc("Public Post")
	post.update({
		"post_description": post_description,
	})
	if post.insert():
		return 1

@frappe.whitelist()
def get_employee_gender_data():
	datasetlist = []
	valuelist = []
	companylist = []
	genderlist = []
	g_count = []
	c_count = []

	companies = frappe.db.sql("""SELECT DISTINCT `name` as company FROM `tabCompany` ORDER BY `name`""", as_dict=True)
	for a in companies:
		companylist.append(a.company)

	genders = frappe.db.sql("""SELECT DISTINCT `name` as gender FROM `tabGender` ORDER BY `name`""", as_dict=True)
	for b in genders:
		genderlist.append(b.gender)

	gender_count = frappe.db.sql("""SELECT DISTINCT count(*) as count FROM `tabGender`""", as_dict=True)
	for c in gender_count:
		g_count.append(c.count)

	company_count = frappe.db.sql("""SELECT DISTINCT count(*) as count FROM `tabCompany`""", as_dict=True)
	for d in company_count:
		c_count.append(d.count)

	com_count = c_count[0] - 1
	gen_count = g_count[0] - 1
	while (gen_count >= 0):
		com_count = c_count[0] - 1
		valuelist = []
		while (com_count >= 0):
			employee_count = frappe.db.sql("""SELECT DISTINCT COUNT(*) as count FROM `tabEmployee` WHERE company = %(company)s AND gender = %(gender)s""",{
				"company": companylist[com_count],
				"gender": genderlist[gen_count]
			}, as_dict=True)

			for e in employee_count:
				valuelist.append(e.count)

			com_count = com_count - 1

		datasets = {
			'title': genderlist[gen_count],
			'values': valuelist,
		},
		datasetlist.extend(datasets)

		gen_count = gen_count - 1

	companylist.reverse()

	entries = {
			'labels': companylist,
			'datasets': datasetlist
		}
	return entries

@frappe.whitelist()
def get_employee_age_data():
	datasetlist = []
	valuelist = []
	agelist = []

	ages = frappe.db.sql("""SELECT DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(), birthday)), "%Y")+0 as age FROM `tabEmployee` GROUP BY age ORDER BY age""", as_dict=True)
	for b in ages:
		agelist.append(int(b.age))

		employee_count = frappe.db.sql("""SELECT DISTINCT COUNT(*) as count FROM `tabEmployee` WHERE DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(), birthday)), '%%Y') + 0 = %(age)s""",{
			"age": int(b.age)
		}, as_dict=True)

		for e in employee_count:
			valuelist.append(e.count)

	datasets = {
		'title': 'Employees',
		'values': valuelist,
	},
	datasetlist.extend(datasets)

	entries = {
			'labels': agelist,
			'datasets': datasetlist
		}
	return entries
