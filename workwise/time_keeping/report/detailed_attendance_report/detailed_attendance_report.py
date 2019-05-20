# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):

	columns = get_columns(filters)
	results = get_result(filters)

	return columns, results

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "reg",
			"label": _("Work"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "abs",
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

def get_result(filters):
	data = get_data(filters)
	result = get_result_as_list(data, filters)

	return result

def get_result_as_list(data, filters):
	result = []
	for d in data:
		result.append(d)

	return result

def get_register(emp, pay_from, pay_to):
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
	pay_from, pay_to = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to"])
	employees = get_employees(filters)

	for emp in employees:
		reg_hrs = 0.00
		absent = 0.00
		tardy = 0.00
		ut = 0.00
		sl = 0.00
		vl = 0.00
		bl = 0.00
		cto = 0.00
		ot_ex = 0.00
		ot = 0.00
		nd = 0.00
		nd_ot = 0.00
		rd_reg = 0.00
		rd_ot = 0.00
		rd_nd = 0.00
		rd_nd_ot = 0.00
		sh_reg = 0.00
		sh_ot = 0.00
		sh_nd = 0.00
		sh_nd_ot = 0.00
		lh_reg = 0.00
		lh_ot = 0.00
		lh_nd = 0.00
		lh_nd_ot = 0.00
		rd_sh_reg = 0.00
		rd_sh_ot = 0.00
		rd_sh_nd = 0.00
		rd_sh_nd_ot = 0.00
		rd_lh_reg = 0.00
		rd_lh_ot = 0.00
		rd_lh_nd = 0.00
		rd_lh_nd_ot = 0.00

		tot_sl = 0.00
		tot_vl = 0.00
		tot_bl = 0.00

		register = get_register(emp.name, pay_from, pay_to)
		for reg in register:
			#Ordinary
			if reg.work_hours > 0 and reg.is_restday < 1 and reg.is_sp_holiday < 1 and reg.is_holiday < 1: 
				reg_hrs += reg.work
			if reg.is_absent > 0 or reg.is_lwop > 0 and reg.lv_status > 1 or reg.is_halfday > 0:
				if reg.work > 0 and reg.lv_status > 1 or reg.is_halfday > 0:
					absent += reg.work_hours - reg.work
				else:
					absent += reg.work_hours
			if reg.late > 0:
				tardy += reg.late
			if reg.undertime > 0:
				ut += reg.undertime
			if "Sick Leave" in reg.leave_name and reg.lv_status > 0:
				lv = frappe.db.get_value("Leave Application", reg.linked_leave, "total_leave_days")
				sl += flt(reg.work_hours, 2) * flt(lv, 2)
			if "Vacation Leave" in reg.leave_name and reg.lv_status > 0:
				lv = frappe.db.get_value("Leave Application", reg.linked_leave, "total_leave_days")
				vl += flt(reg.work_hours, 2) * flt(lv, 2)
			if "Birthday Leave" in reg.leave_name and reg.lv_status > 0:
				lv = frappe.db.get_value("Leave Application", reg.linked_leave, "total_leave_days")
				bl += flt(reg.work_hours, 2) * flt(lv, 2)
			if reg.cto > 0:
				cto += reg.cto
			if reg.overtime_ex > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
				ot_ex += reg.overtime_ex
			if reg.overtime > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
				ot += reg.overtime
			if reg.nightdiff > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
				nd += reg.nightdiff
			if reg.overtime_nd > 0 and not reg.is_restday > 0 and not reg.is_sp_holiday > 0  and not reg.is_holiday > 0:
				nd_ot += reg.overtime_nd
			#Rest Day
			if reg.is_restday > 0 and reg.overtime > 0:
				rd_reg += reg.overtime
			if reg.is_restday > 0 and reg.overtime_ex > 0:
				rd_ot += reg.overtime_ex
			if reg.is_restday > 0 and reg.nightdiff > 0:
				rd_nd += reg.nightdiff
			if reg.is_restday > 0 and reg.overtime_nd > 0:
				rd_nd_ot += reg.overtime_nd
			#Special Holiday
			if reg.is_sp_holiday > 0 and reg.overtime > 0:
				sh_reg += reg.overtime
			if reg.is_sp_holiday > 0 and reg.overtime_ex > 0:
				sh_ot += reg.overtime_ex
			if reg.is_sp_holiday > 0 and reg.nightdiff > 0:
				sh_nd += reg.nightdiff
			if reg.is_sp_holiday > 0 and reg.overtime_nd > 0:
				sh_nd_ot += reg.overtime_nd
			#Legal Holiday
			if reg.is_holiday > 0 and reg.overtime > 0 and not reg.is_sp_holiday > 0:
				lh_reg += reg.overtime
			if reg.is_holiday > 0 and reg.overtime_ex > 0 and not reg.is_sp_holiday > 0:
				lh_ot += reg.overtime_ex
			if reg.is_holiday > 0 and reg.nightdiff > 0 and not reg.is_sp_holiday > 0:
				lh_nd += reg.nightdiff
			if reg.is_holiday > 0 and reg.overtime_nd > 0 and not reg.is_sp_holiday > 0:
				lh_nd_ot += reg.overtime_nd
			#Rest Day & Special Holiday
			if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.overtime > 0:
				rd_sh_reg += reg.overtime
			if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.overtime_ex > 0:
				rd_sh_ot += reg.overtime_ex
			if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.nightdiff > 0:
				rd_sh_nd += reg.nightdiff
			if reg.is_restday > 0 and reg.is_sp_holiday > 0 and reg.overtime_nd > 0:
				rd_sh_nd_ot += reg.overtime_nd
			#Rest Day & Legal Holiday
			if reg.is_holiday > 0 and reg.is_restday > 0 and reg.overtime > 0 and not reg.is_sp_holiday > 0:
				rd_lh_reg += reg.overtime
			if reg.is_holiday > 0 and reg.is_restday > 0 and reg.overtime_ex > 0 and not reg.is_sp_holiday > 0:
				rd_lh_ot += reg.overtime_ex
			if reg.is_holiday > 0 and reg.is_restday > 0 and reg.nightdiff > 0 and not reg.is_sp_holiday > 0:
				rd_lh_nd += reg.nightdiff
			if reg.is_holiday > 0 and reg.is_restday > 0 and reg.overtime_nd > 0 and not reg.is_sp_holiday > 0:
				rd_lh_nd_ot += reg.overtime_nd

		emp_total = reg_hrs + absent + tardy + ut + sl + vl + bl + cto + ot_ex + ot + nd + nd_ot + rd_reg + rd_ot + rd_nd + rd_nd_ot + sh_reg + sh_ot + sh_nd + sh_nd_ot + lh_reg + lh_ot + lh_nd + lh_nd_ot + rd_sh_reg + rd_sh_ot + rd_sh_nd + rd_sh_nd_ot + rd_lh_reg + rd_lh_ot + rd_lh_nd + rd_lh_nd_ot
		if filters.hide_zero:
			if emp_total > 0:
				data.append({
					"employee_name": emp.full_name,
					"reg": '{:,.2f}'.format(convert_hrs(filters ,reg_hrs)),
					"abs": '{:,.2f}'.format(convert_hrs(filters ,absent)),
					"tardy": '{:,.2f}'.format(convert_hrs(filters ,tardy)),
					"ut": '{:,.2f}'.format(convert_hrs(filters ,ut)),
					"sl": '{:,.2f}'.format(convert_hrs(filters ,sl)),
					"vl": '{:,.2f}'.format(convert_hrs(filters ,vl)),
					"bl": '{:,.2f}'.format(convert_hrs(filters ,bl)),
					"cto": '{:,.2f}'.format(convert_hrs(filters ,cto)),
					"ot_ex": '{:,.2f}'.format(convert_hrs(filters ,ot_ex)),
					"ot": '{:,.2f}'.format(convert_hrs(filters ,ot)),
					"nd": '{:,.2f}'.format(convert_hrs(filters ,nd)),
					"nd_ot": '{:,.2f}'.format(convert_hrs(filters ,nd_ot)),
					"rd_reg": '{:,.2f}'.format(convert_hrs(filters ,rd_reg)),
					"rd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_ot)),
					"rd_nd": '{:,.2f}'.format(convert_hrs(filters ,rd_nd)),
					"rd_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_nd_ot)),
					"sh_reg": '{:,.2f}'.format(convert_hrs(filters ,sh_reg)),
					"sh_ot": '{:,.2f}'.format(convert_hrs(filters ,sh_ot)),
					"sh_nd": '{:,.2f}'.format(convert_hrs(filters ,sh_nd)),
					"sh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,sh_nd_ot)),
					"lh_reg": '{:,.2f}'.format(convert_hrs(filters ,lh_reg)),
					"lh_ot": '{:,.2f}'.format(convert_hrs(filters ,lh_ot)),
					"lh_nd": '{:,.2f}'.format(convert_hrs(filters ,lh_nd)),
					"lh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,lh_nd_ot)),
					"rd_sh_reg": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_reg)),
					"rd_sh_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_ot)),
					"rd_sh_nd": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_nd)),
					"rd_sh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_nd_ot)),
					"rd_lh_reg": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_reg)),
					"rd_lh_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_ot)),
					"rd_lh_nd": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_nd)),
					"rd_lh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_nd_ot))
				})
		else:
			data.append({
				"employee_name": emp.full_name,
				"reg": '{:,.2f}'.format(convert_hrs(filters ,reg_hrs)),
				"abs": '{:,.2f}'.format(convert_hrs(filters ,absent)),
				"tardy": '{:,.2f}'.format(convert_hrs(filters ,tardy)),
				"ut": '{:,.2f}'.format(convert_hrs(filters ,ut)),
				"sl": '{:,.2f}'.format(convert_hrs(filters ,sl)),
				"vl": '{:,.2f}'.format(convert_hrs(filters ,vl)),
				"bl": '{:,.2f}'.format(convert_hrs(filters ,bl)),
				"cto": '{:,.2f}'.format(convert_hrs(filters ,cto)),
				"ot_ex": '{:,.2f}'.format(convert_hrs(filters ,ot_ex)),
				"ot": '{:,.2f}'.format(convert_hrs(filters ,ot)),
				"nd": '{:,.2f}'.format(convert_hrs(filters ,nd)),
				"nd_ot": '{:,.2f}'.format(convert_hrs(filters ,nd_ot)),
				"rd_reg": '{:,.2f}'.format(convert_hrs(filters ,rd_reg)),
				"rd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_ot)),
				"rd_nd": '{:,.2f}'.format(convert_hrs(filters ,rd_nd)),
				"rd_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_nd_ot)),
				"sh_reg": '{:,.2f}'.format(convert_hrs(filters ,sh_reg)),
				"sh_ot": '{:,.2f}'.format(convert_hrs(filters ,sh_ot)),
				"sh_nd": '{:,.2f}'.format(convert_hrs(filters ,sh_nd)),
				"sh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,sh_nd_ot)),
				"lh_reg": '{:,.2f}'.format(convert_hrs(filters ,lh_reg)),
				"lh_ot": '{:,.2f}'.format(convert_hrs(filters ,lh_ot)),
				"lh_nd": '{:,.2f}'.format(convert_hrs(filters ,lh_nd)),
				"lh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,lh_nd_ot)),
				"rd_sh_reg": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_reg)),
				"rd_sh_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_ot)),
				"rd_sh_nd": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_nd)),
				"rd_sh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_sh_nd_ot)),
				"rd_lh_reg": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_reg)),
				"rd_lh_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_ot)),
				"rd_lh_nd": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_nd)),
				"rd_lh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,rd_lh_nd_ot))
			})
	if data:
		total_reg_hrs = 0
		total_absent = 0
		total_tardy = 0
		total_ut = 0
		total_sl = 0
		total_vl = 0
		total_bl = 0
		total_cto = 0
		total_ot_ex = 0
		total_ot = 0
		total_nd = 0
		total_nd_ot = 0
		total_rd_reg = 0
		total_rd_ot = 0
		total_rd_nd = 0
		total_rd_nd_ot = 0
		total_sh_reg = 0
		total_sh_ot = 0
		total_sh_nd = 0
		total_sh_nd_ot = 0
		total_lh_reg = 0
		total_lh_ot = 0
		total_lh_nd = 0
		total_lh_nd_ot = 0
		total_rd_sh_reg = 0
		total_rd_sh_ot = 0
		total_rd_sh_nd = 0
		total_rd_sh_nd_ot = 0
		total_rd_lh_reg = 0
		total_rd_lh_ot = 0
		total_rd_lh_nd = 0
		total_rd_lh_nd_ot= 0
		head_count = 0
		for d in data:
			total_reg_hrs += flt(d['reg'])
			total_absent += flt(d['abs'])
			total_tardy += flt(d['tardy'])
			total_ut += flt(d['ut'])
			total_sl += flt(d['sl'])
			total_vl += flt(d['vl'])
			total_bl += flt(d['bl'])
			total_cto += flt(d['cto'])
			total_ot_ex += flt(d['ot_ex'])
			total_ot += flt(d['ot'])
			total_nd += flt(d['nd'])
			total_nd_ot += flt(d['nd_ot'])
			total_rd_reg += flt(d['rd_reg'])
			total_rd_ot += flt(d['rd_ot'])
			total_rd_nd += flt(d['rd_nd'])
			total_rd_nd_ot += flt(d['rd_nd_ot'])
			total_sh_reg += flt(d['sh_reg'])
			total_sh_ot += flt(d['sh_ot'])
			total_sh_nd += flt(d['sh_nd'])
			total_sh_nd_ot += flt(d['sh_nd_ot'])
			total_lh_reg += flt(d['lh_reg'])
			total_lh_ot += flt(d['lh_ot'])
			total_lh_nd += flt(d['lh_nd'])
			total_lh_nd_ot += flt(d['lh_nd_ot'])
			total_rd_sh_reg += flt(d['rd_sh_reg'])
			total_rd_sh_ot += flt(d['rd_sh_ot'])
			total_rd_sh_nd += flt(d['rd_sh_nd'])
			total_rd_sh_nd_ot += flt(d['rd_sh_nd_ot'])
			total_rd_lh_reg += flt(d['rd_lh_reg'])
			total_rd_lh_ot += flt(d['rd_lh_ot'])
			total_rd_lh_nd += flt(d['rd_lh_nd'])
			total_rd_lh_nd_ot+= flt(d['rd_lh_nd_ot'])
			head_count += 1
		data.append({})
		data.append({
			"employee_name": 'Total',
			"reg": '{:,.2f}'.format(convert_hrs(filters ,total_reg_hrs)),
			"abs": '{:,.2f}'.format(convert_hrs(filters ,total_absent)),
			"tardy": '{:,.2f}'.format(convert_hrs(filters ,total_tardy)),
			"ut": '{:,.2f}'.format(convert_hrs(filters ,total_ut)),
			"sl": '{:,.2f}'.format(convert_hrs(filters ,total_sl)),
			"vl": '{:,.2f}'.format(convert_hrs(filters ,total_vl)),
			"bl": '{:,.2f}'.format(convert_hrs(filters ,total_bl)),
			"cto": '{:,.2f}'.format(convert_hrs(filters ,total_cto)),
			"ot_ex": '{:,.2f}'.format(convert_hrs(filters ,total_ot_ex)),
			"ot": '{:,.2f}'.format(convert_hrs(filters ,total_ot)),
			"nd": '{:,.2f}'.format(convert_hrs(filters ,total_nd)),
			"nd_ot": '{:,.2f}'.format(convert_hrs(filters ,total_nd_ot)),
			"rd_reg": '{:,.2f}'.format(convert_hrs(filters ,total_rd_reg)),
			"rd_ot": '{:,.2f}'.format(convert_hrs(filters ,total_rd_ot)),
			"rd_nd": '{:,.2f}'.format(convert_hrs(filters ,total_rd_nd)),
			"rd_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,total_rd_nd_ot)),
			"sh_reg": '{:,.2f}'.format(convert_hrs(filters ,total_sh_reg)),
			"sh_ot": '{:,.2f}'.format(convert_hrs(filters ,total_sh_ot)),
			"sh_nd": '{:,.2f}'.format(convert_hrs(filters ,total_sh_nd)),
			"sh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,total_sh_nd_ot)),
			"lh_reg": '{:,.2f}'.format(convert_hrs(filters ,total_lh_reg)),
			"lh_ot": '{:,.2f}'.format(convert_hrs(filters ,total_lh_ot)),
			"lh_nd": '{:,.2f}'.format(convert_hrs(filters ,total_lh_nd)),
			"lh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,total_lh_nd_ot)),
			"rd_sh_reg": '{:,.2f}'.format(convert_hrs(filters ,total_rd_sh_reg)),
			"rd_sh_ot": '{:,.2f}'.format(convert_hrs(filters ,total_rd_sh_ot)),
			"rd_sh_nd": '{:,.2f}'.format(convert_hrs(filters ,total_rd_sh_nd)),
			"rd_sh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,total_rd_sh_nd_ot)),
			"rd_lh_reg": '{:,.2f}'.format(convert_hrs(filters ,total_rd_lh_reg)),
			"rd_lh_ot": '{:,.2f}'.format(convert_hrs(filters ,total_rd_lh_ot)),
			"rd_lh_nd": '{:,.2f}'.format(convert_hrs(filters ,total_rd_lh_nd)),
			"rd_lh_nd_ot": '{:,.2f}'.format(convert_hrs(filters ,total_rd_lh_nd_ot))
		})
		data.append({
			"employee_name": 'Head Count',
			"reg": head_count
		})
	return data

def get_employees(filters):
	register = frappe.db.sql("""SELECT DISTINCT `name`, full_name FROM `tabEmployee` 
		WHERE company = %(company)s {conditions}""".format(conditions=get_conditions(filters)), filters, as_dict=1)

	return register

def get_conditions(filters):
	conditions = []
	if filters.get("employee"):
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else "" 

def convert_hrs(filters, hrs):
	con = 0
	if filters.time_options == "Mins":
		con = flt(hrs, 8) * 60
	else:
		con = flt(hrs, 8)

	return flt(con, 8)