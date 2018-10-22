# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import throw, _, scrub
from frappe.utils import get_datetime, cint, flt, today, cstr

class TrainingEvent(Document):

	def validate(self):
		self.validate_datetime()
		self.update_number_of_attendees()
		self.validate_participant_capacity()
		self.validate_attendees()
		self.validate_total_cost()

	def validate_datetime(self):
		if self.event_start and get_datetime(self.event_start) > get_datetime(self.event_end):
			throw(_("Date of Event Start cannot be greater than Date of Event End."))

		if self.event_start and get_datetime(self.event_start) < get_datetime(today()):
			throw(_("Date of Event Start cannot be less than Date Today."))

	def validate_participant_capacity(self):
		if self.number_of_attendees > self.participant_capacity:
			throw(_("Number of Attendees exceed the allowed Participant Capacity"))

	def validate_total_cost(self):
		self.total_cost = cint(self.number_of_attendees) * flt(self.cost_per_participant, 2);

	def update_number_of_attendees(self):
		attendees = 0
		for d in self.training_attendees:
			attendees += 1

		self.number_of_attendees = attendees

	def validate_attendees(self):
		check_list = []
		for d in self.training_attendees:
			check_list.append(cstr(d.employee))

		unique_chk_list = set(check_list)
		if len(unique_chk_list) != len(check_list):
			throw(_("Same Employee has been entered multiple times"))

@frappe.whitelist()
def get_description(source_value):

	target_description = frappe.db.get_value("Training Course", source_value, "description");

	fields_list = {
		"target_description": target_description,
	}

	return fields_list

@frappe.whitelist()
def get_total_cost(number_of_attendees, cost_per_participant):
	
	total_cost = cint(number_of_attendees) * flt(cost_per_participant, 2);

	fields_list = {
		"target_total_cost": total_cost,
	}

	return fields_list