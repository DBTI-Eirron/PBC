# Copyright (c) 2013, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, flt

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_columns(filters):
	columns = [{
		"fieldname":"employee",
		"label": _("Employee"),
		"fieldtype": "Data",
		"width": 160
	},{
		"fieldname":"employee_name",
		"label": _("Employee Name"),
		"fieldtype": "Data",
		"width": 160
	},{
		"fieldname":"department",
		"label": _("Department"),
		"fieldtype": "Data",
		"width": 160
	}]
	payroll_year = get_payroll_year(filters)
	year_division = get_division(filters,payroll_year[0])
	for date in year_division:
		columns.append({
		"fieldname":str(date['name']),
		"label": _(date['name']),
		"fieldtype": "Data",
		"width": 160
		})
	return columns

def get_data(filters):
	data = []
	rating_class = frappe.db.sql("""SELECT * FROM `tabRating Classification`""",as_dict=True)
	payroll_year = get_payroll_year(filters)
	for year in payroll_year:
		data.append({})
		data.append({"employee":"<b>"+str(year)+"</b>"})
		year_division = get_division(filters,year)
		start_date,end_date = get_year_start_end(filters,year)
		employee = frappe.db.sql("""SELECT DISTINCT AP.appraisee, AP.appraisee_name, AP.department, EM.date_hired FROM `tabAppraisal` AP INNER JOIN `tabEmployee` EM ON AP.appraisee = EM.`name` WHERE AP.company = %s AND AP.docstatus = 1 AND AP.from_date BETWEEN %s AND %s"""+add_filter(filters),(filters.company,start_date,end_date),as_dict=True)
		for emp in employee:
			row = {'employee':emp.appraisee,'employee_name':emp.appraisee_name,'department':emp.department}
			ee = 0
			for div in year_division:
				if filters.provi:
					if str(div['name']) == "3rd Month":
						from_date = emp.date_hired + relativedelta(months=+3)
						to_date = emp.date_hired + relativedelta(months=+3)
					else:
						from_date = emp.date_hired + relativedelta(months=+5)
						to_date = emp.date_hired + relativedelta(months=+5)
				six_months = date.today() + relativedelta(months=+6)
				average = frappe.db.sql("""SELECT AVG(total_score) as average FROM `tabAppraisal` WHERE company = %s AND docstatus = 1 AND appraisee = %s AND from_date BETWEEN %s AND %s""",(filters.company,emp.appraisee,getdate(div['from_date']),getdate(div['to_date'])),as_dict=True)	
				for rating in rating_class:
					if flt(average[0].average) >= flt(rating.rate_from) and flt(average[0].average) <= flt(rating.rate_to):
						if filters.rating:
							if rating.rating_equivalent == filters.rating:
								row.update({str(div['name']):rating.rating_equivalent})
								ee += 1
						else:
							row.update({str(div['name']):rating.rating_equivalent})
							ee += 1
			if ee > 0:
				data.append(row)
		# frappe.throw(_(data))
	return data

def get_division(filters,year):
	from_date1 = datetime.strptime(year+"-01-01",'%Y-%m-%d')
	to_date1 = datetime.strptime(year+"-06-30",'%Y-%m-%d')
	from_date2 = datetime.strptime(year+"-07-01",'%Y-%m-%d')
	to_date2 = datetime.strptime(year+"-12-31",'%Y-%m-%d')
	if filters.provi:
		result = [{'name':'3rd Month','from_date':from_date1,'to_date':to_date1},{'name':'5th Month','from_date':from_date2,'to_date':to_date2}]
	else:
		result = [{'name':'First Sem','from_date':from_date1,'to_date':to_date1},{'name':'Second Sem','from_date':from_date2,'to_date':to_date2}]
	return result
def get_year_start_end(filters,year):
	start_date = datetime.strptime(year+"-01-01",'%Y-%m-%d')
	end_date = datetime.strptime(year+"-12-31",'%Y-%m-%d')
	return start_date, end_date

def add_filter(filters):
	additional_filters = ""
	if filters.employee:
		additional_filters += "AND AP.appraisee = '"+filters.employee+"'"
	if filters.provi:
		additional_filters += "AND EM.employment_status = 'Probationary'"
	else:
		additional_filters += "AND EM.employment_status <> 'Probationary'"
	return additional_filters

def get_payroll_year(filters):
	if filters.payroll_year:
		return [filters.payroll_year]
	else:
		year_list = []
		year_dict = frappe.db.sql("""SELECT `name` FROM `tabPayroll Year`""",(),as_dict=True)
		for year in year_dict:
			year_list.append(year.name)
		return year_list
