# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, company = get_columns(filters)
	data,ages = get_data(filters,company)
	chart = get_chart(filters,company,data,ages)

	return columns, data, None, chart

def get_columns(filters):
	columns = [
		{
			"fieldname": "age",
			"label": _("Age"),
			"fieldtype": "Data",
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
	ages = frappe.db.sql("""SELECT DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(), birthday)), "%Y")+0 as age FROM `tabEmployee` WHERE `is_active` = 1 GROUP BY DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(), birthday)), "%Y")+0 """, as_dict=True)
	for age in ages:
		total = 0
		row = {'age':age.age}
		for com in company:
			result = frappe.db.sql("""SELECT DISTINCT COUNT(*) as count FROM `tabEmployee` WHERE `is_active` = 1 AND DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(), birthday)), '%%Y') + 0 = %s and company = %s""",(age.age,com.name),as_dict=True)
			row.update({com.name:result[0].count})
			total += result[0].count
		row.update({'total':total})
		data.append(row)
	return data, ages

def get_chart(filters,company,data,ages):
	datasets = []
	if filters.company:
		labels = [d.get("age") for d in ages]
		values = [d.get(filters.company) for d in data]
		datasets.append({'title':'Employee', 'values': values})
		title=filters.company
	else:
		labels = [d.get("name") for d in company]
		for idx, g in enumerate(ages):
			values = []
			for l in labels:
				count = [d.get(l) for d in data]
				values.append(count[idx])
			datasets.append({'title':g.age,'values':values})
		title = "Age per Department"
	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}
	chart["title"] = title
	chart["type"] = "pie"
	chart["colors"] = ['green', 'blue', 'orange']
	return chart

