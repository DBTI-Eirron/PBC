# Copyright (c) 2013, OSI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate, cint, flt, getdate, cstr, get_datetime
from frappe import _
from datetime import datetime
from workwise.time_keeping.attendance_utils import get_template_map, get_shift_map

def execute(filters=None):
	present, absent, late, leave = process_data(filters)
	columns = get_columns(filters)
	data = get_data(present,absent,late,leave)
	chart = get_chart(filters,present,absent,late,leave)
	return columns,data, None, chart

def get_chart(filters,present,absent,late,leave):
	datasets = []
	labels = ['Present','Absent','Late','Leave']
	values = [len(present),len(absent),len(late),len(leave)]
	datasets.append({'title':'Employee', 'values': values})
	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}
	chart["title"] = filters.company
	chart["type"] = "pie"
	chart["colors"] = ['green', 'blue', 'orange']

	return chart

def get_data(present,absent,late,leave):
	data = []
	data.append({"employee":"<b>PRESENT</b>"})
	for p in present:
		data.append({"employee":p['name'],"full_name":p['full_name']})
	data.append({})
	data.append({"employee":"<b>ABSENT</b>"})
	for a in absent:
		data.append({"employee":a['name'],"full_name":a['full_name']})
	data.append({})
	data.append({"employee":"<b>LATE</b>"})
	for lt in late:
		data.append({"employee":lt['name'],"full_name":lt['full_name']})
	data.append({})
	data.append({"employee":"<b>LEAVE</b>"})
	for lv in leave:
		data.append({"employee":lv['name'],"full_name":lv['full_name']})	
	return data

def get_columns(filters):
	columns = [
		{
			"fieldname": "employee",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"width": 150,
			"options": "Employee"
		},
		{
			"fieldname": "full_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 190,
		},
	]
	return columns
def process_data(filters):
	present = []
	absent = []
	late = []
	leave = []
	employee = dict_employees(filters)
	dict_card = dict_time_cards(filters)
	dict_sched = dict_work_sched(filters)
	list_leave = get_leave_application(filters)
	dict_def = get_template_map()
	dict_shift = get_shift_map()

	for emp in employee:
		if emp.biometrics_id in dict_card:
			if emp.name in dict_sched:
				work_shift = str(dict_sched[emp]['work_shift'])
				if dict_shift[work_shift]['is_restday']	== 0:
					if dict_card[emp.biometrics_id]['card_datetime'] <= get_datetime(str(nowdate())+" "+ str(dict_shift[work_shift]['time_in'])):
						present.append({"name":emp.name,"full_name":emp.full_name,"biometrics_id":emp.biometrics_id})
					else:
						late.append({"name":emp.name,"full_name":emp.full_name,"biometrics_id":emp.biometrics_id})
			else:
				if emp.default_schedule:
					work_shift = dict_def[emp.default_schedule][str(getdate(nowdate()).weekday())]
					if dict_shift[work_shift]['is_restday']	== 0:
						if dict_card[emp.biometrics_id]['card_datetime'] <= get_datetime(str(nowdate())+" "+ str(dict_shift[work_shift]['time_in'])):
							present.append({"name":emp.name,"full_name":emp.full_name,"biometrics_id":emp.biometrics_id})
						else:
							late.append({"name":emp.name,"full_name":emp.full_name,"biometrics_id":emp.biometrics_id})
					else:
						absent.append({"name":emp.name,"full_name":emp.full_name,"biometrics_id":emp.biometrics_id})
		else:
			if emp.name in list_leave:
				leave.append({"name":emp.name,"full_name":emp.full_name,"biometrics_id":emp.biometrics_id})
			else:
				absent.append({"name":emp.name,"full_name":emp.full_name,"biometrics_id":emp.biometrics_id})
	return present, absent, late, leave

def dict_employees(filters):
	employees = frappe.db.sql("""SELECT `name`, full_name, biometrics_id, default_schedule FROM `tabEmployee` WHERE company = %s""",(filters.company),as_dict=True)
	return employees

def dict_time_cards(filters):
	time_cards = frappe.db.sql("""SELECT `name`, biometrics_id, TIMESTAMP(date, time) as card_datetime FROM `tabTime Card` WHERE is_disabled = 0 AND `date` = %s AND card_type = 0 ORDER BY `time` ASC""",(nowdate()),as_dict=True)
	dict_card = {}
	for tc in time_cards:
		if tc.biometrics_id not in dict_card:
			dict_card.setdefault(tc.biometrics_id,frappe._dict({"name":tc.name,"card_type":tc.card_type,"card_datetime":tc.card_datetime}))
	return dict_card

def dict_work_sched(filters):
	work_sched = frappe.db.sql("""SELECT `name`, employee, work_shift FROM `tabWork Schedule` WHERE company = %s AND `target_date` = %s""",(filters.company,nowdate()),as_dict=True)
	dict_sched = {}
	for ws in work_sched:
		if ws.employee not in dict_sched:
			dict_sched.setdefault(ws.employee,frappe._dict({"name":ws.name,"work_shift":ws.work_shift}))
	return dict_sched

def get_leave_application(filters):
	leave_application = frappe.db.sql("""SELECT LA.employee FROM `tabLeave Application` LA INNER JOIN `tabLeave Application Table` LAT ON LA.`name` = LAT.parent WHERE LAT.leave_date = %s""",(nowdate(),),as_dict=True)
	list_leave = []
	for la in leave_application:
		list_leave.append(la.employee)
		
	return list_leave