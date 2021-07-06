# -*- coding: utf-8 -*-
# Copyright (c) 2021, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class EmployeeMovementSetup(Document):
	def validate(self):
		#self.validate_duplicate()
		self.create_custom_fields()

	def validate_duplicate(self):
		ems = frappe.get_all('Employee Movement', filters={'movement_type': self.movement_type})
		if ems:
			for em in ems:
				if em.name != self.name:
					frappe.throw(_('Setup for {0} already exists'.format(self.movement_type) ))

	def create_custom_fields(self):
		if self.enabled:
			if self.fields:
				last_current = str(self.movement_type).replace(" ", "_").lower()+'_additional_sectionbreak'
				last_new = None
				for d in self.fields:
					current_fields = frappe.get_all('Custom Field', filters={'dt': 'Employee Movement', 'label': 'Current '+str(d.label), 'fieldname': 'current_'+str(d.fieldname)}, fields=['*'])
					
					if not current_fields:
						cur_custom = frappe.new_doc("Custom Field")
						cur_custom.update({
							'dt': 'Employee Movement',
							'label': 'Current '+str(d.label),
							'insert_after': 'additional_changes_section',
							'fieldname': 'current_'+str(d.fieldname),
							'fieldtype': d.fieldtype,
							'options': d.options,
							'read_only': 1
						})
						try:
							cur_custom.insert(ignore_permissions=True)
						except Exception as e:
							raise
						last_current = 'current_'+str(d.fieldname)

					new_fields = frappe.get_all('Custom Field', filters={'dt': 'Employee Movement', 'label': 'New '+str(d.label), 'fieldname': 'new_'+str(d.fieldname)}, fields=['*'])

					if not new_fields:
						if not last_new:
							last_new = last_current

						new_custom = frappe.new_doc("Custom Field")
						new_custom.update({
							'dt': 'Employee Movement',
							'label': 'New '+str(d.label),
							'insert_after': last_current,
							'fieldname': 'new_'+str(d.fieldname),
							'fieldtype': d.fieldtype,
							'options': d.options,
						})
						try:
							new_custom.insert(ignore_permissions=True)
						except Exception as e:
							raise
						last_new = 'new_'+str(d.fieldname)