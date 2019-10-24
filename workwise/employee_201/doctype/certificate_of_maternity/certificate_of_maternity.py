# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date
from workwise.time_keeping.application_utils import validate_inactive_employee

class CertificateofMaternity(Document):
	def validate(self):
		validate_inactive_employee(self)

	def get_to_date(self):
		resign_date = frappe.get_value('Employee', self.employee, 'date_resigned')
		if resign_date:
			self.to_date = resign_date
		else:
			self.to_date = date.today()
