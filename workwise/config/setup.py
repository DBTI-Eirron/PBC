from __future__ import unicode_literals
from frappe import _
from frappe.desk.moduleview import add_setup_section

def get_data():
	return [
		{
			"label": _("Jasper Settings"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Jasper Form",
				},
				{
					"type": "doctype",
					"name": "Jasper Settings",
				},
			]
		},
	]
