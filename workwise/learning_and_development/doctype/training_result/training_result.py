# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TrainingResult(Document):
	def validate(self):
		training_event = frappe.get_doc("Training Event", self.training_event)
		if training_event.docstatus != 1:
			frappe.throw(_('{0} must be submitted').format(_('Training Event')))

		#self.employee_emails = ', '.join(get_employee_emails([d.employee
			#for d in self.employees]))

	def on_submit(self):
		pass

#@frappe.whitelist()
#def get_employees(training_event):
#	return frappe.get_doc("Training Event", training_event).employees
