# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class OvertimeRates(Document):
	def validate(self):
		self.get_code()

	def get_code(self):
		#[RD][HO][SHO][DHO][SUN][SAT][EX][ND]
		overtime_type = [self.is_restday, self.is_holiday, self.is_sp_holiday, self.is_db_holiday, self.is_sunday, self.is_saturday, self.is_excess, self.is_ndiff]
		overtime_type = ''.join(str(x) for x in overtime_type)
		self.ot_code = overtime_type