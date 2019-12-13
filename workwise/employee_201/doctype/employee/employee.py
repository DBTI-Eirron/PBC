# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe.model.naming import make_autoname
from frappe import throw, _, scrub
from frappe.utils import getdate, validate_email_add, today, add_years, nowdate, cstr, getdate
from datetime import date
from frappe.contacts.address_and_contact import load_address_and_contact, delete_contact_and_address
from frappe.model.document import Document

class Employee(Document):
	def onload(self):
		load_address_and_contact(self, "employee")
		self.load_approvers()

	def load_approvers(self):
		for ap in self.approvers:
			ap.old_approver = ap.approver
			ap.old_application = ap.application
			ap.old_level = ap.level
		self.old_reports_to = self.reports_to
		self.approvers_count = len(self.approvers)


	def autoname(self):
		employee_naming = frappe.db.get_single_value('Employee Record Settings', 'employee_naming')
		series_format = frappe.db.get_single_value('Employee Record Settings', 'series_format')
		if employee_naming == 'Employee ID':
			if not self.employee_id:
				frappe.throw(_("Employee ID is mandatory"), frappe.MandatoryError)
			self.name = self.employee_id
		elif employee_naming == "Hired Date Series":
			if self.employee_id:
				self.name = self.employee_id
			else:
				if not self.date_hired:
					frappe.throw(_("Hired Date is mandatory"), frappe.MandatoryError)
				date_format = datetime.datetime.strptime(str(getdate(self.date_hired)), '%Y-%m-%d').strftime('%m%y')
				date_format = cstr(date_format)+"-"+".####"
				self.name = make_autoname(cstr(date_format))
				self.employee_id = self.name
		else:
			if not series_format:
				frappe.throw(_("Series Format is mandatory"), frappe.MandatoryError)
			if self.employee_id:
				self.name = self.employee_id
			else:
				self.name = make_autoname(cstr(series_format))
				self.employee_id = self.name

	def validate(self):
		self.update_fullname()
		self.validate_date()
		self.get_age_and_service_years()
		self.validate_spouse()
		self.validate_biometric_id()
		self.validate_period_group()
		self.validate_salary()
		self.validate_bank()
		self.create_user()
		self.validate_is_qualified_dependent()
		# if self.validate_change_approver():
		self.validate_employee_approvers()
		if self.job_offer:
			frappe.db.sql(""" Update `tabOffer Letter` SET apply_type='Completed' where `name`=%s""", (self.job_offer))
		if not self.is_new():
			self.employee_to_subordinate()
		self.update_approver()
		self.validate_user_status()

	def validate_user_status(self):
		if self.is_active:
			enabled = 1
		else:
			enabled = 0

		us = frappe.get_doc("User", self.user_id)
		us.update({
			"new_password": us.frappe_userid,
			"enabled": enabled,
		})
		us.save()
		

	def validate_change_approver(self):
		approvers_list = []
		se_approvers = frappe.db.sql("""SELECT ES.employee FROM `tabEmployee Subordinates` ES INNER JOIN `tabSubordinates` ESE WHERE ESE.subordinate = %s """,(self.name),as_dict=True)
		for se in se_approvers:
			if se.employee not in approvers_list:
				approvers_list.append(se.employee)

		if self.approvers_count != len(self.approvers):
			return 1
		if self.old_reports_to != self.reports_to:
			return 1
		for ap in self.approvers:
			if ap.old_approver != ap.approver or ap.old_application != ap.application or ap.old_level != ap.level:
				return 1
			if ap.approver not in approvers_list:
				return 1
		return 0


	def after_insert(self):
		self.employee_to_subordinate()
			
	def on_update(self):
		if self.user_id:
			self.update_user_permissions()

	def update_user_permissions(self):
		frappe.permissions.add_user_permission("Employee", self.name, self.user_id)
		frappe.permissions.set_user_permission_if_allowed("Company", self.company, self.user_id)

	def update_fullname(self):
		if self.middle_name:
			self.full_name = self.last_name + ', ' + self.first_name + ' ' + self.middle_name
		else:
			self.full_name = self.last_name + ', ' + self.first_name

	def validate_biometric_id(self):
		if self.biometrics_id and self.is_active:
			bio_list = frappe.db.sql(""" SELECT DISTINCT `biometrics_id` FROM `tabEmployee` WHERE `is_active` = 1 AND `name` != %s """,(self.name) , as_dict=1)
			for b in bio_list:
				if self.biometrics_id == b.biometrics_id:
					frappe.throw(_("Biometric ID is already taken"))
					break

	def validate_period_group(self):
		period_group = frappe.db.get_single_value('Payroll Settings', 'strict_period_group')
		if period_group:
			if not self.period_group:
				frappe.throw("Period Group is Required for Strict use of Period Group")

	def validate_salary(self):
		if self.payroll_schedule == "Monthly":
			self.sss_freq = "2nd"
			self.hdmf_freq = "2nd"
			self.phic_freq = "2nd"
			self.whtax_freq = "2nd"
			frappe.msgprint("Government Settings Frequency Changed to ( 2nd ) because Schedule was set to Monthly")

		if self.payroll_schedule != "Weekly" and (self.sss_freq == "All" or self.hdmf_freq == "All" or self.phic_freq == "All" or self.whtax_freq == "All"):
			frappe.throw(" 'All' Frequency in SSS, HDMF, PHIC and WHTAX is only allowed for 'Weekly' Employees ")

		if self.payroll_schedule == "Weekly":
			if self.sss_freq == ("3rd" or "4th" or "5th"):
				self.sss_freq = "2nd" 
				frappe.msgprint("SSS Frequency Changed to ( 2nd ) because (3rd 4th 5th) is not allowed for Monthly and Semi-Monthly")

			if self.hdmf_freq == ("3rd" or "4th" or "5th"):
				self.hdmf_freq = "2nd" 
				frappe.msgprint("HDMF Frequency Changed to ( 2nd ) because (3rd 4th 5th) is not allowed for Monthly and Semi-Monthly")

			if self.phic_freq == ("3rd" or "4th" or "5th"):
				self.phic_freq = "2nd" 
				frappe.msgprint("PHIC Frequency Changed to ( 2nd ) because (3rd 4th 5th) is not allowed for Monthly and Semi-Monthly")

			if self.whtax_freq == ("3rd" or "4th" or "5th"):
				self.whtax_freq = "2nd" 
				frappe.msgprint("WHTAX Frequency Changed to ( 2nd ) because (3rd 4th 5th) is not allowed for Monthly and Semi-Monthly")

	def validate_bank(self):
		if self.mode_of_payment == "Bank":
			if not self.bank_setup:
				frappe.throw("Bank Setup is required")

	def create_user(self):
		if self.email:
			if not self.user_id:
				user = frappe.new_doc("User")
				user.update({
					"email": self.email,
					"first_name": self.first_name,
					"send_welcome_mail": 0,
					"last_name": self.last_name,
				})
				if user.insert():
					self.user_id = self.email
					user = frappe.get_doc("User", self.user_id)
					user.flags.ignore_permissions = True
					user.add_roles(self.role)
					user.save()
					frappe.defaults.set_user_default("Employee", self.name, self.user_id)

	def update_user(self):
		if self.user_id:
			user = frappe.get_doc("User", self.user_id)
			user.flags.ignore_permissions = True

		if "Employee" not in user.get("roles"):
			user.add_roles("Employee")

		# copy details like Fullname, DOB and Image to User
		if self.employee_name and not (user.first_name and user.last_name):
			employee_name = self.employee_name.split(" ")
			if len(employee_name) >= 3:
				user.last_name = " ".join(employee_name[2:])
				user.middle_name = employee_name[1]
			elif len(employee_name) == 2:
				user.last_name = employee_name[1]

			user.first_name = employee_name[0]

		if self.date_of_birth:
			user.birth_date = self.date_of_birth

		if self.gender:
			user.gender = self.gender

		if self.image:
			if not user.user_image:
				user.user_image = self.image
				try:
					frappe.get_doc({
						"doctype": "File",
						"file_name": self.image,
						"attached_to_doctype": "User",
						"attached_to_name": self.user_id
					}).insert()
				except frappe.DuplicateEntryError:
					# already exists
					pass

		user.save()

	def validate_date(self):
		if self.birthday and getdate(self.birthday) > getdate(today()):
			throw(_("Birthday cannot be greater than today."))	

	def validate_spouse(self):
		if self.civil_status == "Single":
			self.spouse = ""

		if self.civil_status == "Married": 
			if not self.spouse:
				throw(_("Spouse is required if Married"))

	def get_user_sensitivity_level(self):
		cur_user = frappe.session.user
		if not self.is_new():
			if not "Administrator" in frappe.get_roles(cur_user):
				if self.sensitivity:
					sensitivy_user = frappe.db.sql(""" SELECT count(*) as `result` FROM `tabSensitivity Users` WHERE `allow_user` = %s AND `parent` = %s """,( cur_user, self.sensitivity ), as_dict=1)
					for user in sensitivy_user:
						if user.result != 0:
							return "access_granted"
						else:
							return "access_denied"
				else:
					return "access_denied"
			else:
				return "access_granted"
		else:
			return "access_granted"

	def validate_is_qualified_dependent(self):
		for emp in self.get("family_members"):
			if emp.is_qualified_dependent == 1:
				emp.is_dependent = 1

	def get_age_and_service_years(self):
		#Get Age
		today = date.today()
		bday = getdate(self.birthday)
		age = today.year - bday.year - ((today.month, today.day) < (bday.month, bday.day))
		self.age = age

		#Get Years in Service
		dte_hired = getdate(self.date_hired)
		serv_date = date.today()
		if self.date_retired:
			serv_date = getdate(self.date_retired)
		if self.date_resigned:
			serv_date = getdate(self.date_resigned)
		if self.date_terminated:
			serv_date = getdate(self.date_terminated)
		yrs_in_serv = serv_date.year - dte_hired.year - ((serv_date.month, serv_date.day) < (dte_hired.month, dte_hired.day))
		self.years_in_service = yrs_in_serv

	def validate_employee_approvers(self):
		unique_emp = []
		unique_entries = []

		for d in self.get("approvers"):
			is_active = frappe.get_value("Employee", d.approver, "is_active")
			if not is_active:
				frappe.throw(_("Approver {0}: {1} is not active").format(d.approver, d.approver_name))

			if str(d.approver+d.application+d.level) not in unique_emp:
				unique_emp.append(str(d.approver+d.application+d.level));

				i = {
					"approver": d.approver,
					"approver_name": d.approver_name,
					"application": d.application,
					"level": d.level
				}	
				unique_entries.append(i);

		self.set('approvers', [])
		for ue in unique_entries:
			row = self.append('approvers', {})
			row.update(ue)

	def employee_to_subordinate(self):
		sub_list = []
		cur_sub_list = []

		if self.approvers:
			for d in self.get("approvers"):
				if d.approver not in sub_list:
					sub_list.append(str(d.approver))

		if self.reports_to:
			if self.reports_to not in sub_list:
				sub_list.append(str(self.reports_to))

		cur_subordinates = frappe.db.sql(""" SELECT TS.`parent`, TS.`subordinate`, TE.`user_id` FROM `tabSubordinates` TS INNER JOIN `tabEmployee` TE ON TS.`parent`=TE.`name` 
			WHERE TS.`created_from_employee` = %s """,( self.name ), as_dict=1)
		for cur in cur_subordinates:
			if not cur.subordinate in sub_list:
				frappe.db.sql("""DELETE FROM `tabSubordinates` WHERE `created_from_employee` = %(employee)s AND `subordinate` = %(employee)s AND `parent` = %(head)s """,
				({ 	"head": cur.parent, "employee": self.name,	}), as_dict=True)

				frappe.db.sql("""DELETE FROM `tabUser Permission` WHERE `is_automated` = 1 AND `user` = %(user_id)s AND `allow` = 'Employee' AND `for_value` = %(employee)s """,
				({ 	"user_id": cur.user_id, "employee": self.name,	}), as_dict=True)
				frappe.cache().delete_value('user_permissions')
		
		for sub in sub_list:
			self.add_to_subordinate(sub)

		

	def add_to_subordinate(self, emp):
		in_subordinate = frappe.db.sql(""" SELECT * FROM `tabSubordinates` WHERE `parent`= %s AND `subordinate` = %s """,( emp, self.name ), as_dict=1)
		if not in_subordinate:
			get_emp_sub = frappe.db.sql("""SELECT TS.`name` FROM `tabEmployee Subordinates` TS WHERE TS.`name` = %(employee)s """,{ "employee": cstr(emp)}, as_dict=1)
			if get_emp_sub:
				empsub_doc = frappe.get_doc("Employee Subordinates", emp)
				empsub_doc.append('subordinates',{
					"subordinate": self.name,
					"subordinate_name": self.full_name,
					"created_from_employee": self.name,
				})
				empsub_doc.save()
			else:
				employee, employee_name, company = frappe.db.get_value("Employee", emp, ["name", "full_name", "company"])
				empsub_new_doc = frappe.new_doc("Employee Subordinates")
				empsub_new_doc.update({
					"employee": employee,
					"employee_name": employee_name,
					"company": company,
				})	
				empsub_new_doc.append('subordinates',{
					"subordinate": self.name,
					"subordinate_name": self.full_name,
					"created_from_employee": self.name,
				})
				empsub_new_doc.insert()
				empsub_new_doc.save()

	def update_approver(self):
		update = frappe.db.sql("UPDATE `tabEmployee Approvers` SET approver_name = %s WHERE approver = %s",(self.full_name,self.name))