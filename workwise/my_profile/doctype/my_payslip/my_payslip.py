# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from frappe.model.document import Document

class MyPayslip(Document):
	def check_password(self, args):
		access = False
		if frappe.local.login_manager.check_password(frappe.session.user, args['filters']):
			access = True
			
		return access