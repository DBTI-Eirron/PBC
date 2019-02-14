from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money, now_datetime
from frappe import _, msgprint

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
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		user_id = frappe.get_value("Employee", self.employee, "user_id")
		if user_id == frappe.session.user:
			frappe.throw(_("Not Allowed to Approved own Application"))

def validate_reject_cancel_own_application(self):
	cur_user = frappe.session.user
	if not "Administrator" in frappe.get_roles(cur_user):
		user_id = frappe.get_value("Employee", self.employee, "user_id")
		if user_id == frappe.session.user:
			frappe.throw(_("You cannot reject or cancel your own application"))

def change_owner(self):
	owner = ""
	owner_email = frappe.db.sql("""SELECT user_id FROM `tabEmployee` WHERE `name` = %s LIMIT 1""",( self.employee ), as_dict=1)
	for d in owner_email:
		self.db_set("owner", d.user_id)

def get_levelled_approval(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers > 0:
		highest_level = frappe.db.sql(""" SELECT MAX(`level`) as level FROM `tabEmployee Approvers` WHERE parenttype = "Employee" AND application = %s AND parent = %s """,(self.doctype, self.employee), as_dict=True)	
		if not "Administrator" in frappe.get_roles(frappe.session.user):
			if int(self.last_approval_level) == 0:
				approver_level = frappe.db.sql(""" SELECT IFNULL(MAX(`level`), 0) as `level` FROM `tabEmployee Approvers` WHERE parenttype = "Employee" AND application = %s AND parent = %s AND approver_userid = %s AND `level` = 1 """,(self.doctype, self.employee, frappe.session.user), as_dict=True)
				if approver_level:
					if int(approver_level[0].level) == 1:
						if int(approver_level[0].level) == int(highest_level[0].level):
							set_levelled_approval_to_approved(self, highest_level)
						else:
							set_levelled_approval_to_progress(self, approver_level)
					else:
						frappe.throw(_("Insufficient permission to approve this application"))
				else:
					frappe.throw(_("Insufficient permission to approve this application"))
			else:
				last_approval_level = int(self.last_approval_level+1)
				approver_level = frappe.db.sql(""" SELECT IFNULL(MAX(`level`), 0) as `level` FROM `tabEmployee Approvers` WHERE parenttype = "Employee" AND application = %s AND parent = %s AND approver_userid = %s AND `level` = %s """,(self.doctype, self.employee, frappe.session.user, last_approval_level), as_dict=True)
				if approver_level:
					if int(approver_level[0].level) == int(highest_level[0].level):
						set_levelled_approval_to_approved(self, highest_level)
					else:
						if int(approver_level[0].level) == int(self.last_approval_level+1):
							set_levelled_approval_to_progress(self, approver_level)
						else:
							frappe.throw(_("Insufficient permission to approve this application"))
				else:
					frappe.throw(_("Insufficient permission to approve this application"))
		else:
			if highest_level:
				set_levelled_approval_to_approved(self, highest_level)

def set_levelled_approval_to_progress(self, approver_level):
	approval_history = ""
	if self.approval_history is not None:
		approval_history = self.approval_history
	approval_history = str(approval_history)+"Level "+str(approver_level[0].level)+": "+str(frappe.session.user)+" approved on "+str(now_datetime().strftime('%Y-%m-%d %H:%M:%S'))+"\n"
	self.db_set("approval_history", approval_history)
	self.db_set("last_approval_level", approver_level[0].level)
	self.db_set("workflow_state", "Approval in Progress")
	frappe.db.commit()
	frappe.msgprint(_("Approval Successful"))

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
	frappe.msgprint(_("Approval Successful"))

def get_levelled_approval_rejection(self):
	enable_employee_approvers = frappe.db.get_single_value('Timekeeping Settings', 'enable_employee_approvers')
	if enable_employee_approvers > 0:
		approver_level = frappe.db.sql(""" SELECT IFNULL(SUM(`level`), 0) as level FROM `tabEmployee Approvers` WHERE parenttype = "Employee" AND application = %s AND parent = %s AND approver_userid = %s """,(self.doctype, self.employee, frappe.session.user), as_dict=True)
		if not "Administrator" in frappe.get_roles(frappe.session.user):
			if self.workflow_state == "Rejected":
				if approver_level:
					if int(approver_level[0].level) != int(self.last_approval_level+1):
						frappe.throw(_("Insufficient permission to reject this application"))
				if self.approval_history:
					if frappe.session.user in self.approval_history:
						frappe.throw(_("Insufficient permission to reject this application"))

def get_approver_and_date(self):
	if self.workflow_state == "Approved":
		self.db_set("approved_by", frappe.session.user)
		self.db_set("approved_on", nowdate())
		frappe.db.commit()