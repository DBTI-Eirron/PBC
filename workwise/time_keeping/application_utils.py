from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

def grant_head_subordinate_access(self):
	reject_head_access = frappe.db.get_single_value('System Settings', 'head_not_allowed_for_subordinate')
	if reject_head_access == 1:
		subordinate = frappe.db.sql(""" SELECT `for_value` FROM `tabUser Permission` WHERE `allow` = "Employee" AND `for_value` = %s AND `user` = %s """, ( self.employee, frappe.session.user ), as_dict=True)
		if subordinate:
			user_id = frappe.db.sql("""SELECT user_id FROM `tabEmployee` WHERE `name` = %s LIMIT 1""",( self.employee ), as_dict=1)
			if user_id[0].user_id != frappe.session.user:
				frappe.throw(_("You Cannot Create Application In Behalf Of Your Subordinate"))

def get_approver_and_date(self):
	self.approved_by = frappe.session.user
	self.approved_on = nowdate()

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
		self.owner = d.user_id