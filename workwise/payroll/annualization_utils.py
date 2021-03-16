from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, cstr, add_to_date
from workwise.payroll.payroll_utils import get_transaction_map

def get_annual_employees(employee, company, department, location, payroll_schedule, from_year, to_year):
	c_list = []
	if employee:
		c_list.append("TE.`name`=%(employee)s")

	if department:
		lft, rgt = frappe.db.get_value("Department", department, ["lft", "rgt"])
		c_list.append(_("( DEPT.`lft` BETWEEN '{0}' AND '{1}' )").format(lft, rgt))

	if location:
		c_list.append("TE.location=%(location)s")
	
	if frappe.session.user != "Administrator":
		c_list.append(_("TE.sensitivity IN ( SELECT SL.`name` FROM `tabSensitivity Level` SL INNER JOIN `tabSensitivity Users` SU ON SU.parent = SL.`name` WHERE allow_user = '{0}' )").format(frappe.session.user))

	conditions = "AND {}".format(" AND ".join(c_list)) if c_list else ""
	employees = frappe.db.sql("""SELECT TE.`name`, TE.tin, TE.full_name, TE.company, TE.location, TE.mwe_loc, TE.date_hired, TE.date_retired, TE.date_resigned, 
		TE.date_terminated, TE.date_contract_ended, TE.total_yr_days, TE.no_hours, TE.rate, TE.rate_type, TE.sensitivity, 
		(SELECT COUNT(`name`) FROM `tabEmployee External Work History` WHERE parent = TE.`name`) as has_prev
		FROM `tabEmployee` TE 
		LEFT JOIN `tabDepartment` DEPT ON TE.`department`=DEPT.`name`
		WHERE TE.company = %(company)s 
		AND TE.payroll_schedule = %(schedule)s AND TE.date_hired < %(to_year)s {conditions} 
		ORDER BY TE.full_name ASC """.format( conditions=conditions),
			({ 
				"company": company,
				"schedule": payroll_schedule,
				"employee": employee,
				"from_year": from_year,
				"to_year": to_year,
			}), as_dict=True)

	return employees

def get_annual_registers(employee, company, payroll_schedule, payroll_year, omit_hold):
	c_list = []
	if employee:
		c_list.append("employee=%(employee)s")

	if omit_hold:
		c_list.append("PR.on_hold='0' ")

	conditions = "and {}".format(" and ".join(c_list)) if c_list else ""	
	registers = frappe.db.sql("""SELECT PR.name, PR.employee, PR.employee_name, PR.company, PR.posting_date, PR.schedule, PR.gross_payroll,
			PRE.pay_code, PRE.entry_type, PRE.is_taxable, PRE.amount, PR.bonus, PR.monthly_rate, PR.daily_rate FROM `tabPayroll Register Entries` PRE
		INNER JOIN `tabPayroll Register` PR ON PR.`name` = PRE.`parent`
		INNER JOIN `tabPayroll Period` PP ON PR.period = PP.`name`
		WHERE PR.company=%(company)s AND PR.schedule=%(schedule)s {conditions} 
		AND PP.payroll_year = %(payroll_year)s  """.format( conditions=conditions ),
			({ 
				"company": company,
				"schedule": payroll_schedule,
				"employee": employee,
				"payroll_year": payroll_year,
			}), as_dict=True)

	return registers

def get_annual_prev2316(employee, payroll_year):
	c_list = []
	if employee:
		c_list.append("PR.employee=%(employee)s")

	conditions = "and {}".format(" and ".join(c_list)) if c_list else ""
	previous_bir = frappe.db.sql("""SELECT * FROM `tabBIR2316` 
		WHERE payroll_year = %(payroll_year)s AND document_type = "Previous" {conditions} 
		AND docstatus = 1 """.format( conditions=self.conditions ),
			({ 
				"employee": employee,
				"payroll_year": payroll_year,
			}), as_dict=1)

	return previous_bir

def get_annual_results(employees, registers, previous_bir, lastpay, payroll_year, from_year, to_year):
	annual_registers = []
	emp_map = get_employee_map(employees)
	company_map = get_company_map()
	get_employee_wise_register(registers, previous_bir, lastpay, emp_map)
	#Annualization Settings
	tax_nd_birtype = frappe.db.get_single_value("Payroll Settings", "tax_nd_birtype")
	ceiling_month_pay = frappe.db.get_single_value("Payroll Settings", "ceiling_month_pay")
	ceiling_deminimis = frappe.db.get_single_value("Payroll Settings", "ceiling_demi")
	use_ceiling_demi = frappe.db.get_single_value("Payroll Settings", "use_ceiling_demi")
	mwe_rate_basis = frappe.db.get_single_value("Payroll Settings", "mwe_rate_basis")
	anoa_label = frappe.db.get_single_value("Payroll Settings", "anoa_label")
	anob_label = frappe.db.get_single_value("Payroll Settings", "anob_label")
	anoa_sp_label = frappe.db.get_single_value("Payroll Settings", "anoa_sp_label")
	anob_sp_label = frappe.db.get_single_value("Payroll Settings", "anob_sp_label")
	loc_map = get_location_map()
	
	for emp, emp_dict in sorted(emp_map.items(), key=lambda x: x[1]['employee_name']):
		frappe.db.sql("""DELETE FROM `tabAnnualization Register` WHERE employee = %s AND payroll_year = %s """,(emp, payroll_year), as_dict=1)
		ntax_benefits, tax_benefits, tax_due, adj_tax = 0, 0, 0, 0
		ntax_total, amt_withheld, over_withheld = 0, 0, 0
		exclude = 0
		last_date_list = []
		rates = get_rates(emp_dict)

		emp_dict['rdo_code'] = company_map[emp_dict.company]['rdo_code']
		emp_dict['anoa_label'], emp_dict['anob_label'], emp_dict['anoa_sp_label'], emp_dict['anob_sp_label'] = anoa_label, anob_label, anoa_sp_label, anob_sp_label

		
		emp_dict.from_date = getdate(from_year)
		emp_dict.to_date = getdate(to_year)
		if getdate(emp_dict.date_hired) > getdate(from_year) and emp_dict.has_prev > 0:
				emp_dict.from_date = getdate(emp_dict.date_hired)

		if emp_dict.date_terminated or emp_dict.date_resigned or emp_dict.date_retired or emp_dict.date_contract_ended:
			if getdate(emp_dict.date_terminated) <= getdate(to_year):
				emp_dict.is_terminated = 1
				emp_dict.to_date = getdate(emp_dict.date_terminated)
			if getdate(emp_dict.date_resigned) <= getdate(to_year):
				emp_dict.is_terminated = 1
				emp_dict.to_date = getdate(emp_dict.date_resigned)
			if getdate(emp_dict.date_retired) <= getdate(to_year):
				emp_dict.is_terminated = 1
				emp_dict.to_date = getdate(emp_dict.date_retired)
			if getdate(emp_dict.date_contract_ended) <= getdate(to_year):
				emp_dict.is_terminated = 1
				emp_dict.to_date = getdate(emp_dict.date_retired)					
		
		if emp_dict.date_terminated or emp_dict.date_resigned or emp_dict.date_retired or emp_dict.date_contract_ended:
			if getdate(emp_dict.date_terminated) <= getdate(from_year):
				exclude = 1
			if getdate(emp_dict.date_resigned) <= getdate(from_year):
				exclude = 1
			if getdate(emp_dict.date_retired) <= getdate(from_year):
				exclude = 1
			if getdate(emp_dict.date_contract_ended) <= getdate(from_year):
				exclude = 1

		#Always reduce Basic to contrib
		emp_dict.total_basic -= abs(emp_dict.total_contrib)

		#get excess deminimis
		if use_ceiling_demi:
			emp_dict.total_conv=0
			emp_dict.med_cash=0
			emp_dict.total_med_cash=0
			emp_dict.total_rice=0
			emp_dict.total_uniform=0
			emp_dict.total_med_ast=0
			emp_dict.total_laundry=0
			emp_dict.total_awards=0
			emp_dict.total_gifts=0
			emp_dict.total_prod=0

			excess_cl_demi=0
			if emp_dict.total_demi > flt(ceiling_deminimis, 8):
				excess_cl_demi = flt(emp_dict.total_demi,8) - flt(ceiling_deminimis, 8)
				nt_cl_demi = flt(ceiling_deminimis, 8)
			else:
				nt_cl_demi = flt(emp_dict.total_demi, 8)

			final_demi = nt_cl_demi
			total_excess_demi = excess_cl_demi
			emp_dict.excess_demi = total_excess_demi

		else:
			emp_dict.total_demi = 0
			max_conversion = flt(rates['daily_rate'] * 10, 8)
			excess_conv=0
			if emp_dict.total_conv > max_conversion:
				excess_conv = flt(emp_dict.total_conv,8) - flt(max_conversion, 8)
				nt_conv = max_conversion
			else:
				nt_conv = flt(emp_dict.total_conv, 2)

			excess_med_cash=0
			if emp_dict.total_med_cash > 3000:
				excess_med_cash = flt(emp_dict.total_med_cash,8) - flt(3000, 8)
				nt_med_cash = 3000
			else:
				nt_med_cash = flt(emp_dict.total_med_cash, 2)

			excess_rice=0
			if emp_dict.total_rice > 24000:
				excess_rice = flt(emp_dict.total_rice,8) - flt(24000, 8)
				nt_rice = 24000
			else:
				nt_rice = flt(emp_dict.total_rice, 2)
			
			excess_uniform=0
			if emp_dict.total_uniform > 6000:
				excess_uniform = flt(emp_dict.total_uniform,8) - flt(6000, 8)
				nt_uniform = 6000
			else:
				nt_uniform = flt(emp_dict.total_uniform, 2)

			excess_med_ast=0
			if emp_dict.total_med_ast > 10000:
				excess_med_ast = flt(emp_dict.total_med_ast,8) - flt(10000, 8)
				nt_med_ast = 10000
			else:
				nt_med_ast = flt(emp_dict.total_med_ast, 2)

			excess_laundry=0
			if emp_dict.total_laundry > 3600:
				excess_laundry = flt(emp_dict.total_laundry,8) - flt(3600, 8)
				nt_laundry = 3600
			else:
				nt_laundry = flt(emp_dict.total_laundry, 2)

			excess_awards=0
			if emp_dict.total_awards > 10000:
				excess_awards = flt(emp_dict.total_awards,8) - flt(10000, 8)
				nt_awards = 10000
			else:
				nt_awards = flt(emp_dict.total_awards, 2)

			excess_gifts=0
			if emp_dict.total_gifts > 5000:
				excess_gifts = flt(emp_dict.total_gifts,8) - flt(5000, 8)
				nt_gifts = 5000
			else:
				nt_gifts = flt(emp_dict.total_gifts, 2)

			excess_prod=0
			if emp_dict.total_prod > 10000:
				excess_prod = flt(emp_dict.total_prod,8) - flt(10000, 8)
				nt_prod = 10000
			else:
				nt_prod = flt(emp_dict.total_prod, 2)												
			

			emp_dict.ex_conv = excess_conv
			emp_dict.ex_med_cash = excess_med_cash 
			emp_dict.ex_rice = excess_rice
			emp_dict.ex_uniform = excess_uniform 
			emp_dict.ex_med_ast = excess_med_ast 
			emp_dict.ex_laundry = excess_laundry 
			emp_dict.ex_awards = excess_awards 
			emp_dict.ex_gifts = excess_gifts
			emp_dict.ex_prod = excess_prod
			
			final_demi = nt_conv + nt_med_cash + nt_rice + nt_uniform + nt_med_ast + nt_laundry + nt_awards + nt_gifts + nt_prod
			total_excess_demi = excess_conv + excess_med_cash + excess_rice + excess_uniform + excess_med_ast + excess_laundry + excess_awards + excess_gifts + excess_prod
			emp_dict.excess_demi = flt(total_excess_demi, 8)


		#calculate if other benefits is beyond the ceiling and taxable benefits
		combined_benefits = emp_dict.total_benefits + total_excess_demi
		t_combined_benefits = 0
		nt_combined_benefits = 0
		exceed_ceiling = 0

		if flt(combined_benefits, 8) > flt(ceiling_month_pay, 8):
			nt_combined_benefits = flt(ceiling_month_pay, 8)
			t_combined_benefits = abs(flt(combined_benefits, 8) - flt(ceiling_month_pay, 8))
			exceed_ceiling = 1
		else:
			#assign as non taxable
			nt_combined_benefits = emp_dict.total_benefits + total_excess_demi

		#check for MWE
		emp_dict.minimum_wage = 0
		mwe = 0
		if emp_dict.mwe_loc:
			location = emp_dict.mwe_loc
		else:
			location = emp_dict.location

		if mwe_rate_basis == "Daily Rate":
			if rates['daily_rate'] < flt(loc_map[location]['min_wage'], 8):
				mwe = 1

		elif mwe_rate_basis == "Dynamic":
			if emp_dict.rate_type in ["Daily Rate","Hourly Rate","Weekly Rate"]:
				if rates['daily_rate'] < flt(loc_map[location]['min_wage'], 8):
					mwe = 1
			else:
				smw = flt(loc_map[location]['min_wage'], 8) * flt(emp_dict.total_yr_days, 8) / 12
				if rates['monthly_rate'] < smw:
					mwe = 1
		else:
			smw = flt(loc_map[location]['min_wage'], 8) * flt(emp_dict.total_yr_days, 8) / 12
			if rates['monthly_rate'] < smw:
				mwe = 1

		if mwe == 1:
			emp_dict.minimum_wage = 1
			#Fixed Exempt
			emp_dict.nt_demi = final_demi

			#exempt from smw
			emp_dict.nt_basic = emp_dict.total_basic
			emp_dict.nt_holiday = emp_dict.total_holiday
			emp_dict.nt_overtime = emp_dict.total_overtime
			emp_dict.nt_nightdiff = emp_dict.total_nightdiff
			emp_dict.nt_hazard = emp_dict.total_hazard

			#maintain taxable permanents
			emp_dict.t_represent = emp_dict.total_represent
			emp_dict.t_transpo = emp_dict.total_transpo
			emp_dict.t_cola = emp_dict.total_cola
			emp_dict.t_housing = emp_dict.total_housing
			emp_dict.t_comm = emp_dict.total_comm
			emp_dict.t_sharing = emp_dict.total_sharing
			emp_dict.t_fees = emp_dict.total_fees
			emp_dict.t_other_a = emp_dict.total_other_a
			emp_dict.t_other_b = emp_dict.total_other_b
			emp_dict.t_other_sa = emp_dict.total_other_sa
			emp_dict.t_other_sb = emp_dict.total_other_sb

			emp_dict.nt_contrib = emp_dict.total_contrib
			emp_dict.nt_other = emp_dict.total_other

			if exceed_ceiling == 1:
				emp_dict.nt_benefits = nt_combined_benefits
				emp_dict.t_benefits = t_combined_benefits					
			else:
				emp_dict.nt_benefits = nt_combined_benefits

		else:
			#Fixed Exempt
			emp_dict.nt_demi = final_demi
			emp_dict.nt_other = emp_dict.total_other

			#set contrib always non-tax
			emp_dict.nt_contrib = emp_dict.total_contrib

			emp_dict.t_basic = emp_dict.total_basic
			emp_dict.t_overtime = emp_dict.total_overtime
			#emp_dict.t_nightdiff = emp_dict.total_nightdiff no taxable ND in 2316
			emp_dict.t_hazard = emp_dict.total_hazard
			emp_dict.t_represent = emp_dict.total_represent
			emp_dict.t_transpo = emp_dict.total_transpo
			emp_dict.t_cola = emp_dict.total_cola
			emp_dict.t_housing = emp_dict.total_housing
			emp_dict.t_comm = emp_dict.total_comm
			emp_dict.t_sharing = emp_dict.total_sharing
			emp_dict.t_fees = emp_dict.total_fees
			emp_dict.t_other_a = emp_dict.total_other_a
			emp_dict.t_other_b = emp_dict.total_other_b
			emp_dict.t_other_sa = emp_dict.total_other_sa
			emp_dict.t_other_sb = emp_dict.total_other_sb

			if exceed_ceiling == 1:
				emp_dict.nt_benefits = nt_combined_benefits
				emp_dict.t_benefits = t_combined_benefits					
			else:
				emp_dict.nt_benefits = nt_combined_benefits

			#add taxable ND and Other to benefits after benefit calc,because there is no taxable ND and Other field
			if tax_nd_birtype == "Other Regular A":
				emp_dict.t_other_a += emp_dict.total_nightdiff
			elif tax_nd_birtype == "Other Regular B":
				emp_dict.t_other_b += emp_dict.total_nightdiff
			elif tax_nd_birtype == "Other Supplementary A":
				emp_dict.t_other_sa += emp_dict.total_nightdiff
			elif tax_nd_birtype == "Other Supplementary B":
				emp_dict.t_other_sb += emp_dict.total_nightdiff
			else:
				emp_dict.t_benefits += emp_dict.total_nightdiff

			emp_dict.t_benefits += emp_dict.total_holiday #taxable holiday on taxable add as benefits

		#PREVIOUS TOTALS
		#Previous totals are straight up
		emp_dict.prev_non_taxable_total = (emp_dict.pnt_basic + emp_dict.pnt_holiday + emp_dict.pnt_overtime + emp_dict.pnt_nightdiff + emp_dict.pnt_hazard + 
			emp_dict.pnt_benefits + emp_dict.pnt_demi + emp_dict.pnt_contrib + emp_dict.pnt_other)

		emp_dict.prev_taxable_total = (emp_dict.pt_basic + emp_dict.pt_represent + emp_dict.pt_transpo + emp_dict.pt_cola + emp_dict.pt_housing + emp_dict.pt_comm + emp_dict.pt_sharing + 
			emp_dict.pt_fees + emp_dict.pt_benefits + emp_dict.pt_hazard + emp_dict.pt_overtime + emp_dict.pt_other_a + emp_dict.pt_other_b + emp_dict.pt_other_sa + emp_dict.pt_other_sb)

		emp_dict.prev_gross_compensation = emp_dict.prev_non_taxable_total + emp_dict.prev_taxable_total
		emp_dict['item_22'] = emp_dict.prev_taxable_total


		#CURRENT TOTAL
		#Get Total Non-Taxable
		emp_dict.non_taxable_total = (emp_dict.nt_basic + emp_dict.nt_holiday + emp_dict.nt_overtime + emp_dict.nt_nightdiff + emp_dict.nt_hazard + 
			emp_dict.nt_benefits + emp_dict.nt_demi + emp_dict.nt_contrib + emp_dict.nt_other)	
		emp_dict['item_20'] = emp_dict.non_taxable_total

		#Get Total Taxable
		emp_dict.taxable_total = (emp_dict.t_basic + emp_dict.t_represent + emp_dict.t_transpo + emp_dict.t_cola + emp_dict.t_housing + emp_dict.t_comm + emp_dict.t_sharing + 
			emp_dict.t_fees + emp_dict.t_benefits + emp_dict.t_hazard + emp_dict.t_nightdiff + emp_dict.t_overtime + emp_dict.t_other_a + emp_dict.t_other_b + emp_dict.t_other_sa + emp_dict.t_other_sb)
		emp_dict['item_21'] = emp_dict.taxable_total

		#Get Gross Compensation
		emp_dict.gross_compensation = emp_dict.non_taxable_total + emp_dict.taxable_total
		emp_dict['item_19'] = emp_dict.gross_compensation

		emp_dict['item_23'] = emp_dict.item_21 + emp_dict.item_22

		#Get Tax Due
		taxable = emp_dict.taxable_total + emp_dict.prev_taxable_total
		table = frappe.db.sql("""SELECT prescribed, compensatory, percentage FROM `tabTRAIN Table`
			WHERE %s >= beginning AND %s <= ending AND frequency = %s LIMIT 1""",(( taxable ), ( taxable ), 'Yearly'), as_dict=True )

		for t in table:
			tax_due = (flt( ( taxable ) , 8) - flt(t.compensatory, 8)) * flt(flt(t.percentage, 8) / 100 , 8)
			if t.prescribed > 0:
				tax_due += flt(t.prescribed, 8)

		emp_dict.tax_due = tax_due
		#check if tax is to be refunded or to be paid
		withheld = emp_dict.tax_due - (emp_dict.tax_withheld + emp_dict.prev_tax_withheld)

		#Set Amount Withheld & Paid for in December
		emp_dict.adj_amount_withheld = (emp_dict.tax_withheld + emp_dict.prev_tax_withheld) - (emp_dict.withheld_nov + emp_dict.prev_withheld_nov)

		if withheld > 1:
			emp_dict.adj_withheld = abs(withheld)
		elif withheld < 0:
			emp_dict.adj_over_withheld = abs(withheld)
		else:
			emp_dict.adj_withheld = 0

		if exclude != 1:
			annual_registers.append(emp_dict)
			
	return annual_registers

def get_employee_wise_register(payroll_year, registers, previous_bir, lastpay, emp_map):
	tr_map = get_transaction_map()
	last_day_nov = monthrange(cint(payroll_year), 11)[1]
	last_day_nov = getdate(cstr(""+cstr(payroll_year)+"-11-"+cstr(last_day_nov)+""))
	first_day_jan = getdate(cstr(""+cstr(payroll_year)+"-1-1"))

	for reg in registers:
		if reg.employee in emp_map:
			if reg.pay_code in tr_map:
				btype = tr_map[reg.pay_code]['bir_type']
				_type = tr_map[reg.pay_code]['type'] 
				is_tax = tr_map[reg.pay_code]['is_taxable']
				if _type != "None":
					#ALWAYS TAXABLES
					if btype == "Basic":
						emp_map[reg.employee].total_basic += reg.amount if _type == "Income" else -(reg.amount)
					
					if btype == "Holiday":
						emp_map[reg.employee].total_holiday += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Overtime":
						emp_map[reg.employee].total_overtime += reg.amount if _type == "Income" else -(reg.amount)					

					if btype == "Night Differential":
						emp_map[reg.employee].total_nightdiff += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Hazard":
						emp_map[reg.employee].total_hazard += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Other Non-Taxable":
						emp_map[reg.employee].total_other += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Representation":
						emp_map[reg.employee].total_represent += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Transportation":
						emp_map[reg.employee].total_transpo += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "COLA":
						emp_map[reg.employee].total_cola += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Housing":
						emp_map[reg.employee].total_housing += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Commission":
						mp_map[reg.employee].total_comm += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Profit Sharing":
						emp_map[reg.employee].total_sharing += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Fees":
						emp_map[reg.employee].total_fees += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Other Regular A":
						emp_map[reg.employee].total_other_a += reg.amount if _type == "Income" else -(reg.amount)	

					if btype == "Other Regular B":
						emp_map[reg.employee].total_other_b += reg.amount if _type == "Income" else -(reg.amount)	

					if btype == "Other Supplementary A":
						emp_map[reg.employee].total_other_sa += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Other Supplementary B":
						emp_map[reg.employee].total_other_sb += reg.amount if _type == "Income" else -(reg.amount)

					#BENEFITS
					if btype == "13th Month":
						emp_map[reg.employee].total_benefits += reg.amount if _type == "Income" else -(reg.amount)

					#Deminimis
					if btype == "Deminimis":
						emp_map[reg.employee].total_demi += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Leave Conversion":
						emp_map[reg.employee].total_conv += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Medical Cash Allowance":
						emp_map[reg.employee].total_med_cash += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Rice Subsidy":
						emp_map[reg.employee].total_rice += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Uniform":
						emp_map[reg.employee].total_uniform += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Actual Medical Assistance":
						emp_map[reg.employee].total_med_ast += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Laundry Allowance":
						emp_map[reg.employee].total_laundry += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Achievement Awards":
						emp_map[reg.employee].total_awards += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Gifts":
						emp_map[reg.employee].total_gifts += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Productivity Incentive":
						emp_map[reg.employee].total_prod += reg.amount if _type == "Income" else -(reg.amount)																					

					#ALWAYS NOT TAXABLE
					if (btype == "Contribution"): #Contribution is Reversed and Regardless if Taxable or not
						emp_map[reg.employee].total_contrib += -(reg.amount) if _type == "Income" else reg.amount 

					#TAX WITHHELD
					if btype == "TAX":
						#get tax witheld jan - dec
						emp_map[reg.employee].tax_withheld += -(reg.amount) if _type == "Income" else reg.amount 
						emp_map[reg.employee].total_tax += -(reg.amount) if _type == "Income" else reg.amount
						
						#get tax witheld jan - nov
						if first_day_jan <= getdate(reg.posting_date) <= last_day_nov: 
							emp_map[reg.employee].withheld_nov += -(reg.amount) if _type == "Income" else reg.amount

	for d in previous_bir:
		if d.employee in emp_map:
			emp_map[d.employee].with_previous = 1
			#PREVIOUS NON-TAXABLE
			emp_map[d.employee].pnt_basic = d.ntax_bs
			emp_map[d.employee].pnt_holiday = d.ntax_ho
			emp_map[d.employee].pnt_overtime = d.ntax_ot
			emp_map[d.employee].pnt_nightdiff = d.ntax_nd
			emp_map[d.employee].pnt_hazard = d.ntax_hazard
			emp_map[d.employee].pnt_benefits = d.ntax_bonus
			emp_map[d.employee].pnt_demi = d.ntax_demi
			emp_map[d.employee].pnt_contrib = d.ntax_contrib
			emp_map[d.employee].pnt_other = d.ntax_other
			emp_map[d.employee].pnt_total = d.ntax_total

			#PREVIOUS TAXABLE
			emp_map[d.employee].pt_basic = d.tax_bs
			emp_map[d.employee].pt_represent = d.tax_rep
			emp_map[d.employee].pt_transpo = d.tax_transpo
			emp_map[d.employee].pt_cola = d.tax_cola
			emp_map[d.employee].pt_housing = d.tax_housing
			emp_map[d.employee].pt_comm = d.tax_commission
			emp_map[d.employee].pt_sharing = d.tax_sharing
			emp_map[d.employee].pt_fees = d.tax_fees
			emp_map[d.employee].pt_benefits = d.tax_bonus
			emp_map[d.employee].pt_hazard = d.tax_hazard
			emp_map[d.employee].pt_overtime = d.tax_ot
			emp_map[d.employee].pt_other_a = d.other_reg_a
			emp_map[d.employee].pt_other_b = d.other_reg_b
			emp_map[d.employee].pt_other_sa = d.other_supp_a
			emp_map[d.employee].pt_other_sb = d.other_supp_b

			#withheld
			emp_map[d.employee].prev_adj_withheld = d.sum_tatwa
			emp_map[d.employee].prev_tax_due = d.sum_td
			emp_map[d.employee].prev_tax_withheld = d.sum_tatwa
			emp_map[d.employee].prev_withheld_nov = d.sum_tatwa

	#LAST PAY
	for lp in lastpay:
		if lp.employee in emp_map:
			if lp.transaction_type in tr_map:
				btype = tr_map[lp.transaction_type]['bir_type']
				_type = lp.type
				is_tax = tr_map[lp.transaction_type]['is_taxable']
				if _type != "None":
					#ALWAYS TAXABLES
					if btype == "Basic":
						emp_map[lp.employee].total_basic += lp.amount if _type == "Income" else -(lp.amount)
					
					if btype == "Holiday":
						emp_map[lp.employee].total_holiday += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Overtime":
						emp_map[lp.employee].total_overtime += lp.amount if _type == "Income" else -(lp.amount)					

					if btype == "Night Differential":
						emp_map[lp.employee].total_nightdiff += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Hazard":
						emp_map[lp.employee].total_hazard += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Other Non-Taxable":
						emp_map[reg.employee].total_other += reg.amount if _type == "Income" else -(reg.amount)

					if btype == "Representation":
						emp_map[lp.employee].total_represent += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Transportation":
						emp_map[lp.employee].total_transpo += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "COLA":
						emp_map[lp.employee].total_cola += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Housing":
						emp_map[lp.employee].total_housing += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Commission":
						mp_map[lp.employee].total_comm += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Profit Sharing":
						emp_map[lp.employee].total_sharing += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Fees":
						emp_map[lp.employee].total_fees += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Other Regular A":
						emp_map[lp.employee].total_other_a += lp.amount if _type == "Income" else -(lp.amount)	

					if btype == "Other Regular B":
						emp_map[lp.employee].total_other_b += lp.amount if _type == "Income" else -(lp.amount)	

					if btype == "Other Supplementary A":
						emp_map[lp.employee].total_other_sa += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Other Supplementary B":
						emp_map[lp.employee].total_other_sb += lp.amount if _type == "Income" else -(lp.amount)

					#BENEFITS
					if btype == "13th Month":
						emp_map[lp.employee].total_benefits += lp.amount if _type == "Income" else -(lp.amount)

					#Deminimis
					if btype == "Deminimis":
						emp_map[lp.employee].total_demi += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Leave Conversion":
						emp_map[lp.employee].total_conv += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Medical Cash Allowance":
						emp_map[lp.employee].total_med_cash += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Rice Subsidy":
						emp_map[lp.employee].total_rice += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Uniform":
						emp_map[lp.employee].total_uniform += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Actual Medical Assistance":
						emp_map[lp.employee].total_med_ast += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Laundry Allowance":
						emp_map[lp.employee].total_laundry += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Achievement Awards":
						emp_map[lp.employee].total_awards += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Gifts":
						emp_map[lp.employee].total_gifts += lp.amount if _type == "Income" else -(lp.amount)

					if btype == "Productivity Incentive":
						emp_map[lp.employee].total_prod += lp.amount if _type == "Income" else -(lp.amount)							

					#ALWAYS NOT TAXABLE
					if (btype == "Contribution"): #Contribution is Reversed and Regardless if Taxable or not
						emp_map[lp.employee].total_contrib += -(lp.amount) if _type == "Income" else lp.amount 

					#TAX WITHHELD
					if btype == "TAX":
						emp_map[lp.employee].tax_withheld += -(lp.amount) if _type == "Add" else lp.amount
						emp_map[lp.employee].total_tax += -(lp.amount) if _type == "Add" else lp.amount

def get_employee_map(employees, payroll_year):
	emp_map = frappe._dict()
	for emp in employees:
		emp_map.setdefault(emp.name, frappe._dict({
				"employee": emp.name,
				"employee_name": emp.full_name,
				"company": emp.company,
				"rdo_code": "",
				"sensitivity_level": emp.sensitivity,
				"payroll_year": payroll_year,
				"tax_id": emp.tin,
				"date_hired": emp.date_hired,
				"from_date": None,
				"to_date": None,
				"has_prev":emp.has_prev,
				"total_yr_days": emp.total_yr_days,
				"no_hours": emp.no_hours,
				"rate": emp.rate,
				"rate_type": emp.rate_type,
				"location": emp.location,
				"mwe_loc": emp.mwe_loc,
				#TERMINATION DATES
				"date_terminated": emp.date_terminated,
				"date_resigned": emp.date_resigned,
				"date_retired": emp.date_retired,
				"date_contract_ended": emp.date_contract_ended,
				#STATUS
				"with_previous": 0,
				"is_terminated": 0,
				"minimum_wage": 0,
				#OTHER
				"factor": emp.total_yr_days,
				"per_day": 0,
				"per_month": 0,
				"per_year": 0,
				"anoa_label":"",
				"anob_label":"",
				"anoa_sp_label":"",
				"anob_sp_label":"",
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
				"pt_basic": 0.0,
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
				#DEMI
				"nt_conv": 0,
				"nt_med_cash": 0,
				"nt_rice":0,
				"nt_uniform":0,
				"nt_laundry":0,
				"nt_med_ast":0,	
				"total_conv": 0,				
				"total_med_cash": 0,
				"total_rice":0,
				"total_uniform":0,
				"total_laundry":0,
				"total_med_ast":0,
				"total_awards": 0,
				"total_gifts": 0,
				"total_prod": 0,
				"ex_conv": 0,
				"ex_med_cash": 0, 
				"ex_rice": 0,
				"ex_uniform": 0,
				"ex_med_ast": 0,
				"ex_laundry": 0, 
				"ex_awards": 0, 
				"ex_gifts": 0, 
				"ex_prod": 0,
				"excess_demi":0,
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
				"t_nightdiff": 0,
				"t_other_a": 0,
				"t_other_b": 0,
				"t_other_sa": 0,
				"t_other_sb": 0,
				#TOTALS
				"total_basic": 0,
				"total_holiday": 0,
				"total_overtime": 0,
				"total_nightdiff": 0,
				"total_contrib": 0,
				"total_benefits": 0,
				"total_demi": 0,
				"total_fees": 0,
				"total_hazard": 0,					
				"total_comm": 0,
				"total_sharing": 0,
				"total_housing": 0,
				"total_cola": 0,
				"total_tax": 0,
				"total_transpo": 0,		
				"total_represent": 0,		
				"total_other": 0,
				"total_other_a": 0,
				"total_other_b": 0,
				"total_other_sa": 0,
				"total_other_sb": 0,					
				"gross_compensation": 0,
				"total_benefits": 0,
				"non_taxable_total": 0,
				"taxable_total": 0,
				"tax_due": 0,
				"tax_withheld": 0,				
				"adj_amount_withheld": 0,
				"adj_over_withheld": 0,
				"adj_withheld": 0,
				"withheld_nov": 0,
				#PREVIOUS TOTALS
				"prev_withheld_nov": 0,
				"prev_tax_due": 0,
				"prev_tax_withheld": 0,
				"prev_adj_withheld": 0,
				"prev_gross_compensation": 0,
				"prev_total_benefits": 0,
				"prev_non_taxable_total": 0,
				"prev_taxable_total": 0,
			})
		)

	return emp_map