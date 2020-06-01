# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date

class CertificateofMaternity(Document):
	def validate(self):
		pass
	def get_to_date(self):
		if self.employee:
			resign_date,eoc,retired_date,terminated_date = frappe.get_value('Employee', self.employee, ['date_resigned','date_contract_ended','date_retired','date_terminated'])
			if resign_date:
				self.to_date = resign_date
			elif eoc:
				self.to_date = eoc
			elif retired_date:
				self.to_date = retired_date
			elif terminated_date:
				self.to_date = terminated_date
			else:
				self.to_date = date.today()
