from __future__ import unicode_literals
import frappe, datetime
from datetime import time, datetime, timedelta
from frappe.utils import cstr, cint, flt, nowdate, add_days, getdate, fmt_money
from frappe import _

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

def get_approver_and_date(self):
	self.db_set("approved_by", frappe.session.user)
	self.db_set("approved_on", nowdate())
	frappe.db.commit()

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