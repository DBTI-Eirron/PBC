from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from workwise.payroll.payroll_utils import get_transaction_map

def create_annualization(self):
	validate_filters(self)
	from_year, to_year = frappe.db.get_value("Payroll Year", self.payroll_year, ["from_date", "to_date"])
	employees = frappe.db.sql("""select `name`, tin, full_name, company, tin, date_retired, date_resigned, date_terminated from tabEmployee WHERE company = %(company)s AND payroll_schedule = %(schedule)s {conditions} 
		ORDER BY full_name ASC """.format( conditions=get_employee_conditions(self) ),
			({ 
				"company": self.company,
				"schedule": self.schedule,
				"employee": self.employee,
				"from_year": from_year,
				"to_year": to_year,
			}), as_dict=True)

	registers = get_registers(self, from_year, to_year)
	create_entries(self, employees, registers, from_year, to_year)	

def get_registers(self, from_year, to_year):
	registers = frappe.db.sql("""SELECT PR.name, PR.employee, PR.employee_name, PR.company, PR.posting_date, PR.schedule, PR.gross_payroll,
			PRE.pay_code, PRE.entry_type, PRE.is_taxable, PRE.amount FROM `tabPayroll Register` PR
		INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
		WHERE PR.company=%(company)s AND PR.schedule=%(schedule)s {conditions} 
		AND PR.posting_date >= %(from_year)s AND PR.posting_date <= %(to_year)s ORDER BY PR.employee_name ASC  """.format( conditions=get_conditions(self) ),
			({ 
				"company": self.company,
				"schedule": self.schedule,
				"employee": self.employee,
				"from_year": from_year,
				"to_year": to_year,
			}), as_dict=True)

	return registers

def get_conditions(self):
	conditions = []
	if self.employee:
		conditions.append("PR.employee=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_employee_conditions(self):
	conditions = []
	if self.employee:
		conditions.append("`name`=%(employee)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_employee_wise_register(registers, emp_map):
	tr_map = get_transaction_map()
	for reg in registers:
		if reg.employee in emp_map:
			if reg.pay_code in tr_map:
				btype = tr_map[reg.pay_code]['bir_type']
				_type = tr_map[reg.pay_code]['type'] 
				is_tax = tr_map[reg.pay_code]['is_taxable']
				if _type != "None":
					#NON-TAXABlE BASIC 
					if (btype == "Basic") and not is_tax:
						emp_map[reg.employee].nt_basic += reg.amount if _type == "Income" else -(reg.amount)
					
					if (btype == "Holiday") and not is_tax:
						emp_map[reg.employee].nt_holiday += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Overtime") and not is_tax:
						emp_map[reg.employee].nt_overtime += reg.amount if _type == "Income" else -(reg.amount)						

					if (btype == "Night Differential") and not is_tax:
						emp_map[reg.employee].nt_nightdiff += reg.amount if _type == "Income" else -(reg.amount)	

					if (btype == "Hazard") and not is_tax:
						emp_map[reg.employee].nt_hazard += reg.amount if _type == "Income" else -(reg.amount)	

					if (btype == "Deminimis") and not is_tax:
						emp_map[reg.employee].nt_demi += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Contribution"): #Contribution is Reversed and Regardless if Taxable or not
						emp_map[reg.employee].nt_contrib += -(reg.amount) if _type == "Income" else reg.amount 

					if (btype == "Other") and not is_tax:
						emp_map[reg.employee].nt_other += reg.amount if _type == "Income" else -(reg.amount)

					#TAXABLE BASIC SALARY
					if (btype == "Basic" or btype == "Contribution") and is_tax: #Contribution Reduce Taxable Basic
						emp_map[reg.employee].t_basic += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Representation") and is_tax:
						emp_map[reg.employee].t_represent += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Transportation") and is_tax:
						emp_map[reg.employee].t_transpo += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "COLA") and is_tax:
						emp_map[reg.employee].t_cola += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Housing") and is_tax:
						emp_map[reg.employee].t_housing += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Commission") and is_tax:
						emp_map[reg.employee].t_comm += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Profit Sharing") and is_tax:
						emp_map[reg.employee].t_sharing += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Fees") and is_tax:
						emp_map[reg.employee].t_fees += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Hazard") and is_tax:
						emp_map[reg.employee].t_hazard += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Overtime") and is_tax:
						emp_map[reg.employee].t_overtime += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Other Regular (A)") and is_tax:
						emp_map[reg.employee].t_other_a += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Other Regular (B)") and is_tax:
						emp_map[reg.employee].t_other_b += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Other Supplementary (A)") and is_tax:
						emp_map[reg.employee].t_other_sa += reg.amount if _type == "Income" else -(reg.amount)

					if (btype == "Other Supplementary (B)") and is_tax:
						emp_map[reg.employee].t_other_sb += reg.amount if _type == "Income" else -(reg.amount)

					#BENEFITS
					if btype == "13th Month":
						emp_map[reg.employee].total_benefits += reg.amount if _type == "Income" else -(reg.amount)

					#TAX WITHHELD
					if btype == "TAX":
						emp_map[reg.employee].tax_withheld += -(reg.amount) if _type == "Income" else reg.amount 

	return emp_map

def create_entries(self, employees, registers, from_year, to_year):
	emp_map = get_employee_map(self, employees)
	emp_map = get_employee_wise_register(registers, emp_map)

	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
		frappe.db.sql("""DELETE FROM `tabAnnualization Register` WHERE employee = %s AND year = %s """,(emp, self.payroll_year), as_dict=1)
		ntax_benefits, tax_benefits, tax_due, adj_tax = 0, 0, 0, 0
		ntax_total, amt_withheld, over_withheld = 0, 0, 0
		
		if emp_dict.date_terminated or emp_dict.date_resigned or emp_dict.date_retired:
			if getdate(emp_dict.date_terminated) < getdate(to_year):
				emp_dict.is_terminated = 1
			if getdate(emp_dict.date_resigned) < getdate(to_year):
				emp_dict.is_terminated = 1
			if getdate(emp_dict.date_retired) < getdate(to_year):
				emp_dict.is_terminated = 1

		if emp_dict.total_benefits > 90000:
			emp_dict.nt_benefits  = 90000
			emp_dict.t_benefits  = abs(emp_dict.total_benefits - 90000)
		else:
			emp_dict.nt_benefits = emp_dict.total_benefits

		emp_dict.non_taxable_total = (emp_dict.nt_basic + emp_dict.nt_holiday + emp_dict.nt_overtime + emp_dict.nt_nightdiff + emp_dict.nt_hazard + 
			emp_dict.nt_benefits + emp_dict.nt_demi + emp_dict.nt_contrib + emp_dict.nt_other)

		emp_dict.taxable_total = (emp_dict.t_basic + emp_dict.t_represent + emp_dict.t_transpo + emp_dict.t_cola + emp_dict.t_housing + emp_dict.t_comm + emp_dict.t_sharing + 
			emp_dict.t_fees + emp_dict.t_benefits + emp_dict.t_hazard + emp_dict.t_overtime + emp_dict.t_other_a + emp_dict.t_other_b + emp_dict.t_other_sa + emp_dict.t_other_sb)

		emp_dict.gross_compensation = emp_dict.non_taxable_total + emp_dict.taxable_total

		table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
			WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(( emp_dict.taxable_total ), ( emp_dict.taxable_total ), 'Yearly'), as_dict=True )
		
		for t in table:
			tax_due = (flt( ( emp_dict.taxable_total ) , 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
			if t.prescribed > 0:
				tax_due += flt(t.prescribed, 8)	

		emp_dict.tax_due = tax_due

		withheld = emp_dict.tax_due - emp_dict.tax_withheld
		if withheld > 1:
			emp_dict.adj_amount_withheld = abs(withheld)
			emp_dict.adj_withheld = emp_dict.tax_withheld + emp_dict.adj_amount_withheld
		else:	
			emp_dict.adj_over_withheld = abs(withheld)
			emp_dict.adj_withheld = emp_dict.tax_withheld - emp_dict.adj_over_withheld

		register = frappe.new_doc("Annualization Register")
		register.update(emp_dict)
		register.insert()

def get_employee_map(self, employees):
	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"employee": emp.name,
				"employee_name": emp.full_name,
				"company": emp.company,
				"payroll_year": self.payroll_year,
				"tax_id": emp.tin,
				#TERMINATION DATES
				"date_terminated": emp.date_terminated,
				"date_resigned": emp.date_resigned,
				"date_retired": emp.date_retired,
				#STATUS
				"with_previous": 0,
				"is_terminated": 0,
				"minimum_wage": 0,		
				#PREVIOUS NON-TAXABLE
				"pnt_basic": 0,
				"pnt_holiday": 0,
				"pnt_overtime": 0,
				"pnt_nightdiff": 0,
				"pnt_hazard": 0,
				"pnt_benefits": 0,
				"pnt_demi": 0,
				"pnt_contrib": 0,
				"pnt_other": 0,
				"pnt_total": 0,
				#PREVIOUS TAXABLE
				"pt_basic": 0,
				"pt_represent": 0,
				"pt_transpo": 0,
				"pt_cola": 0,
				"pt_housing": 0,
				"pt_comm": 0,
				"pt_sharing": 0,
				"pt_fees": 0,
				"pt_benefits": 0,
				"pt_hazard": 0,
				"pt_overtime": 0,
				"pt_other_a": 0,
				"pt_other_b": 0,
				"pt_other_sa": 0,
				"pt_other_sb": 0,
				#NON-TAXABLE
				"nt_basic": 0,
				"nt_holiday": 0,
				"nt_overtime": 0,
				"nt_nightdiff": 0,
				"nt_hazard": 0,
				"nt_benefits": 0,
				"nt_demi": 0,
				"nt_contrib": 0,
				"nt_other": 0,
				#TAXABLE
				"t_basic": 0,
				"t_represent": 0,
				"t_transpo": 0,
				"t_cola": 0,
				"t_housing": 0,
				"t_comm": 0,
				"t_sharing": 0,
				"t_fees": 0,
				"t_benefits": 0,
				"t_hazard": 0,
				"t_overtime": 0,
				"t_other_a": 0,
				"t_other_b": 0,
				"t_other_sa": 0,
				"t_other_sb": 0,
				#TOTALS
				"gross_compensation": 0,
				"total_benefits": 0,
				"non_taxable_total": 0,
				"taxable_total": 0,
				"ptax_due": 0,
				"ptax_withheld": 0,					
				"tax_due": 0,
				"tax_withheld": 0,				
				"adj_amount_withheld": 0,
				"adj_over_withheld": 0,
				"adj_withheld": 0
			})
		)

	return emp_map

def validate_filters(self):
	if not self.company:
		frappe.throw(" Company is Required for Annualization Processing")

	if not self.payroll_year:
		frappe.throw(" Year is Required for Annualization Processing")

	if not self.schedule:
		frappe.throw(" Payroll Schedule is Required for Annualization Processing")

