from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money, now_datetime, add_to_date, now
from frappe import _, msgprint
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_card_within, get_sorted_card, get_all_dtrp, get_schedule, get_shift_map, get_all_tla, get_defaults)

def get_employee_details(self):
	if self.is_new():
		full_name, company = frappe.get_value("Employee", self.employee, ["full_name", "company"])
		if self.doctype in ["Leave Application", "Overtime Application", "Change Request Application", "Official Business Application"]:
			if not self.full_name:
				self.full_name = full_name

		if self.doctype in ["Undertime Application", "Excuse Tardiness Application", "Change Schedule Application", "DTR Problem Application", "Compensatory Time Off"]:
			if not self.employee_name:
				self.employee_name = full_name	
	
		if not self.company:
			self.company = company


def grant_head_subordinate_access(self):
	if self.is_new():
		reject_head_access = frappe.db.get_single_value('System Settings', 'head_not_allowed_for_subordinate')
		if reject_head_access:
			emp = frappe.db.sql(""" SELECT name, `user_id` FROM `tabEmployee` 
				WHERE user_id = %s AND user_id != "" AND user_id is not null LIMIT 1""",( frappe.session.user ), as_dict=1)

			for d in emp:
				subordinates = frappe.db.sql("""SELECT S.subordinate FROM `tabEmployee Subordinates` ES INNER JOIN `tabSubordinates` S ON S.`parent` = ES.`name` 
					WHERE ES.employee = %s """, ( d.name ), as_dict=True)

				for sub in subordinates:
					if self.employee == sub.subordinate:
						frappe.throw(_("You Cannot Create Application In Behalf Of Your Subordinate"))
		
def validate_approve_own_application(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers < 1:
		cur_user = frappe.session.user
		if not "Administrator" in frappe.get_roles(cur_user):
			user_id = frappe.get_value("Employee", self.employee, "user_id")
			if str(user_id).lower() == str(cur_user).lower():
				frappe.throw(_("Not Allowed to Approved own Application"))

def validate_reject_cancel_own_application(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers < 1:
		if self.workflow_state == "Rejected" or self.workflow_state == "Cancelled":
			cur_user = frappe.session.user
			if not "Administrator" in frappe.get_roles(cur_user):
				user_id = frappe.get_value("Employee", self.employee, "user_id")
				if str(user_id).lower() == str(cur_user).lower():
					frappe.throw(_("You cannot reject or cancel your own application"))

def validate_inactive_employee(self):
	is_active = frappe.get_value("Employee", self.employee, "is_active")
	if not is_active:
		frappe.throw(_("Employee {0} is not active").format(self.employee))

def validate_active_employee(self):
	is_active = frappe.get_value("Employee", self.employee, "is_active")
	if is_active:
		frappe.throw(_("Employee {0} is active").format(self.employee))

def get_user_fullname(self):
	user_fullname = frappe.db.sql("""SELECT full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
	if user_fullname:
		return cstr(user_fullname[0].full_name)

def change_owner(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers < 1:
		if not self.owner:
			owner = ""
			owner_email = frappe.db.sql("""SELECT user_id FROM `tabEmployee` WHERE `name` = %s LIMIT 1""",( self.employee ), as_dict=1)
			for d in owner_email:
				self.db_set("owner", d.user_id)

def clear_approval_history(self):
	if self.is_new():
		self.approval_history = ""
		self.last_approval_level = 0
		self.approved_by = ""
		self.approved_on = ""
		self.owner = ""

def get_levelled_approval(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers > 0:
		req_level = 0
		highest_level = frappe.db.sql(""" SELECT IFNULL(MAX(`level`), 0) as level FROM `tabEmployee Approvers` WHERE parenttype = "Employee" AND (`application` = %s OR `application` = "All") AND parent = %s """,(self.doctype, self.employee), as_dict=True)	
		if highest_level > 0:
			if not "Administrator" or not "Admin Approver" in frappe.get_roles(frappe.session.user):
				if int(self.last_approval_level) == 0:
					approver_level = frappe.db.sql(""" SELECT IFNULL(MAX(EA.`level`), 0) as `level` FROM `tabEmployee Approvers` EA JOIN `tabEmployee` TE ON EA.`approver` = TE.`name` WHERE EA.parenttype = "Employee" AND (EA.application = %s OR EA.application = "All") AND EA.parent = %s AND TE.user_id = %s AND EA.`level` = 1 """,(self.doctype, self.employee, frappe.session.user), as_dict=True)
					if approver_level:
						level_of_approval_first_level(self, approver_level, highest_level)
					else:
						frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to approve this application").format(self.doctype, self.name))
				else:
					req_level = int(self.last_approval_level)+1
					approver_level = frappe.db.sql(""" SELECT IFNULL(MAX(EA.`level`), 0) as `level` FROM `tabEmployee Approvers` EA JOIN `tabEmployee` TE ON EA.`approver` = TE.`name` WHERE EA.parenttype = "Employee" AND (EA.application = %s OR EA.application = "All") AND EA.parent = %s AND TE.user_id = %s AND EA.`level` = %s """,(self.doctype, self.employee, frappe.session.user, int(req_level)), as_dict=True)
					if approver_level:
						level_of_approval_next_level(self, approver_level, highest_level, req_level)
					else:
						frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to approve this application").format(self.doctype, self.name))
			else:
				set_levelled_approval_to_approved(self, highest_level)
		else:
			set_levelled_approval_to_approved(self, highest_level)

def level_of_approval_first_level(self, approver_level, highest_level):
	if int(approver_level[0].level) == 1:
		if int(approver_level[0].level) == int(highest_level[0].level):
			set_levelled_approval_to_approved(self, highest_level)
		else:
			set_levelled_approval_to_progress(self, approver_level)
	else:
		frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to approve this application").format(self.doctype, self.name))

def level_of_approval_next_level(self, approver_level, highest_level, req_level):
	if approver_level[0].level == highest_level[0].level:
		set_levelled_approval_to_approved(self, highest_level) 
	elif int(req_level) == int(approver_level[0].level) and int(req_level) > 1:
		set_levelled_approval_to_progress(self, approver_level)
	else:
		frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to approve this application").format(self.doctype, self.name))
		
def validate_cutoff_approval_date(self):
	if self.workflow_state == "Approved":
		cutoff_list = []
		approvals_cutoff = None
		target_date, from_date, to_date = None, None, None
		approved_on = getdate(self.approved_on)
		if self.doctype in ['Leave Application', 'Overtime Application', 'Official Business Application', 'Change Schedule Application']:
			from_date = self.from_date
			to_date = self.to_date

		if self.doctype in ['Compensatory Time Off']:
			from_date = self.from_date
			to_date = self.to_date

		if self.doctype in ['Excuse Tardiness Application']:
			target_date = self.date

		if self.doctype in ['Undertime Application']:
			target_date = self.from_date

		if self.doctype in ['DTR Problem Application']:
			target_date = self.target_date

		if self.doctype in ['Timelogs Application']:
			if self.timelogs:
				targets = []
				for d in self.timelogs:
					targets.append(d.target_date)
				target_date = max(targets)

		if target_date:
			approvals_cutoff = frappe.db.sql("""SELECT MAX(`approval_cutoff`) as `approval_cutoff` FROM `tabPayroll Period` WHERE `company` = %s AND %s BETWEEN `attendance_from` AND `attendance_to` """,(self.company, target_date), as_dict=1)
		if from_date and to_date:
			approvals_cutoff = frappe.db.sql("""SELECT MAX(`approval_cutoff`) as `approval_cutoff` FROM `tabPayroll Period` WHERE `company` = %s AND `attendance_from` <= %s And `attendance_to` >= %s """,(self.company, from_date, to_date), as_dict=1)
		
		for ap in approvals_cutoff:
			if ap.approval_cutoff:
				if approved_on >= getdate(ap.approval_cutoff):
					frappe.msgprint("Approved Application is Beyond Approval Cut off")

def validate_approver_userperm(self):
	missing_up = {}

	approvers = frappe.db.sql("""SELECT EA.`approver`, EA.`level`, TE.`full_name`, TE.`user_id` 
		FROM `tabEmployee Approvers` EA INNER JOIN `tabEmployee` TE ON EA.`approver`=TE.`name`
		WHERE EA.`parent` = %s AND (EA.`application` = %s OR EA.`application` = "All")""",(self.employee, self.doctype), as_dict=1)
	if approvers:
		for app in approvers:
			user_permission = frappe.db.sql("""SELECT `name` FROM `tabUser Permission` 
				WHERE `for_value` = %s AND `user` = %s AND `allow` = 'Employee' """,(self.employee, app.user_id),as_dict=True)
	
			if not user_permission:
				missing_up[cstr(str(app.approver)+str(app.level))] = {
					"approver": app.approver,
					"full_name": app.full_name,
					"level": app.level,
				}
	
		missing_out = []
		for ms in sorted(missing_up.items(), key=lambda k: k[1]['level']):
			missing_out.append( "Level: "+cstr(ms[1]['level'])+" Approver:"+cstr(ms[1]['approver'])+" - "+cstr(ms[1]['full_name']) )
		if missing_out:
			message = "Approvers with No Permission with this Employee: <br>"
			message+="<br>".join(missing_out)
			frappe.throw(_(message))
	else:
		frappe.throw(_("Employee has No Approver for this Application"))

def set_levelled_approval_to_progress(self, approver_level):
	approval_history = ""
	if self.approval_history is not None:
		approval_history = self.approval_history
	approval_history = cstr(approval_history)+"Level "+cstr(approver_level[0].level)+": "+cstr(frappe.session.user)+" approved on "+cstr(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	self.db_set("approval_history", approval_history)
	self.db_set("last_approval_level", approver_level[0].level)
	self.db_set("workflow_state", "Approval in Progress")
	self.db_set("approved_by", frappe.session.user)
	self.db_set("approved_on", now())
	approver_name = frappe.db.sql("""SELECT full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
	if approver_name:
		self.db_set("approver_name", cstr(approver_name[0].full_name))
	frappe.db.commit()
	frappe.msgprint(_("<b>{0}: {1}</b><hr> Approval Successful").format(self.doctype, self.name))

def set_levelled_approval_to_approved(self, highest_level):
	approval_history = ""
	if self.approval_history is not None:
		approval_history = self.approval_history
	if highest_level[0].level is None:
		approval_history = cstr(approval_history)+cstr(frappe.session.user)+" approved on "+cstr(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	else:
		approval_history = cstr(approval_history)+"Level "+cstr(highest_level[0].level)+": "+cstr(frappe.session.user)+" approved on "+cstr(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	self.db_set("approval_history", approval_history)
	self.db_set("last_approval_level", highest_level[0].level)
	self.db_set("workflow_state", "Approved")
	self.db_set("approved_by", frappe.session.user)
	self.db_set("approved_on", now())
	approver_name = frappe.db.sql("""SELECT full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
	if approver_name:
		self.db_set("approver_name", cstr(approver_name[0].full_name))
	frappe.db.commit()
	frappe.msgprint(_("<b>{0}: {1}</b><hr> Approval Successful").format(self.doctype, self.name))

def get_levelled_approval_rejection(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers > 0:
		approver_level = frappe.db.sql(""" SELECT IFNULL(MAX(EA.`level`), 0) as `level` FROM `tabEmployee Approvers` EA JOIN `tabEmployee` TE ON EA.`approver` = TE.`name` WHERE EA.parenttype = "Employee" AND (EA.application = %s OR EA.application = "All") AND EA.parent = %s AND TE.user_id = %s """,(self.doctype, self.employee, frappe.session.user), as_dict=True)
		if not "Administrator" or not "Admin Approver" in frappe.get_roles(frappe.session.user):
			if self.workflow_state == "Rejected":
				if approver_level:
					if int(approver_level[0].level) != int(self.last_approval_level+1):
						frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to reject this application").format(self.doctype, self.name))
				if self.approval_history:
					if frappe.session.user in self.approval_history:
						frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to reject this application").format(self.doctype, self.name))

def get_approver_and_date(self):
	if self.workflow_state == "Approved":
		self.db_set("approved_by", frappe.session.user)
		self.db_set("approved_on", now())
		approver_name = frappe.db.sql("""SELECT full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
		if approver_name:
			self.db_set("approver_name", cstr(approver_name[0].full_name))
		frappe.db.commit()

def get_cancelled_by_and_date(self):
	if self.docstatus == 2:
		self.db_set("cancelled_by", frappe.session.user)
		self.db_set("cancelled_on", nowdate())
		cancelled_by_name = frappe.db.sql("""SELECT full_name FROM `tabEmployee` WHERE `user_id` = %s LIMIT 1""",( frappe.session.user ), as_dict=1)
		if cancelled_by_name:
			self.db_set("cancelled_by_name", cstr(cancelled_by_name[0].full_name))
		frappe.db.commit()

def get_current_logs(employee, target_date):
	cin, cout = "", ""

	emp = frappe.get_doc('Employee', employee)
	emp_map = frappe._dict()
	emp_map.setdefault(employee, frappe._dict({
			"employee": employee,
			"employee_name": emp.full_name,
			"company": emp.company,
			"employee_details": emp,
			"schedules": [],
			"timecards": [],
			"overrides": [],
			"hls": [],
			"lvs": [],
			"ots": [],
			"obs": [],
			"uts": [],
			"ext": [],
			"cto": [],
			"wss": [],
			"csa": [],
			"dtrp": [],
			"tla": [],
			"timelogs_map": {},
		})
	)

	shift_map = get_shift_map()
	#template_map = get_template_map()
	schedule = get_schedule(employee, target_date - timedelta(days=1), target_date + timedelta(days=1))
	bio_id = frappe.get_value('Employee',employee,'biometrics_id')
	timecard_list = get_timecard_list(bio_id, target_date - timedelta(days=1), target_date + timedelta(days=1))
	dtrp = get_dtrp(employee, target_date - timedelta(days=1), target_date + timedelta(days=1))
	tla = get_all_tla(emp_map, employee, target_date - timedelta(days=1), target_date + timedelta(days=1), 0, 0)
	emp_map[employee]['schedules'] = get_schedule(employee, target_date - timedelta(days=1), target_date + timedelta(days=1))

	for d in schedule:
		if target_date == d['target_date']:
			sched = {'target_date': d['target_date'], 'work_shift': d['work_shift'], 'is_default_schedule': d['is_default_schedule']}
			entry = get_defaults(emp, sched, shift_map, None)
			cards_in, cards_out = get_card_within(sched['target_date'], emp_map[employee]['timelogs_map'], emp_map[employee]['schedules'], 
				shift_map, entry.get('pre_shift'), entry.get('end_preshift'), entry.get('post_shift'), entry.get('end_postshift'), timecard_list, dtrp, tla)
			sorted_card_list = get_sorted_card(entry, cards_in, cards_out, emp_map[employee]['timelogs_map'])
			cin, cout = entry.get('card_in'), entry.get('card_out')

	return cin, cout

def get_overrides(employee, from_date, to_date):
	overrides = frappe.db.sql("""SELECT employee, target_date, time_in, break_in, break_out, time_out,
		TIMESTAMP(target_date, time_in) as card_datetime_in, TIMESTAMP(target_date, time_out) as card_datetime_out
		FROM `tabOverride List` 
		WHERE target_date >= %(from_date)s AND target_date <= %(to_date)s """,{
			"from_date": getdate(from_date),
			"to_date": getdate(to_date),
		}, as_dict=True)

	return overrides if overrides else []

def get_dtrp(employee, pay_from, pay_to):
		dtr_apps = frappe.db.sql(""" SELECT DA.`name`, DA.`employee`, TIMESTAMP(DA.`target_date`, DT.`request`) as card_datetime, 
			DA.`target_date`, DT.`request`, DT.`type`, DA.`approved_on`, DT.`card_type`
			FROM `tabDTR Problem Table` DT INNER JOIN `tabDTR Problem Application` DA ON DT.`parent`=DA.`name` 
			WHERE DA.`workflow_state` = 'Approved' AND DA.employee = %s
			AND DA.`target_date` >= %s AND DA.`target_date` <= %s
			ORDER BY card_datetime """, (employee, pay_from, pay_to), as_dict=1)

		return dtr_apps

def get_approver_email_list(self, event):
	approver_recipients = []
	next_approver_recipients = []
	approvers = frappe.db.sql(""" SELECT TE.user_id, EA.`level` FROM `tabEmployee Approvers` EA JOIN `tabEmployee` TE ON EA.`approver` = TE.`name` 
		WHERE EA.parenttype = "Employee" AND (EA.application = %s OR EA.application = "All") AND EA.parent = %s """,
	(self.doctype, self.employee), as_dict=True)

	self.db_set("approver_email_list", None)
	self.db_set("next_approver_email_list", None)
	if approvers:
		for app in approvers:
			if event == 'on_submit':
				if (int(self.last_approval_level)+1 == int(app.level)):
					approver_recipients.append(app.user_id)
				if (int(self.last_approval_level)+2 == int(app.level)):
					next_approver_recipients.append(app.user_id)
			if event == 'before_update_after_submit':
				if (int(self.last_approval_level)+2 == int(app.level)):
					approver_recipients.append(app.user_id)
				if (int(self.last_approval_level)+3 == int(app.level)):
					next_approver_recipients.append(app.user_id)

		if approver_recipients:
			send_to_approver = ', '.join(cstr(x) for x in approver_recipients)
			self.db_set("approver_email_list", send_to_approver)

		if next_approver_recipients:
			send_to_next_approver = ', '.join(cstr(x) for x in next_approver_recipients)
			self.db_set("next_approver_email_list", send_to_next_approver)