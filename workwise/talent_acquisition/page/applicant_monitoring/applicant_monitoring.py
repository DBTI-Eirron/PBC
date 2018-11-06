# -*- coding: utf-8 -*-
# Copyright (c) 2018, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate, formatdate
from frappe.model.document import Document

class Modules(Document):
	pass

@frappe.whitelist()
def get_candidates(target_doc=None):
	info = {
		"candidates": "",
		"schedule_assessment": "",
		"interview": "",
		"background_investigation": "",
		"contract_sigining": "",
		"job_offer": "",
		"onboarding": "",		
		"ar": "",
	}
	#STEP 1
	info['candidates'] = frappe.db.sql("""SELECT * FROM `tabJob Applicant` WHERE docstatus = 0  AND apply_type = 'Candidate'""", as_dict=1)
	
	#STEP 2
	info['schedule_assessment'] = frappe.db.sql("""SELECT * FROM `tabJob Applicant` WHERE apply_type = 'For Assessment' AND docstatus = 1 """, as_dict=1)
	
	#STEP 3
	info['interview'] = frappe.db.sql("""SELECT * FROM `tabSchedules and Assessment` WHERE apply_type = 'For Interview' AND docstatus = 1  AND interview_status != 'Completed' """, as_dict=1)
	
	#STEP 4
	info['background_investigation'] = frappe.db.sql("""SELECT * FROM `tabSchedules and Assessment` WHERE apply_type = 'Background Investigation' AND docstatus = 1 AND interview_status = 'Completed' """, as_dict=1)
	
	#STEP 5
	info['job_offer'] = frappe.db.sql("""SELECT * FROM `tabBackground Investigation` WHERE apply_type = 'Job Offer' AND docstatus = 1 AND investigation_status = 'Passed' """, as_dict=1)
	
	#STEP 6
	info['contract_signing'] = frappe.db.sql("""SELECT * FROM `tabOffer Letter` WHERE apply_type = 'For Contract Signing' AND status = 'Accepted' AND docstatus = 1 AND signed_contract IS NULL """, as_dict=1)
	
	#STEP 7
	info['for_employee'] = frappe.db.sql("""SELECT * FROM `tabOffer Letter` WHERE apply_type = 'For 201' AND status = 'Accepted' AND docstatus = 1  """, as_dict=1)
	
	#Personel Requisition
	info['ar'] = frappe.db.sql("""SELECT * FROM `tabPersonnel Requisition` WHERE docstatus = 1 """, as_dict=1)
	
	return info

@frappe.whitelist()
def get_requisition(user=None):	
	fields = ['name','creation']
	user_icons = frappe.db.get_all('Talent Requisition', fields=fields)

	return user_icons