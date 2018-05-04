# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class TransactionType(Document):
	def on_trash(self):
		if self.is_standard == 1:
			frappe.throw(_("Cannot delete Standard Transaction Type"))