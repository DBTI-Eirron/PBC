# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _, scrub
from frappe.utils import getdate, validate_email_add, today, add_years, nowdate, cstr, getdate
from datetime import date
from frappe.contacts.address_and_contact import load_address_and_contact, delete_contact_and_address
from frappe.model.document import Document

class Employee(Document):
	def onload(self):
		load_address_and_contact(self, "employee")

	def validate(self):
		self.update_fullname()
		self.validate_date()
		self.get_age()
		self.validate_spouse()
		self.validate_salary()
		self.create_user()
		self.validate_is_qualified_dependent()
		if self.job_offer:
			frappe.db.sql(""" Update `tabOffer Letter` SET apply_type='Completed' where `name`=%s""", (self.job_offer))
			
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

	def validate_salary(self):
		if self.payroll_schedule == "Monthly":
			self.sss_freq = "2nd"
			self.hdmf_freq = "2nd"
			self.phic_freq = "2nd"
			self.whtax_freq = "2nd"
			frappe.msgprint("Government Settings Frequency Changed to ( 2nd ) because Schedule was set to Monthly")

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
		if not "Administrator" in frappe.get_roles(cur_user):
			sensitivy_user = frappe.db.sql(""" SELECT count(*) as `result` FROM `tabSensitivity Users` WHERE `allow_user` = %s AND `parent` = %s """,( cur_user, self.sensitivity ), as_dict=1)
			for user in sensitivy_user:
				if user.result != 0:
					return "access_granted"
				else:
					return "access_denied"

	def validate_is_qualified_dependent(self):
		for emp in self.get("family_members"):
			if emp.is_qualified_dependent == 1:
				emp.is_dependent = 1

	def get_age(self):
		today = date.today()
		bday = getdate(self.birthday)
		age = today.year - bday.year - ((today.month, today.day) < (bday.month, bday.day))
		self.age = age