# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, getdate, cstr
from frappe import _

def execute(filters=None):

	columns = get_columns(filters)
	results = get_result(filters, columns)

	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee_id",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "location",
			"label": _("Location"),
			"fieldtype": "Link",
			"options": "Location",
			"width": 180
		},
		{
			"fieldname": "reg_hrs",
			"label": _("Work"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "absent",
			"label": _("Absent"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "tardy",
			"label": _("Tardy"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "ut",
			"label": _("UT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "sl",
			"label": _("SL"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "vl",
			"label": _("VL"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "bl",
			"label": _("BL"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "cto",
			"label": _("CTO"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "ot",
			"label": _("OT REG"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "ot_ex",
			"label": _("OT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "nd",
			"label": _("ND"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "nd_ot",
			"label": _("ND OT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_reg",
			"label": _("RD REG"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_ot",
			"label": _("RD OT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_nd",
			"label": _("RD ND"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_nd_ot",
			"label": _("RD NDOT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "sh_reg",
			"label": _("SH REG"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "sh_ot",
			"label": _("SH OT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "sh_nd",
			"label": _("SH ND"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "sh_nd_ot",
			"label": _("SH ND OT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "lh_reg",
			"label": _("LH REG"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "lh_ot",
			"label": _("LH OT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "lh_nd",
			"label": _("LH ND"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "lh_nd_ot",
			"label": _("LH NDOT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_sh_reg",
			"label": _("RD SHREG"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_sh_ot",
			"label": _("RD SHOT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_sh_nd",
			"label": _("RD SHND"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_sh_nd_ot",
			"label": _("RD SHNDOT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_lh_reg",
			"label": _("RD LHREG"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_lh_ot",
			"label": _("RD LHOT"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_lh_nd",
			"label": _("RD LHND"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "rd_lh_nd_ot",
			"label": _("RD LHNDOT"),
			"fieldtype": "Data",
			"width": 100
		},
	]

	return columns

def get_result(filters, columns):
	data = get_data(filters, columns)
	result = get_result_as_list(data, filters)

	return result

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)

	return result

def get_register(filters, pay_from, pay_to):
	register = frappe.db.sql("""SELECT AR.*, TE.`name` as employee_id, TE.`full_name`, TE.`location` 
		FROM `tabAttendance Register` AR INNER JOIN `tabEmployee` TE ON AR.`employee` = TE.`name`
		WHERE TE.`company` = %(company)s AND TE.`is_attendance_base` = 1 AND target_date >= %(from_date)s AND target_date <= %(to_date)s {conditions}
		GROUP BY AR.`name` ORDER BY TE.`full_name` ASC""".format(conditions=get_conditions(filters)), {
		"company": filters.company,
		"location": filters.location,
		"employee": filters.employee,
		"from_date": pay_from,
		"to_date": pay_to,
	}, as_dict=True)

	return register

def get_data(filters, columns):
	#Initialize
	data = []
	data_register = {}
	total_dict = {}

	field_list = ["reg_hrs", "absent", "tardy", "ut", "sl", "vl", "bl", "cto", "ot_ex", "ot", "nd", "nd_ot", "rd_reg", "rd_ot", "rd_nd", "rd_nd_ot", "sh_reg", "sh_ot", 
	"sh_nd", "sh_nd_ot", "lh_reg", "lh_ot", "lh_nd", "lh_nd_ot", "rd_sh_reg", "rd_sh_ot", "rd_sh_nd", "rd_sh_nd_ot", "rd_lh_reg", "rd_lh_ot", "rd_lh_nd", "rd_lh_nd_ot"]

	for fld in field_list:
		total_dict[fld] = 0.00

	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])
	register = get_register(filters, pay_from, pay_to)

	for reg in register:
		if reg.employee_id not in data_register:
			data_register.update({
				str(reg.employee_id): {
					"employee_id": str(reg.employee_id),
					"employee_name": cstr(reg.full_name),
					"location": str(reg.location),
					#Ordinary
					"reg_hrs": 0.00,
					"absent": 0.00,
					"tardy": 0.00,
					"ut": 0.00,
					"sl": 0.00,
					"vl": 0.00,
					"bl": 0.00,
					"cto": 0.00,
					"ot_ex": 0.00,
					"ot": 0.00,
					"nd": 0.00,
					"nd_ot": 0.00,
					#Rest Day
					"rd_reg": 0.00,
					"rd_ot": 0.00,
					"rd_nd": 0.00,
					"rd_nd_ot": 0.00,
					#Special Holiday
					"sh_reg": 0.00,
					"sh_ot": 0.00,
					"sh_nd": 0.00,
					"sh_nd_ot": 0.00,
					#Legal Holiday
					"lh_reg": 0.00,
					"lh_ot": 0.00,
					"lh_nd": 0.00,
					"lh_nd_ot": 0.00,
					#Rest Day & Special Holiday
					"rd_sh_reg": 0.00,
					"rd_sh_ot": 0.00,
					"rd_sh_nd": 0.00,
					"rd_sh_nd_ot": 0.00,
					#Rest Day & Legal Holiday
					"rd_lh_reg": 0.00,
					"rd_lh_ot": 0.00,
					"rd_lh_nd": 0.00,
					"rd_lh_nd_ot": 0.00,
					#Totals
					"tot_sl": 0.00,
					"tot_vl": 0.00,
					"tot_bl": 0.00,
					"emp_total": 0.00
				}
			})

		#Ordinary
		if reg.work_hours > 0 and reg.is_restday < 1 and reg.is_sp_holiday < 1 and reg.is_holiday < 1: 
			data_register[reg.employee_id]["reg_hrs"] += reg.work
		if reg.is_absent > 0 or reg.is_lwop > 0 and reg.lv_status > 1 or reg.is_halfday > 0:
			if reg.work > 0 and reg.lv_status > 1 or reg.is_halfday > 0:
				data_register[reg.employee_id]["absent"] += reg.work_hours - reg.work
			else:
				data_register[reg.employee_id]["absent"] += reg.work_hours
		if reg.late > 0:
			data_register[reg.employee_id]["tardy"] += reg.late
		if reg.undertime > 0:
			data_register[reg.employee_id]["ut"] += reg.undertime
		if "Sick Leave" in reg.leave_name and reg.lv_status > 0:
			lv = frappe.db.get_value("Leave Application", reg.linked_leave, "total_leave_days")
			data_register[reg.employee_id]["sl"] += flt(reg.work_hours, 2) * flt(lv, 2)
		if "Vacation Leave" in reg.leave_name and reg.lv_status > 0:
			lv = frappe.db.get_value("Leave Application", reg.linked_leave, "total_leave_days")
			data_register[reg.employee_id]["vl"] += flt(reg.work_hours, 2) * flt(lv, 2)
		if "Birthday Leave" in reg.leave_name and reg.lv_status > 0:
			lv = frappe.db.get_value("Leave Application", reg.linked_leave, "total_leave_days")
			data_register[reg.employee_id]["bl"] += flt(reg.work_hours, 2) * flt(lv, 2)
		if reg.cto > 0:
			data_register[reg.employee_id]["cto"] += reg.cto
		if reg.overtime_ex > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
			data_register[reg.employee_id]["ot_ex"] += reg.overtime_ex
		if reg.overtime > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
			data_register[reg.employee_id]["ot"] += reg.overtime
		if reg.nightdiff > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
			data_register[reg.employee_id]["nd"] += reg.nightdiff
		if reg.overtime_nd > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
			data_register[reg.employee_id]["nd_ot"] += reg.overtime_nd
		#Rest Day
		if reg.is_restday > 0 and reg.overtime > 0:
			data_register[reg.employee_id]["rd_reg"] += reg.overtime
		if reg.is_restday > 0 and reg.overtime_ex > 0:
			data_register[reg.employee_id]["rd_ot"] += reg.overtime_ex
		if reg.is_restday > 0 and reg.nightdiff > 0:
			data_register[reg.employee_id]["rd_nd"] += reg.nightdiff
		if reg.is_restday > 0 and reg.overtime_nd > 0:
			data_register[reg.employee_id]["rd_nd_ot"] += reg.overtime_nd
		#Special Holiday
		if reg.is_sp_holiday > 0 and reg.overtime > 0:
			data_register[reg.employee_id]["sh_reg"] += reg.overtime
		if reg.is_sp_holiday > 0 and reg.overtime_ex > 0:
			data_register[reg.employee_id]["sh_ot"] += reg.overtime_ex
		if reg.is_sp_holiday > 0 and reg.nightdiff > 0:
			data_register[reg.employee_id]["sh_nd"] += reg.nightdiff
		if reg.is_sp_holiday > 0 and reg.overtime_nd > 0:
			data_register[reg.employee_id]["sh_nd_ot"] += reg.overtime_nd
		#Legal Holiday
		if reg.is_holiday > 0 and reg.overtime > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["lh_reg"] += reg.overtime
		if reg.is_holiday > 0 and reg.overtime_ex > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["lh_ot"] += reg.overtime_ex
		if reg.is_holiday > 0 and reg.nightdiff > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["lh_nd"] += reg.nightdiff
		if reg.is_holiday > 0 and reg.overtime_nd > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["lh_nd_ot"] += reg.overtime_nd
		#Rest Day & Special Holiday
		if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.overtime > 0:
			data_register[reg.employee_id]["rd_sh_reg"] += reg.overtime
		if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.overtime_ex > 0:
			data_register[reg.employee_id]["rd_sh_ot"] += reg.overtime_ex
		if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.nightdiff > 0:
			data_register[reg.employee_id]["rd_sh_nd"] += reg.nightdiff
		if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.overtime_nd > 0:
			data_register[reg.employee_id]["rd_sh_nd_ot"] += reg.overtime_nd
		#Rest Day & Legal Holiday
		if reg.is_holiday > 0 and reg.is_restday > 0 and reg.overtime > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["rd_lh_reg"] += reg.overtime
		if reg.is_holiday > 0 and reg.is_restday > 0 and reg.overtime_ex > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["rd_lh_ot"] += reg.overtime_ex
		if reg.is_holiday > 0 and reg.is_restday > 0 and reg.nightdiff > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["rd_lh_nd"] += reg.nightdiff
		if reg.is_holiday > 0 and reg.is_restday > 0 and reg.overtime_nd > 0 and not reg.is_sp_holiday > 0:
			data_register[reg.employee_id]["rd_lh_nd_ot"] += reg.overtime_nd

		for f in field_list:
			data_register[reg.employee_id]["emp_total"] += flt(data_register[reg.employee_id][f], 8)
	
	head_count = 0
	for dr in data_register:
		row = {}
		if filters.hide_zero:
			if data_register[dr]["emp_total"] > 0:
				for col in columns:
					clm = col['fieldname']
					if clm in field_list:
						row[clm] = '{:,.2f}'.format( convert_hrs(filters ,flt(data_register[dr][clm], 8)) )
						total_dict[clm] += flt(data_register[dr][clm], 8)
					else:
						row[clm] = cstr(data_register[dr][clm])
		else:
			for col in columns:
				clm = col['fieldname']
				if clm in field_list:
					row[clm] = '{:,.2f}'.format( convert_hrs(filters ,flt(data_register[dr][clm], 8)) )
					total_dict[clm] += flt(data_register[dr][clm], 8)
				else:
					row[clm] = cstr(data_register[dr][clm])
		if row:
			head_count += 1
			data.append(row)	

	data_list = sorted(data, key=lambda k: k['employee_name'])

	if filters.show_total:
		total_row = {}
		headcount_list = {}

		for col in columns:
			clm = col['fieldname']
			total_row[clm] = ""
			headcount_list[clm] = ""
			if clm == 'location':
				total_row[clm] = 'Total'
				headcount_list[clm] = 'Head Count'
			if clm == 'reg_hrs':
				headcount_list[clm] = head_count

		for tl in total_dict:
			total_row[tl] = '{:,.2f}'.format( convert_hrs(filters ,flt(total_dict[tl], 8)) )
			
		data_list.append(total_row)
		data_list.append(headcount_list)

	return data_list

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("TE.`name`=%(employee)s")

	if filters.get("location"):
		conditions.append("TE.`location`=%(location)s")

	if filters.get("show_active"):
		conditions.append("TE.is_active=1")

	return "AND {}".format(" AND ".join(conditions)) if conditions else "" 

def convert_hrs(filters, hrs):
	con = 0
	if filters.time_options == "Mins":
		con = flt(hrs, 8) * 60
	else:
		con = flt(hrs, 8)

	return flt(con, 8)