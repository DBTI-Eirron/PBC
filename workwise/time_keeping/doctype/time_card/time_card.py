# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime, hashlib
from frappe import throw, _
from frappe.utils import cstr
from frappe.model.document import Document

class TimeCard(Document):
	def autoname(self):
		date_str = datetime.datetime.strptime(self.date, '%Y-%m-%d')
		time_str = datetime.datetime.strptime(self.time, '%H:%M:%S')
		combined_datetime = datetime.datetime.combine(date_str.date(), time_str.time())
		salt = hashlib.md5(str(self.biometrics_id) + str(combined_datetime) + str(self.card_type))
		self.name = salt.hexdigest()