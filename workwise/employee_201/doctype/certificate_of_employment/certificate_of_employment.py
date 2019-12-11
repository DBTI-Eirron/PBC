# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date

class CertificateofEmployment(Document):
	def get_to_date(self):
		if self.employee:
			resign_date,term_date,retired_date = frappe.get_value('Employee', self.employee, ['date_resigned','date_terminated','date_retired'])
			if resign_date:
				self.to_date = resign_date
			elif term_date:
				self.to_date = term_date
			elif retired_date:
				self.to_date = retired_date
			else:
				self.to_date = date.today()
