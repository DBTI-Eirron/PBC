# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document

class BiometricsDevice(Document):
	def validate(self):
		self.test_connection()

	def test_connection(self):
		frappe.throw(_("s"))
