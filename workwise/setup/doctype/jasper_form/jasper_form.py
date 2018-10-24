# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class JasperForm(Document):
	pass

@frappe.whitelist()
def get_forms(doctype_name):
	forms = frappe.db.sql(""" SELECT * FROM `tabJasper Form` WHERE linked_doctype = %s """, doctype_name, as_dict=True)
	for d in forms:
		d['form_ip'] = frappe.db.get_single_value('Jasper Settings', 'jasper_ip')
		d['form_port'] = frappe.db.get_single_value('Jasper Settings', 'jasper_port')
		d['form_user'] = frappe.db.get_single_value('Jasper Settings', 'jasper_user')
		d['form_pass'] = frappe.db.get_single_value('Jasper Settings', 'jasper_pass')

	return forms

@frappe.whitelist()
def get_server_info():
	j_ip = frappe.db.get_single_value('Jasper Settings', 'jasper_ip')
	j_port = frappe.db.get_single_value('Jasper Settings', 'jasper_port')
	j_user = frappe.db.get_single_value('Jasper Settings', 'jasper_user')
	j_pass = frappe.db.get_single_value('Jasper Settings', 'jasper_pass')	
	forms = {
		"jasper_ip": j_ip,
		"jasper_port": j_port,
		"jasper_user": j_user,
		"jasper_pass": j_pass,
	}

	return forms