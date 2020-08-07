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
		{
			"module_name": "Dashboard",
			"color": "#4d90fe",
			"icon": "fa fa-dashboard",
			"type": "module",
			"label": _("Dashboard"),
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
			"module_name": "Learning and Development",
			"color": "#3cc051",
			"icon": "fa fa-book",
			"type": "module",
			"label": _("Learning and Development"),
			"reverse": 0
		},
		{
			"module_name": "Talent Acquisition",
			"color": "#3cc051",
			"icon": "fa fa-lightbulb-o",
			"type": "module",
			"label": _("Talent Acquisition"),
			"reverse": 0
		},
		{
			"module_name": "Performance Management",
			"color": "#3cc051",
			"icon": "fa fa-line-chart",
			"type": "module",
			"label": _("Performance Management"),
			"reverse": 0
		},
		{
			"module_name": "Analytics",
			"color": "#3cc051",
			"icon": "fa fa-line-chart",
			"type": "module",
			"label": _("Analytics"),
			"reverse": 0
		},
		{
			"module_name": "Utilities",
			"color": "#666666",
			"icon": "fa fa-wrench",
			"type": "module",
			"label": _("Utilities"),
			"reverse": 1
		},
	]
