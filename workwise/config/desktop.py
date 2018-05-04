# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "workwise",
			"color": "#589494",
			"icon": "octicon octicon-book",
			"type": "module",
			"label": _("workwise")
		},
		{
			"module_name": "Employee 201",
			"color": "#3cc051",
			"icon": "fa fa-vcard-o",
			"type": "module",
			"label": _("Employee Records"),
			"reverse": 1
		},
		{
			"module_name": "HR",
			"color": "#4d90fe",
			"icon": "fa fa-users",
			"type": "module",
			"label": _("HR"),
			"reverse": 1
		},
		{
			"module_name": "My Profile",
			"color": "#4d90fe",
			"icon": "fa fa-user",
			"type": "module",
			"label": _("My Profile"),
			"reverse": 1
		},
		{
			"module_name": "Payroll",
			"color": "#4d90fe",
			"icon": "fa fa-money",
			"type": "module",
			"label": _("Payroll"),
			"reverse": 1
		},
		{
			"module_name": "Time Keeping",
			"color": "#4d90fe",
			"icon": "fa fa-clock-o",
			"type": "module",
			"label": _("Attendance Management"),
			"reverse": 1
		},
	]
