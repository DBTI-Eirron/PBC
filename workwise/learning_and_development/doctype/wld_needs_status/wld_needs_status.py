# -*- coding: utf-8 -*-
# Copyright (c) 2019, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class WLDNeedsStatus(Document):
	def validate(self):
		for d in self.get('status_table'):
			if d.new_status:
				frappe.db.sql("""UPDATE `tabWLD Needs Table` SET `status` = %s WHERE `parent` = %s AND `employee` = %s AND `training` = %s """,( d.new_status, self.wld_needs_id, d.employee, d.training ), as_dict=True )
				frappe.db.commit()