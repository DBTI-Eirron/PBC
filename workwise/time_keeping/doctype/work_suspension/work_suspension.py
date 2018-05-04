# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import chk_time_format

class WorkSuspension(Document):

	def validate(self):
		self.validate_time_format()
		self.validate_date()

	def validate_time_format(self):
		for d in self.get('dates'):
			chk_time_format(d.suspension_start, "%H:%M:%S")
			chk_time_format(d.suspension_end, "%H:%M:%S")

	def validate_date(self):
		if self.from_date > self.to_date:
			frappe.throw(_("From Date must be before To Date"))

		for d in self.get('dates'):
			exist = frappe.db.sql("""SELECT WS.`name` FROM `tabWork Suspension` WS 
				INNER JOIN `tabWork Suspension Dates` WSD ON WSD.parent = WS.`name`
				WHERE WSD.target_date = %s AND WS.company = %s AND WS.`name` != %s AND WS.docstatus = 1  """,(d.target_date, self.company, self.name) )
			if exist:
				frappe.throw(_("Work Suspension Already Filed on {0} for {1}").format(d.target_date, self.company))

	def get_dates(self):
		if not self.from_date and not self.to_date:
			frappe.throw(_("No From Date and To Date is Required"))
		
		if self.from_date > self.to_date:
			frappe.throw(_("To From Date Should be Greater than To"))
			
		else:
			dates, entries, dates_table = [], [], []
			start = datetime.datetime.strptime(self.from_date, '%Y-%m-%d')
			end = datetime.datetime.strptime(self.to_date, '%Y-%m-%d')
			step = datetime.timedelta(days=1)
			while start <= end:
				dates.append(start.date());
				start += step

			for i in dates:
				info = { "target_date": i, "time_in": "", "time_out": "", }
				dates_table.append(info);
			self.set('dates', [])
			for d in sorted(list(dates_table), key=lambda k: k['target_date']):
				row = self.append('dates', {})
				row.update(d)