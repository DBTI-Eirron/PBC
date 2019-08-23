from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money, now_datetime, add_to_date
from frappe import _, msgprint
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_card_within, get_sorted_card, get_all_dtrp)

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
			if user_id == frappe.session.user:
				frappe.throw(_("Not Allowed to Approved own Application"))

def validate_reject_cancel_own_application(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers < 1:
		cur_user = frappe.session.user
		if not "Administrator" in frappe.get_roles(cur_user):
			user_id = frappe.get_value("Employee", self.employee, "user_id")
			if user_id == frappe.session.user:
				frappe.throw(_("You cannot reject or cancel your own application"))

def validate_inactive_employee(self):
	is_active = frappe.get_value("Employee", self.employee, "is_active")
	if not is_active:
		frappe.throw(_("Employee {0} is not active").format(self.employee))

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

def set_levelled_approval_to_progress(self, approver_level):
	approval_history = ""
	if self.approval_history is not None:
		approval_history = self.approval_history
	approval_history = cstr(approval_history)+"Level "+cstr(approver_level[0].level)+": "+cstr(frappe.session.user)+" approved on "+cstr(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	self.db_set("approval_history", approval_history)
	self.db_set("last_approval_level", approver_level[0].level)
	self.db_set("workflow_state", "Approval in Progress")
	self.db_set("approved_by", frappe.session.user)
	self.db_set("approved_on", nowdate())
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
	self.db_set("approved_on", nowdate())
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
		self.db_set("approved_on", nowdate())
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
	schedule = frappe.db.sql("""SELECT work_shift, datetime_in, datetime_out FROM `tabWork Schedule` 
		WHERE employee = %(employee)s AND target_date = %(target_date)s ORDER BY target_date ASC""",{
			"employee": employee, "target_date": target_date,
		}, as_dict=True)

	for d in schedule:
		entry = {"card_in": "", "card_out": "", "override_in": "", "override_out": "", "break_out": "", "break_in": ""}

		shift = frappe.db.sql("""SELECT * FROM `tabWork Shift` WHERE `name` = %s """,(d.work_shift), as_dict=True)
		pre_shift = add_to_date(d.datetime_in, hours= (0 -  shift[0].setup_preshift) )
		end_preshift = add_to_date(d.datetime_in, hours=  shift[0].end_preshift )
		post_shift = add_to_date(d.datetime_out, hours= (0 -  shift[0].setup_postshift) )
		end_postshift = add_to_date(d.datetime_out, hours= shift[0].end_postshift )

		bio = frappe.get_value("Employee", employee, "biometrics_id")
		timecard_list = get_timecard_list(bio, add_days(getdate(target_date), -1), add_days(getdate(target_date), +1))
		dtrp = get_dtrp(employee, add_days(getdate(target_date), -1), add_days(getdate(target_date), +1))
		cards_in, cards_out = get_card_within(pre_shift, end_preshift, post_shift, end_postshift, timecard_list, dtrp)
		get_sorted_card(entry, cards_in, cards_out)
		cin, cout = entry.get('card_in'), entry.get('card_out')

	return cin, cout 

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