# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.utils import getdate
from frappe.utils import flt
from frappe import _

def execute(filters=None):

	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):

	columns = [
		{
			"fieldname": "data",
			"label": _("Data"),
			"fieldtype": "Data",
			"width": 400
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "total_hours",
			"label": _("Total Hours"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "tags",
			"label": _("Tags"),
			"fieldtype": "Data",
			"width": 400
		},
	]

	return columns

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)
	return result

def get_register(filters, emp, pay_from, pay_to):
	register = frappe.db.sql("""SELECT DISTINCT * FROM `tabAttendance Register` 
		WHERE employee = %(employee)s AND target_date >= %(from_date)s AND target_date <= %(to_date)s
		ORDER BY target_date ASC""",{
			"employee": emp,
			"from_date": pay_from,
			"to_date": pay_to,
		}, as_dict=True)

	return register

def get_data(filters):
	#Initialize
	data = []
	data.append({"data":"<b>Company: </b>"+filters.company+"",})
	data.append({})

	employees = get_employees(filters)
	ot_map = get_overtime_map()
	for emp in employees:
		if emp.overtime > 0 or emp.overtime_nd > 0 or emp.overtime_ex > 0:
			register = get_register(filters, emp.name, filters.from_date, filters.to_date)
			data.append({"data":"<b>Employee: </b>"+emp.full_name+"",})
			data.append({"data":"<b>Employee ID: </b>"+emp.name+"",})
			total_ob_hrs = 0.0
			is_sunday = 0
			is_saturday = 0
			for reg in register:
				if reg.overtime > 0 or reg.overtime_nd > 0 or reg.overtime_ex > 0:
					tags = ""
					ot_list = ""
					target_date = datetime.datetime.strptime(str(reg.target_date), '%Y-%m-%d').strftime("%A")
					if target_date == "Sunday":
						is_sunday = 1
					if target_date == "Saturday":
						is_saturday = 1

					if reg.overtime > 0:
						overtime_type = [reg.is_restday, reg.is_holiday, reg.is_sp_holiday, reg.is_db_holiday, is_sunday, is_saturday, 0, 0]
						overtime_type = ''.join(str(x) for x in overtime_type)
						if overtime_type in ot_map:
							tags += " <span class='label label-success'> "+ot_map[overtime_type]['name']+" "+str(flt(reg.overtime, 2))+" Hrs </span> "
						else:
							tags += " <span class='label label-success'>Ordinary Overtime "+str(flt(reg.overtime, 2))+" Hrs </span> "
					if reg.overtime_nd > 0:
						overtime_type = [reg.is_restday, reg.is_holiday, reg.is_sp_holiday, reg.is_db_holiday, is_sunday, is_saturday, 0, 1]
						overtime_type = ''.join(str(x) for x in overtime_type)
						if overtime_type in ot_map:
							tags += " <span class='label label-success'> "+ot_map[overtime_type]['name']+" "+str(flt(reg.overtime_nd, 2))+" Hrs </span> "
						else:
							tags += " <span class='label label-success'>Night Differential Overtime"+str(flt(reg.overtime_nd, 2))+" Hrs </span> "
					if reg.overtime_ex > 0:
						overtime_type = [reg.is_restday, reg.is_holiday, reg.is_sp_holiday, reg.is_db_holiday, is_sunday, is_saturday, 1, 0]
						overtime_type = ''.join(str(x) for x in overtime_type)
						if overtime_type in ot_map:
							tags += " <span class='label label-success'> "+ot_map[overtime_type]['name']+" "+str(flt(reg.overtime_ex, 2))+" Hrs </span> "
						else:
							tags += " <span class='label label-success'>Overtime Excess"+str(flt(reg.overtime_ex, 2))+" Hrs </span> "

					ot_apps = get_ot_list(emp.name, reg.target_date)
					for app in ot_apps:
						if ot_list:
							ot_list += ", "+app.name
						else:
							ot_list = app.name

					entry = {
						"date": getdate(reg.target_date),
						"data": ot_list,
						"total_hours": '{:,.2f}'.format(flt(reg.overtime, 2)+flt(reg.overtime_nd, 2)+flt(reg.overtime_ex, 2)),
						"tags": tags
					}
					total_ob_hrs += flt(reg.overtime, 2)+flt(reg.overtime_nd, 2)+flt(reg.overtime_ex, 2)
					data.append(entry)

			data.append({
				"data":"<b>Total</b>",
				"total_hours": flt(total_ob_hrs, 2)
			})
			data.append({})

	return data

def get_overtime_map():
	ot_map = {}
	ot = frappe.db.sql(""" SELECT ot_name, ot_code, ot_rate FROM `tabOvertime Rates` """, as_dict=1)
	for t in ot:
		ot_map[t.ot_code] = {
			"name": t.ot_name
		}
	return ot_map

def get_ot_list(employee, target_date):
	ot_apps = frappe.db.sql("""SELECT `name` FROM `tabOvertime Application` 
		WHERE workflow_state = 'Approved' AND employee = %s AND target_date >= %s 
		AND target_date <= %s """,(employee, target_date, target_date), as_dict=1)

	return ot_apps

def convert_secs(filters, secs):
	con = 0
	if filters.time_options == "Mins":
		con = flt(secs, 8) * 60
	else:
		con = flt(secs, 8)
	return flt(con, 8)

def get_employees(filters):
	register = frappe.db.sql("""SELECT DISTINCT TE.`name`, TE.full_name, AR.overtime, AR.overtime_nd, AR.overtime_ex FROM `tabAttendance Register` AR INNER JOIN `tabEmployee` TE ON AR.employee=TE.`name`
		WHERE AR.`target_date` >= %(from_date)s AND AR.`target_date` <= %(to_date)s AND TE.`company` = %(company)s {conditions}
		ORDER BY AR.`target_date` ASC""".format(conditions=get_conditions(filters)),{
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"company": filters.company,
		}, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("TE.`name`=%(employee)s")


	return "and {}".format(" and ".join(conditions)) if conditions else "" 