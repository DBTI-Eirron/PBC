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
			"Leave Application": {"workflow_state": "Pending"},
			"Overtime Application": {"workflow_state": "Pending"},
			"Official Business Application": {"workflow_state": "Pending"},
			"Change Schedule Application": {"workflow_state": "Pending"},
			"Undertime Application": {"workflow_state": "Pending"},
			"Excuse Tardiness Application": {"workflow_state": "Pending"},
			"DTR Problem Application": {"workflow_state": "Pending"},
			"Compensatory Time Off": {"workflow_state": "Pending"},
			"Blanket": {"workflow_state": "Pending"},
			"Work Suspension": {"workflow_state": "Pending"},
			"Loan Application": {"workflow_state": "Pending"},
			"Appraisal": {"appraisal_type": "360-Degree"},
			"Job Applicant": {"status": "Open"},
			
		}
	}

	doctype = [d for d in notification_for_doctype.get('for_doctype')]
	for doc in frappe.get_all('DocType',
		fields= ["name"], filters = {"name": ("not in", doctype), 'is_submittable': 1}):
		notification_for_doctype["for_doctype"][doc.name] = {"docstatus": 1}

	return notification_for_doctype
