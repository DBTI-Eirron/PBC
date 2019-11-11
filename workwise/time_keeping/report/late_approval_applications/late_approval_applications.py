# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from datetime import date
from frappe import _
from frappe.utils import getdate, cstr, flt

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "application",
			"label": _("Application"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "approved_on",
			"label": _("Approved On"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "approved_by",
			"label": _("Approved By"),
			"fieldtype": "Data",
			"width": 240
		},
		{
			"fieldname": "link",
			"label": _("Link"),
			"fieldtype": "Data",
			"width": 180
		},
	]

	return columns

def get_data(filters):
	data = []
	lv_included_list = []
	ob_included_list = []
	ot_included_list = []
	ut_included_list = []
	cto_included_list = []
	et_included_list = []
	csa_included_list = []
	dtr_included_list = []

	pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", filters.payroll_period, ["attendance_from", "attendance_to", "approval_cutoff"])

	leaves = frappe.db.sql("""SELECT L.`name`, L.employee, L.leave_type, LA.leave_date, TE.full_name, L.approved_on, L.approved_by,
		LA.is_half_day, LA.is_second_half, LA.is_holiday, LA.is_excluded, L.is_lwop
		FROM `tabLeave Application Table` LA
		INNER JOIN `tabLeave Application` L ON L.`name` = LA.parent
		INNER JOIN `tabEmployee` TE ON L.employee = TE.`name`
		WHERE L.`company` = %s AND LA.leave_date >= %s AND LA.leave_date <= %s AND L.docstatus = '1' AND L.workflow_state = 'Approved'
		AND L.approved_on > %s ORDER BY TE.full_name, LA.leave_date ASC """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	ob_apps = frappe.db.sql("""SELECT OBA.`name`, OBA.employee, OBAT.target_date, OBAT.date, OBAT.to_date, TE.full_name,
		OBAT.from_time, OBAT.to_time, OBAT.hrs, OBAT.is_holiday, OBAT.is_excluded, OBA.approved_on, OBA.approved_by
		FROM `tabOfficial Business Application Table` OBAT
		INNER JOIN `tabOfficial Business Application` OBA  ON OBAT.parent = OBA.`name`
		INNER JOIN `tabEmployee` TE ON OBA.employee = TE.`name`
		WHERE OBA.`company` = %s AND OBA.workflow_state = 'Approved' AND OBAT.target_date >= %s 
		AND OBAT.target_date <= %s AND OBAT.is_excluded = 0 AND OBA.approved_on > %s ORDER BY TE.full_name """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	overtimes = frappe.db.sql("""SELECT OT.`name`, OT.employee, OT.total_hrs, OT.break_hrs, OT.target_date, OT.from_date, TE.full_name,
		OT.to_date, OT.from_time, OT.to_time, OT.approved_on, OT.approved_by FROM `tabOvertime Application` OT
		INNER JOIN `tabEmployee` TE ON OT.employee = TE.`name`
		WHERE OT.`company` = %s AND OT.workflow_state = 'Approved' AND OT.target_date >= %s 
		AND OT.target_date <= %s AND OT.approved_on > %s ORDER BY TE.full_name """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	undertimes = frappe.db.sql("""SELECT UT.`name`, UT.employee, UT.from_time, UT.to_time, UT.from_date, TE.full_name, UT.approved_on, UT.approved_by
		FROM `tabUndertime Application` UT
		INNER JOIN `tabEmployee` TE ON UT.employee = TE.`name` WHERE UT.workflow_state = 'Approved' AND UT.`company` = %s
		AND UT.from_date >= %s AND UT.from_date <= %s AND UT.approved_on > %s ORDER BY TE.full_name """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	compensatory = frappe.db.sql("""SELECT CTO.`name`, CTO.employee, CTO.use_total_hours, CTO.use_date, TE.full_name, CTO.approved_on, CTO.approved_by 
		FROM `tabCompensatory Time Off` CTO INNER JOIN `tabEmployee` TE ON CTO.employee = TE.`name`
		WHERE CTO.`company` = %s AND CTO.workflow_state = 'Approved' AND CTO.use_date >= %s AND CTO.use_date <= %s AND CTO.`type` = 'Use' 
		AND CTO.approved_on > %s ORDER BY TE.full_name """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	ex_tardiness = frappe.db.sql("""SELECT ET.`name`, ET.employee, ET.`date`, ET.from_time, ET.to_time, ET.`type`, 
		ET.approved_on, ET.approved_by, TE.full_name FROM `tabExcuse Tardiness Application` ET
		INNER JOIN `tabEmployee` TE ON ET.employee = TE.`name` WHERE ET.workflow_state = 'Approved' AND ET.`company` = %s
		AND ET.`date` >= %s AND ET.`date` <= %s AND ET.approved_on > %s ORDER BY TE.full_name """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	cs_apps = frappe.db.sql(""" SELECT CSA.`name`, CSA.employee, CSA.approved_on, CSAT.target_date, CSAT.new_shift, TE.full_name, CSA.approved_on, CSA.approved_by
		FROM `tabChange Schedule Application` CSA INNER JOIN `tabChange Schedule Application Table` CSAT ON CSAT.parent = CSA.`name` 
		INNER JOIN `tabEmployee` TE ON CSA.employee = TE.`name` WHERE CSA.`company` = %s AND CSA.docstatus = 1 AND CSA.workflow_state = 'Approved' AND CSAT.target_date >= %s 
		AND CSAT.target_date <= %s AND CSA.approved_on > %s ORDER BY TE.full_name """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	dtr_apps = frappe.db.sql(""" SELECT DA.`name`, DA.`employee`, TIMESTAMP(DA.`target_date`, DT.`request`) as card_datetime, 
		DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`, TE.full_name, DA.approved_on, DA.approved_by
		FROM `tabDTR Problem Table` DT INNER JOIN `tabDTR Problem Application` DA ON DT.`parent`=DA.`name` 
		INNER JOIN `tabEmployee` TE ON DA.employee = TE.`name`
		WHERE DA.`company` = %s AND DA.`workflow_state` = 'Approved' AND DA.`target_date` >= %s AND DA.`target_date` <= %s AND DA.approved_on > %s
		ORDER BY TE.full_name, card_datetime """,(filters.company, pay_from, pay_to, getdate(approval_cutoff)), as_dict=1)

	data_entry = {
		"leave_application": {},
		"overtime_application": {},
		"official_business_application": {},
		"undertime_application": {},
		"compesnatory_time_off": {},
		"excuse_tardiness": {},
		"change_schedule_application": {},
		"dtrp_application": {},
	}

	for lv in leaves:
		if lv.name not in lv_included_list:
			row = {
				"employee_name": lv.full_name,
				"application": "Leave Application",
				"approved_on": lv.approved_on,
				"approved_by": lv.approved_by,
				"link": "<a href='/desk#Form/Leave Application/"+lv.name+"'> "+lv.name+" </a>",
			}
			lv_included_list.append(lv.name)
			data.append(row)

	for ob in ob_apps:
		if ob.name not in ob_included_list:
			row = {
				"employee_name": ob.full_name,
				"application": "Official Business Application",
				"approved_on": ob.approved_on,
				"approved_by": ob.approved_by,
				"link": "<a href='/desk#Form/Official Business Application/"+ob.name+"'> "+ob.name+" </a>",
			}
			ob_included_list.append(ob.name)
			data.append(row)

	for ot in overtimes:
		if ot.name not in ot_included_list:
			row = {
				"employee_name": ot.full_name,
				"application": "Overtime Application",
				"approved_on": ot.approved_on,
				"approved_by": ot.approved_by,
				"link": "<a href='/desk#Form/Overtime Application/"+ot.name+"'> "+ot.name+" </a>",
			}
			ot_included_list.append(ot.name)
			data.append(row)

	for ut in undertimes:
		if ut.name not in ut_included_list:
			row = {
				"employee_name": ut.full_name,
				"application": "Undertime Application",
				"approved_on": ut.approved_on,
				"approved_by": ut.approved_by,
				"link": "<a href='/desk#Form/Undertime Application/"+ut.name+"'> "+ut.name+" </a>",
			}
			ut_included_list.append(ut.name)
			data.append(row)

	for cto in compensatory:
		if cto.name not in cto_included_list:
			row = {
				"employee_name": cto.full_name,
				"application": "Compensatory Time Off",
				"approved_on": cto.approved_on,
				"approved_by": cto.approved_by,
				"link": "<a href='/desk#Form/Compensatory Time Off/"+cto.name+"'> "+cto.name+" </a>",
			}
			cto_included_list.append(cto.name)
			data.append(row)

	for et in ex_tardiness:
		if et.name not in et_included_list:
			row = {
				"employee_name": et.full_name,
				"application": "Excuse Tardiness Application",
				"approved_on": et.approved_on,
				"approved_by": et.approved_by,
				"link": "<a href='/desk#Form/Excuse Tardiness Application/"+et.name+"'> "+et.name+" </a>",
			}
			et_included_list.append(et.name)
			data.append(row)

	for csa in cs_apps:
		if csa.name not in csa_included_list:
			row = {
				"employee_name": csa.full_name,
				"application": "Change Schedule Application",
				"approved_on": csa.approved_on,
				"approved_by": csa.approved_by,
				"link": "<a href='/desk#Form/Change Schedule Application/"+csa.name+"'> "+csa.name+" </a>",
			}
			csa_included_list.append(csa.name)
			data.append(row)

	for dtr in dtr_apps:
		if dtr.name not in dtr_included_list:
			row = {
				"employee_name": dtr.full_name,
				"application": "DTR Problem Application",
				"approved_on": dtr.approved_on,
				"approved_by": dtr.approved_by,
				"link": "<a href='/desk#Form/DTR Problem Application/"+dtr.name+"'> "+dtr.name+" </a>",
			}
			dtr_included_list.append(dtr.name)
			data.append(row)

	return data
