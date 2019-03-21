from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money, now_datetime
from frappe import _, msgprint
from workwise.time_keeping.attendance_utils import (get_timecard_list, get_card_within, get_sorted_card)

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

def change_owner(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers < 1:
		if not self.owner:
			owner = ""
			owner_email = frappe.db.sql("""SELECT user_id FROM `tabEmployee` WHERE `name` = %s LIMIT 1""",( self.employee ), as_dict=1)
			for d in owner_email:
				self.db_set("owner", d.user_id)

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
	approval_history = str(approval_history)+"Level "+str(approver_level[0].level)+": "+str(frappe.session.user)+" approved on "+str(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	self.db_set("approval_history", approval_history)
	self.db_set("last_approval_level", approver_level[0].level)
	self.db_set("workflow_state", "Approval in Progress")
	frappe.db.commit()
	frappe.msgprint(_("<b>{0}: {1}</b><hr> Approval Successful").format(self.doctype, self.name))

def set_levelled_approval_to_approved(self, highest_level):
	approval_history = ""
	if self.approval_history is not None:
		approval_history = self.approval_history
	if highest_level[0].level is None:
		approval_history = str(approval_history)+str(frappe.session.user)+" approved on "+str(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	else:
		approval_history = str(approval_history)+"Level "+str(highest_level[0].level)+": "+str(frappe.session.user)+" approved on "+str(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	self.db_set("approval_history", approval_history)
	self.db_set("last_approval_level", highest_level[0].level)
	self.db_set("workflow_state", "Approved")
	self.db_set("approved_by", frappe.session.user)
	self.db_set("approved_on", nowdate())
	frappe.db.commit()
	frappe.msgprint(_("<b>{0}: {1}</b><hr> Approval Successful").format(self.doctype, self.name))

def get_levelled_approval_rejection(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers > 0:
		approver_level = frappe.db.sql(""" SELECT IFNULL(SUM(`level`), 0) as level FROM `tabEmployee Approvers` WHERE parenttype = "Employee" AND application = %s AND parent = %s AND approver_userid = %s """,(self.doctype, self.employee, frappe.session.user), as_dict=True)
		if not "Administrator" in frappe.get_roles(frappe.session.user):
			if self.workflow_state == "Rejected":
				if approver_level:
					if int(approver_level[0].level) != int(self.last_approval_level+1):
						frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to approve this application").format(self.doctype, self.name))
				if self.approval_history:
					if frappe.session.user in self.approval_history:
						frappe.throw(_("<b>{0}: {1}</b><hr> Insufficient permission to approve this application").format(self.doctype, self.name))

def get_approver_and_date(self):
	if self.workflow_state == "Approved":
		self.db_set("approved_by", frappe.session.user)
		self.db_set("approved_on", nowdate())
		frappe.db.commit()

def get_current_logs(employee, target_date):
	cin, cout = "", ""
	schedule = frappe.db.sql("""SELECT work_shift FROM `tabWork Schedule` 
		WHERE employee = %(employee)s AND target_date = %(target_date)s ORDER BY target_date ASC""",{
			"employee": employee, "target_date": target_date,
		}, as_dict=True)

	for d in schedule:
		entry = {"card_in": "", "card_out": "", "override_in": "", "override_out": "", "break_out": "", "break_in": ""}
		preshift, end_preshift, postshift, end_postshift = frappe.get_value("Work Shift", d.work_shift, ["setup_preshift","end_preshift", "setup_postshift", "end_postshift"])
		bio = frappe.get_value("Employee", employee, "biometrics_id")
		timecard_list = get_timecard_list(bio, add_days(getdate(target_date), -1), add_days(getdate(target_date), +1))
		cards_in, cards_out = get_card_within(preshift, end_preshift, postshift, end_postshift, timecard_list)
		get_sorted_card(entry, cards_in, cards_out)
		cin, cout = entry.get('card_in'), entry.get('card_out')

	return cin, cout 