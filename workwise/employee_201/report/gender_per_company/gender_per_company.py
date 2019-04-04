# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, company = get_columns(filters)
	data,gender = get_data(filters,company)
	chart = get_chart(filters,company,data,gender)

	return columns, data, None, chart

def get_columns(filters):
	columns = [
		{
			"fieldname": "gender",
			"label": _("Gender"),
			"fieldtype": "Link",
			"options":"Gender",
			"width": 150
		},
	]
	additional_filter = ""
	if filters.company:
		additional_filter += "WHERE `name`='"+filters.company+"'"
	company = frappe.db.sql("""SELECT `name` FROM `tabCompany`"""+additional_filter,as_dict=True)
	for com in company:
		columns.append({
			"fieldname": com.name,
			"label": com.name,
			"fieldtype": "Data",
			"width": 150
		})

	columns.append({"fieldname": "total",
			"label": "Total",
			"fieldtype": "Data",
			"width": 150})

	return columns,company

def get_data(filters,company):
	data = []
	gender = frappe.db.sql("""SELECT `name` FROM `tabGender`""",as_dict=True)
	for gen in gender:
		total = 0
		row = {'gender':gen.name}
		for com in company:
			result = frappe.db.sql("""SELECT COUNT(`name`) as count FROM `tabEmployee` WHERE gender = %s AND company = %s""",(gen.name,com.name),as_dict=True)
			row.update({com.name:result[0].count})
			total += result[0].count
		row.update({'total':total})
		data.append(row)
	return data, gender

def get_chart(filters,company,data,gender):
	datasets = []
	if filters.company:
		labels = [d.get("name") for d in gender]
		values = [d.get(filters.company) for d in data]
		datasets.append({'title':'Employee', 'values': values})
		title=filters.company
	else:
		labels = [d.get("name") for d in company]
		for idx, g in enumerate(gender):
			values = []
			for l in labels:
				count = [d.get(l) for d in data]
				values.append(count[idx])
			datasets.append({'title':g.name,'values':values})
		title = "Gender per Department"
	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}
	chart["title"] = title
	chart["type"] = "bar"
	chart["colors"] = ['green', 'blue', 'orange']
	return chart

