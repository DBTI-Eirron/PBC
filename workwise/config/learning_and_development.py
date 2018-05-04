from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Training and Development"),
			"items": [
				{
					"type": "doctype",
					"name": "Training Course",
					"description": _("Training Course"),
				},
				{
					"type": "doctype",
					"name": "Training Event",
					"description": _("Training Event"),
				},
				{
					"type": "doctype",
					"name": "Training Evaluation",
					"description": _("Training Evaluation"),
				},
			]
		},
	]