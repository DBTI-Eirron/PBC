# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

def get_notification_config():
	notification_for_doctype =  { "for_doctype":
		{
			"Memo": {"involvement": "Offender"},
			"Memo": {"involvement": "Witness"},
			"Memo": {"involvement": "Complainant"},
			"Job Applicant": {"status": "Open"},
			"Appraisal": {"appraisal_type": "360-Degree"},
		}
	}

	doctype = [d for d in notification_for_doctype.get('for_doctype')]
	for doc in frappe.get_all('DocType',
		fields= ["name"], filters = {"name": ("not in", doctype), 'is_submittable': 1}):
		notification_for_doctype["for_doctype"][doc.name] = {"docstatus": 1}

	return notification_for_doctype
