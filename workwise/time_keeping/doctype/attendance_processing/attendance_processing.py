# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date, nowtime, nowdate
from workwise.time_keeping.timekeeping_utils import add_date, db_datetime_str
from workwise.time_keeping.application_utils import validate_inactive_employee
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_schedule, get_holiday_list, get_leave_list, get_shift_map, get_card_within, 
get_attendance, get_defaults, get_ob_list, get_ot_list, get_ut_list, get_ext_list, get_cto_list, get_sorted_card, get_wss_list, insert_overtime,
init_employee_map,complete_sched,change_sched,get_template_map)
from workwise.time_keeping.application_utils import get_user_fullname

class AttendanceProcessing(Document):
	def get_employees(self):
		employees = frappe.db.sql("""SELECT TE.`name`, TE.full_name, TE.biometrics_id, TE.company, TE.location, TE.is_attendance_base, 
			TE.no_hours, TE.rate_type, TE.default_schedule, TE.department, DEPT.`lft`, TE.cost_center
			FROM `tabEmployee` TE
			LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
			WHERE TE.company = %(company)s 
			AND TE.payroll_schedule = %(schedule)s {conditions}
			AND TE.is_active = 1 ORDER BY TE.`full_name` """.format(conditions=self.get_employee_conditions()),{ 
				"company": self.company,
				"employee": self.employee,
				"schedule": self.schedule,
				"department": self.department,
				"location": self.location,
				"period_group": self.period_group,
			}, as_dict=True)

		return employees

	def get_employee_conditions(self):
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		conditions = []
		if self.employee:
			conditions.append("TE.`name`=%(employee)s")
		
		if self.department:
			lft, rgt = frappe.db.get_value("Department", self.department, ["lft", "rgt"])
			conditions.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))
		
		if self.location:
			conditions.append("TE.location=%(location)s")

		if strict_period_group:
			conditions.append("TE.period_group=%(period_group)s")

		return "AND {}".format(" AND ".join(conditions)) if conditions else ""

	def validate_period(self):
		strict_period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		company, period_stats = frappe.db.get_value("Payroll Period", self.period, ["company", "status"])

		if not self.period:
			frappe.throw(_("Please Select Payroll Period"))

		if company != self.company:
			frappe.throw(_("Selected Period does not belong to company"))

		if period_stats == "Closed":
			frappe.throw(_("Selected Period is Already Closed"))
		
		if strict_period_group and not self.period_group:
			frappe.throw(_("Period Group is required for Payroll Period {0}").format(self.period))

	def process_attendance(self):
		if self.employee:
			validate_inactive_employee(self)
		self.validate_period()

		employees = self.get_employees()
		ss_list = 0

		if employees:
			pay_from, pay_to, approval_cutoff = frappe.db.get_value("Payroll Period", self.period, ["attendance_from", "attendance_to", "approval_cutoff"])
			employee_list = self.convert_to_list(employees)
			data = []
			ot_list = []
			reg_list = []
			employee_log_list = ""
			headcount, no_sched_count, no_work_count = 0, 0, 0 
			time_start = nowtime()

			if self.employee:
				employee = self.employee
			else:
				employee = None

			frappe.db.sql("""DELETE FROM `tabAttendance Register` WHERE target_date >= %s AND target_date <= %s and employee IN %s """,(pay_from, pay_to,employee_list), as_dict=1)
			frappe.db.sql("""DELETE FROM `tabOvertime` WHERE target_date >= %s AND target_date <= %s AND employee IN %s """,(pay_from, pay_to,employee_list), as_dict=1)
			template_map = get_template_map()
			shift_map = get_shift_map()
			emp_map = init_employee_map(employees, employee, self.company, pay_from, pay_to, approval_cutoff, 0)
			for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
				ss_list += 1
				issue_tag = ""
				no_work = 1
				complete_sched(emp_dict, pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1), template_map)
				change_sched(emp_dict, emp_dict['schedules'], emp_dict.get('csa'))
				for sched in emp_dict['schedules']:
					if sched['target_date'] not in [pay_from - datetime.timedelta(days=1), pay_to + datetime.timedelta(days=1)]:
						entry = get_defaults(emp_dict.get('employee_details'), sched, shift_map, emp_dict.get('overrides'))
						cards_in, cards_out = get_card_within(sched['target_date'], emp_dict['timelogs_map'], emp_dict['schedules'], shift_map, entry.get('pre_shift'), entry.get('end_preshift'), 
							entry.get('post_shift'), entry.get('end_postshift'), emp_dict.get('timecards'), emp_dict.get('dtrp'), emp_dict.get('tla'))
						get_sorted_card(entry, cards_in, cards_out, emp_dict['timelogs_map'])
						get_attendance(entry, emp_dict.get('overrides'),emp_dict.get('lvs'), emp_dict.get('hls'), emp_dict.get('obs'), 
							emp_dict.get('ots'), emp_dict.get('uts'), emp_dict.get('ext'), emp_dict.get('cto'), emp_dict.get('wss'), emp_dict.get('dtrp'), emp_dict.get('tla'))
						
						entry['break'] = self.convert_secs(entry['break'])
						entry['work'] = self.convert_secs(entry['work'])
						entry['late'] = self.convert_secs(entry['late'])
						entry['undertime'] = self.convert_secs(entry['undertime'])
						entry['overtime'] = self.convert_secs(entry['overtime'])
						entry['overtime_nd'] = self.convert_secs(entry['overtime_nd'])
						entry['overtime_ex'] = self.convert_secs(entry['overtime_ex'])
						entry['nightdiff'] = self.convert_secs(entry['nightdiff'])
						entry['earlynightdiff'] = self.convert_secs(entry['earlynightdiff'])
						entry['latenightdiff'] = self.convert_secs(entry['latenightdiff'])
						entry['cto'] = self.convert_secs(entry['cto'])
						entry['ot_early_nd'] = self.convert_secs(entry['ot_early_nd'])
						entry['ot_late_nd'] = self.convert_secs(entry['ot_late_nd'])
						ot_list.extend(entry.get('ot_list'))
						insert_overtime(entry)
						reg_list.append(entry)

						#Get Processing Logs
						if no_work == 1:
							if entry['work'] > 0:
								no_work = 0
							if entry['cto'] > 0:
								no_work = 0
							if not entry['is_restday'] and not entry['is_holiday']:
								if entry['is_absent'] == 0 and entry['is_lwop'] == 0:
									no_work = 0

				if not emp_dict['schedules']:
					issue_tag += " <span class='label label-danger'> No Schedule </span>"
					no_sched_count += 1
				if no_work == 1:
					issue_tag += " <span class='label label-danger'> No Work </span>"
					no_work_count += 1
				employee_log_list += cstr(emp_dict['employee'])+" : "+cstr(emp_dict['employee_name'])+" "+issue_tag+"<br>"
				headcount += 1
			processing_logs = frappe.new_doc("Attendance Processing Logs")
			processing_logs.update({
				"company": self.company,
				"payroll_period": self.period,
				"period_from": self.period_from,
				"period_to": self.period_to,
				"processed_date": getdate(nowdate()),
				"processed_by": frappe.session.user,
				"processed_by_name": get_user_fullname(self),
				"processed_time_start": time_start,
				"processed_time_end": nowtime(),
				"headcount": headcount,
				"no_work": no_work_count,
				"no_schedule": no_sched_count,
				"employee_list": employee_log_list,
			})
			processing_logs.flags.ignore_permissions = True
			processing_logs.save()
				#payslip_label = "Created for "+ cstr(emp_dict.get('employee_name')) +""

			for ot in ot_list:
				otdoc = frappe.new_doc("Overtime")
				otdoc.update({
					"employee": ot.get('employee'),
					"target_date": ot.get('target_date'),
					"ot_code": ot.get('ot_code'),	
					"hrs": ot.get('ot_hrs'),
					"early_nd": ot.get('early_nd'),
					"late_nd": ot.get('late_nd'),
					"linked_ot": ot.get('linked_ot'),
				})
				otdoc.flags.ignore_mandatory = True
				otdoc.flags.ignore_permissions = True
				otdoc.insert()

			for reg in reg_list:
				row = {
					'employee': reg['employee'],
					'employee_name': frappe.db.get_value("Employee", reg['employee'], ["full_name"]),
					'cost_center': reg['cost_center'],
					'target_date': reg['target_date'],
					'work_shift': reg['work_shift'],
					'work_hours': reg['work_hours'],
					'work': reg['work'],
					'break': reg['break'],
					'late': reg['late'],
					'overtime': reg['overtime'],
					'overtime_nd': reg['overtime_nd'],
					'overtime_ex': reg['overtime_ex'],
					'nightdiff': reg['nightdiff'],
					'earlynightdiff': reg['earlynightdiff'],
					'latenightdiff': reg['latenightdiff'],
					'undertime': reg['undertime'],
					'cto': reg['cto'],
					'linked_leave': reg['linked_leave'],
					'leave_name': reg['leave_name'],
					'linked_overtime': "",
					'linked_ob': reg['linked_ob'],
					'linked_holiday': reg['linked_holiday'],
					'is_leave': reg['is_leave'],
					'lv_status': reg['lv_status'],
					'is_halfday': reg['is_halfday'],
					'is_ob': reg['is_ob'],
					'is_absent': reg['is_absent'],
					'is_flexible': reg['is_flexible'],
					'is_restday': reg['is_restday'],
					'is_holiday': reg['is_holiday'],
					'is_lwop': reg['is_lwop'],
					'is_sp_holiday': reg['is_sp_holiday'],
					'is_db_holiday': reg['is_db_holiday'],
					'is_default_schedule': reg['is_default_schedule'],
					'is_change_schedule': reg['is_change_schedule'],
					'has_issue': "",
					'ot_early_nd': reg['ot_early_nd'],
					'ot_late_nd': reg['ot_late_nd'],
					'card_in': reg['card_in'],
					'card_out': reg['card_out'],
					'tags': reg['tags'],
					'links': reg['links'],
				}

				register = frappe.new_doc("Attendance Register")
				register.update(row)
				register.flags.ignore_mandatory = True
				register.flags.ignore_permissions = True
				register.insert()
		else:
			frappe.throw(_("No Employee Found"))
		
		return self.create_log(ss_list, headcount, no_sched_count, no_work_count)

	def create_log(self, ss_list, headcount, no_sched_count, no_work_count):
		log = "<p>" + _("No Employee for the above selected criteria Attendance or Already Created") + "</p>"
		#if ss_list:
			#log = "<b>" + _("Attendance Registers Created") + "</b>\
			#<br><br>%s" % '<br>'.join(ss_list)
		if ss_list:
			log = "<p>" + _("Attendance Processed Successfully 	<br>\
				Headcount: "+cstr(headcount)+"/"+cstr(headcount)+" No Work: "+cstr(no_work_count)+" No Schedule: "+cstr(no_sched_count)+" <br>\
				Attendance Processing Log Created") + "</p>"

		return log

	def format_as_links(self, ss_list):
		return ['<a href="#Form/Attendance Register/{0}">{0}</a>'.format(s) for s in ss_list]

	def convert_secs(self, secs):
		# Converts to HR
		con = (secs / 60) / 60
		return con

	def convert_to_list(self, dic):
		data = []
		for d in dic:
			data.append(d.name)
		return data