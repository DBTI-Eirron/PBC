# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class JasperReportForms(Document):
	pass

@frappe.whitelist()
def get_report_forms(report_name):
	forms = frappe.db.sql(""" SELECT * FROM `tabJasper Report Form` WHERE linked_report = %s """, report_name, as_dict=True)
	for d in forms:
		d['form_ip'] = frappe.db.get_single_value('Jasper Settings', 'jasper_ip')
		d['form_port'] = frappe.db.get_single_value('Jasper Settings', 'jasper_port')
		d['form_user'] = frappe.db.get_single_value('Jasper Settings', 'jasper_user')
		d['form_pass'] = frappe.db.get_single_value('Jasper Settings', 'jasper_pass')

	return forms

def get_server_info(report_name):
	forms = frappe.db.sql(""" SELECT * FROM `tabJasper Report Form` WHERE linked_report = %s """, report_name, as_dict=True)
	for d in forms:
		d['form_ip'] = frappe.db.get_single_value('Jasper Settings', 'jasper_ip')
		d['form_port'] = frappe.db.get_single_value('Jasper Settings', 'jasper_port')
		d['form_user'] = frappe.db.get_single_value('Jasper Settings', 'jasper_user')
		d['form_pass'] = frappe.db.get_single_value('Jasper Settings', 'jasper_pass')

	return forms