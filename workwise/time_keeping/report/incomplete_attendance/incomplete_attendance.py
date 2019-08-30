# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import cint, flt, getdate, cstr
from frappe import _
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str

def execute(filters=None):
	
	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "emp_name",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 350
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "shift",
			"label": _("Shift"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "time_in",
			"label": _("Time In"),
			"fieldtype": "Data",
			"width": 130
		},		
		{
			"fieldname": "time_out",
			"label": _("Time Out"),
			"fieldtype": "Data",
			"width": 130
		},
		{
			"fieldname": "particulars",
			"label": _("Particulars"),
			"fieldtype": "Data",
			"width": 200
		},
	]

	return columns

def get_result(filters):

	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_register(filters, pay_from, pay_to):
	register = frappe.db.sql("""SELECT AR.target_date, AR.work_shift, AR.card_in, AR.card_out, AR.employee, TE.full_name, AR.is_absent, AR.late, AR.undertime
		FROM `tabAttendance Register` AR INNER JOIN `tabEmployee` TE ON AR.`employee` = TE.`name`
		WHERE AR.target_date >= %(from_date)s AND AR.target_date <= %(to_date)s {conditions}
		ORDER BY TE.full_name, AR.target_date ASC""".format(conditions=get_conditions(filters)),{
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	return register

def get_data(filters):
	#Initialize
	data = []
	data_entry = {}
	#pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["from_date", "to_date"])
	pay_from = getdate(filters.from_date)
	pay_to = getdate(filters.to_date)

	data.append({	"emp_name":"<b>Company: </b>"+filters.company+"",	})
	if filters.department:
		data.append({	"emp_name":"<b>Department: </b>"+filters.department+"</b>",	})
	data.append({	"emp_name":"<b>Period: </b>"+cstr(filters.payroll_period)+"</b>",	})
	data.append({})

	register = get_register(filters, pay_from, pay_to)
	if register:
		for reg in register:
			tags = ""
			if reg.is_absent > 0 or reg.late > 0 or reg.undertime > 0:
				if reg.employee not in data_entry:
					data_entry[cstr(reg.employee)] = {
						"employee": cstr(reg.employee),
						"employee_name": cstr(reg.full_name),
						"incomlete_attendance": {}
					}

				tags += " <span class='label label-danger'> Late </span> " if reg.late > 0 else ""
				tags += " <span class='label label-danger'> Undertime </span> " if reg.undertime > 0 else ""
				tags += " <span class='label label-danger'> Absent </span> " if reg.is_absent > 0 else ""

				data_entry[reg.employee]['incomlete_attendance'][reg.target_date] = {
					"date": reg.target_date,
					"shift": reg.work_shift,
					"time_in": reg.card_in,
					"time_out": reg.card_out,
					"particulars": tags,
				}
		#frappe.throw(_(sorted(data_entry.items(), key=lambda x: x['employee_name'])))
		for dat in data_entry:
			data.append({	"emp_name":"<b>Employee Name: </b>"+cstr(data_entry[dat]['employee_name'])+"</b>",	})
			data.append({	"emp_name":"<b>ID Number: </b>"+cstr(dat)+"</b>",	})

			for i in sorted(data_entry[dat]['incomlete_attendance']):
				data.append({
					"date": data_entry[dat]['incomlete_attendance'][i]['date'],
					"shift": data_entry[dat]['incomlete_attendance'][i]['shift'],
					"time_in": data_entry[dat]['incomlete_attendance'][i]['time_in'],
					"time_out": data_entry[dat]['incomlete_attendance'][i]['time_out'],
					"particulars": data_entry[dat]['incomlete_attendance'][i]['particulars'],
				})

	return data

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("AR.`employee`='{0}'".format(filters.employee))

	if filters.get("department"):
		conditions.append("TE.`department`='{0}'".format(filters.department))

	if filters.get("company"):
		conditions.append("TE.`company`='{0}'".format(filters.company))

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

def get_result_as_list(data, filters):
	result = []
	for d in data:		
		result.append(d)
	return result