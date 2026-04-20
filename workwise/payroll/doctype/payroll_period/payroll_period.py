# -*- coding: utf-8 -*-
# Copyright (c) 2017, HDI Systech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
import calendar
import time
from time import strptime
from frappe import msgprint, _
from frappe.model.naming import make_autoname
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, comma_or, get_fullname, nowdate, getdate
from frappe.model.document import Document


class PayrollPeriod(Document):
    def autoname(self):
        # pay_year = getdate(self.payroll_date).strftime("%Y")
        pay_year = self.payroll_year
        from_year = getdate(self.from_date).strftime("%Y")
        from_month = getdate(self.from_date).strftime("%b")
        from_day = getdate(self.from_date).strftime("%d")
        to_year = getdate(self.to_date).strftime("%Y")
        to_month = getdate(self.to_date).strftime("%b")
        to_day = getdate(self.to_date).strftime("%d")
        abbr = frappe.get_value("Company", self.company, "abbr")
        if self.period_group:
            self.name = from_month+""+from_day+" "+to_month+"" + \
                to_day+" - "+self.period_group+" - "+abbr+pay_year
        else:
            self.name = from_month+""+from_day+" "+to_month+""+to_day+" - "+abbr+pay_year

    def validate(self):
        self.validate_days()
        self.validate_frequency()
        self.validate_approval_cutoff()
        self.validate_period_group()
        self.validate_payroll_period()

    def validate_payroll_period(self):
        validate_payroll_date = frappe.db.get_single_value(
            'Payroll Settings', 'validate_payroll_date')
        if getdate(self.payroll_date) <= getdate(self.attendance_from) and validate_payroll_date:
            frappe.throw(
                _("Payroll Date should be higher than the cut-off dates."))
        if getdate(self.payroll_date) <= getdate(self.attendance_to) and validate_payroll_date:
            frappe.throw(
                _("Payroll Date should be higher than the cut-off dates."))

    def validate_approval_cutoff(self):
        if getdate(self.approval_cutoff) <= getdate(self.attendance_to):
            frappe.throw(
                _("Last Cutoff Date of Approval should be greater than To Date"))

    def validate_frequency(self):
        if self.schedule == "Monthly" and not self.is_special:
            self.frequency = "2nd"
            frappe.msgprint(
                "Frequency Changed to ( 2nd ) because Schedule was set to Monthly")

        if self.schedule != "Weekly":
            if self.frequency == "3rd" or self.frequency == "4th" or self.frequency == "5th":
                self.frequency = "2nd"
                frappe.msgprint(
                    "Frequency Changed to ( 2nd ) because (3rd 4th 5th) is not allowed for Monthly and Semi-Monthly")

        if self.schedule == "Weekly":
            if not self.weekly_set:
                frappe.throw(_("Weekly Set is Required if Weekly Schedule"))

            self.validate_duplicate_set()

        if self.is_special:
            if self.frequency != "Special":
                frappe.throw(_(str("Frequency must be Special")))

        if self.frequency == "Special":
            self.is_special = 1

    def validate_duplicate_set(self):
        duplicate = frappe.db.sql(""" SELECT `name` FROM `tabPayroll Period` 
			WHERE name != %s AND company = %s AND frequency = %s AND weekly_set = %s AND schedule = "Weekly" """, (self.name, self.company, self.frequency, self.weekly_set), as_dict=1)
        if duplicate:
            frappe.throw(_("{0} Frequency already exist in {1} Weekly Set").format(
                self.frequency, self.weekly_set))

    def validate_period_group(self):
        strict_pg = frappe.db.get_single_value(
            'Payroll Settings', 'strict_period_group')
        if strict_pg:
            if not self.period_group:
                frappe.throw(
                    "Period Group is Required for Strict use of Period Group")

        if self.period_group and self.schedule == "Weekly":
            if self.weekly_set:
                wkpg = frappe.db.get_value(
                    "Weekly Set", self.weekly_set, "period_group")
                if not wkpg:
                    frappe.throw(
                        _("Period Group for Weekly Set is required if Period Group is set"))
                else:
                    if wkpg != self.period_group:
                        frappe.throw(_("Invalid Weekly Set {0}, Weekly Set is for Period Group {1}").format(
                            self.weekly_set, wkpg))

        if self.weekly_set and not self.period_group:
            wkpg_x = frappe.db.get_value(
                "Weekly Set", self.weekly_set, "period_group")
            if wkpg_x:
                frappe.throw(
                    _("Period Group is required for Weekly Set with Period Group"))

    def validate_days(self):
        if not self.is_special:
            difference = date_diff(self.to_date, self.from_date)
            difference += 1
            if self.schedule == "Monthly":
                if not difference > 27:
                    frappe.throw(
                        _("Monthly Schedule Should be Greater than {0} days ").format(difference))
            if difference > 31:
                frappe.throw("Days Should not be Greater than 31 days ")

            if self.schedule == "Weekly":
                if difference > 7:
                    frappe.throw(
                        "Days Should not be Greater than 7 days for Weekly Period")

    def remove_payslips(self):
        log = frappe.new_doc("Payroll Process Logs")
        log.update({
            "user_id": frappe.session.user,
            "datetime": frappe.utils.now(),
            "remarks": "Payroll Period " + self.name + " Deleted Payslips",
        })
        if log.insert():
            frappe.db.sql(""" DELETE FROM `tabMy Payslip` WHERE payroll_period = %(period)s """, {
                "period": self.name,
            }, as_dict=True)

            msgprint("Payslips DELETED")

    def get_leave_balance(self, balances, leave_type, emp):
        balance_dict = []
        for lt in leave_type:
            valid_entry = {}
            less_entry = {}
            add, less, total_balance = 0, 0, 0
            min_date = None
            for d in balances:
                if d.employee == emp and (d.leave_type == lt.name or d.deduct_credits_to == lt.name):
                    if d.balance_type == "Add":
                        if lt.name == d.leave_type:
                            if d.name not in valid_entry:
                                valid_entry[d.name] = {
                                    "credits": d.credits,
                                    "from": getdate(d.from_date),
                                    "to": getdate(d.to_date),
                                }
                    else:
                        if d.deduct_credits_to == lt.name:
                            if d.name not in less_entry:
                                less_entry[d.name] = {
                                    "used": 0,
                                    "credits": d.credits,
                                    "from": getdate(d.from_date),
                                    "to": getdate(d.to_date),
                                }

            for vl in valid_entry:
                to_less = 0
                for le in less_entry:
                    if valid_entry[vl]['credits'] > 0 and not less_entry[le]['used']:
                        if (valid_entry[vl]['from'] <= less_entry[le]['from'] <= valid_entry[vl]['to']) or (valid_entry[vl]['from'] <= less_entry[le]['to'] <= valid_entry[vl]['to']):
                            to_less += less_entry[le]['credits']
                            less_entry[le]['used'] = 1
                valid_entry[vl]['credits'] -= to_less
                if (valid_entry[vl]['from'] <= getdate(self.to_date) <= valid_entry[vl]['to']) or (valid_entry[vl]['from'] <= getdate(self.to_date) <= valid_entry[vl]['to']):
                    total_balance += valid_entry[vl]['credits']

            if total_balance <= 0:
                total_balance = 0
            balance_dict.append({
                "leave_type": lt.name,
                "balance": total_balance
            })

        return balance_dict

    def make_payslips(self):

        # Validation: period must be closed before generating payslips
        if self.status == "Open":
            frappe.throw("Please Close Period Before Creating Payslips")

        # Log the request in Process Logs for audit trail
        log = frappe.new_doc("Payroll Process Logs")
        log.update({
            "user_id": frappe.session.user,
            "datetime": frappe.utils.now(),
            "remarks": "Payroll Period " + self.name + " — Payslip generation queued",
        })
        log.insert(ignore_permissions=True)
        frappe.db.commit()

        # Enqueue the heavy lifting as a background job in the 'long' queue
        # This returns immediately; the user does not wait for payslip creation
        frappe.enqueue(
            "workwise.payroll.doctype.payroll_period.payroll_period.run_make_payslips",
            queue="long",
            timeout=3600,
            period_name=self.name,
        )


def run_make_payslips(period_name):
    # ── Initialize logger for this background job ────────────────────────────────
    # Note: allow_site/max_size/file_count not supported in older Frappe versions
    logger = frappe.logger("payroll_period")
    logger.info(
        "=== run_make_payslips START | period: {0} ===".format(period_name))

    try:
        period = frappe.get_doc("Payroll Period", period_name)

        # ── STEP 1: Delete existing payslips for this period ──────────────────────
        # We delete old payslips to regenerate the full payroll for the period
        # This ensures corrections/removals from the Register are reflected
        logger.info(
            "Deleting existing payslips for period: {0}".format(period_name))
        frappe.db.sql(
            "DELETE FROM `tabMy Payslip` WHERE payroll_period = %(period)s",
            {"period": period_name},
        )
        frappe.db.commit()
        logger.info(
            "Existing payslips deleted for period: {0}".format(period_name))

        # ── STEP 2: Load reference data once (avoid N+1 queries) ──────────────────
        # Fetch all Leave Type names to populate leave balances in payslips
        logger.info("Loading Leave Types for balance calculation...")
        leave_type = frappe.db.sql(
            "SELECT `name` FROM `tabLeave Type`", as_dict=True)
        logger.info(
            "Leave Types loaded: {0} types found.".format(len(leave_type)))

        # ── STEP 3: Load Leave Balance (LB Entry) scoped to the period's date range
        # OPTIMIZATION: Only fetch LB Entry rows that potentially overlap with this period.
        # This avoids loading the entire LB Entry table, which can be tens of thousands of rows.
        # Condition: (from_date <= period.to_date AND to_date >= period.from_date) OR dates are NULL
        logger.info(
            "Loading Leave Balance entries for period {0} ({1} to {2})...".format(
                period_name, period.from_date, period.to_date
            ))
        balances = frappe.db.sql(
            """SELECT * FROM `tabLB Entry`
			   WHERE (from_date <= %(to_date)s AND to_date >= %(from_date)s)
				  OR from_date IS NULL OR to_date IS NULL""",
            {"from_date": period.from_date, "to_date": period.to_date},
            as_dict=True,
        )
        logger.info(
            "Leave Balance entries loaded: {0} entries.".format(len(balances)))

        # ── STEP 4: Fetch eligible employees from Payroll Register ────────────────
        # Only include employees who have a Payroll Register entry for this period
        # and are not on hold. Sort by last_name, first_name for consistency.
        logger.info(
            "Fetching eligible employees for period: {0}...".format(period_name))
        employees = frappe.db.sql(
            """SELECT `name`, full_name, location, company, sss_no, phic_no, hdmf_no, tin, user_id
			   FROM `tabEmployee`
			   WHERE `name` IN (
				   SELECT employee FROM `tabPayroll Register` WHERE period = %s
			   ) AND on_hold != 1
			   ORDER BY last_name, first_name""",
            period_name,
            as_dict=True,
        )
        logger.info(
            "Employees found (eligible for period): {0}".format(len(employees)))

        created_count = 0
        error_count = 0
        batch_size = 10  # Commit every N payslips to avoid holding transaction locks too long

        # ── STEP 5: Process each employee and generate their payslip ──────────────
        for idx, emp in enumerate(employees, start=1):
            logger.info(
                "[{0}/{1}] Processing employee: {2} ({3})".format(
                    idx, len(employees), emp.name, emp.full_name
                ))

            try:
                # Fetch payroll register entries for this employee in this period
                register = frappe.db.sql(
                    """SELECT PRE.*, PR.on_hold, PR.posting_date, PR.net_payroll,
						  PR.total_deduction, PR.total_income
				   FROM `tabPayroll Register` PR
				   INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
				   WHERE PR.period = %(period)s AND PR.employee = %(employee)s""",
                    {"period": period_name, "employee": emp.name},
                    as_dict=True,
                )

                if not register:
                    logger.info(
                        "[{0}/{1}] No register entries for employee {2}, skipping.".format(
                            idx, len(employees), emp.name
                        ))
                    continue

                # Fetch company defaults (letter head) once per employee
                letter_head = frappe.db.get_value(
                    "Company", emp.company, "default_letter_head")

                # Fetch loan information from Payroll Register Entries
                # DESIGN: Use period.payroll_date which is the official date for this payroll batch.
                # This ensures all loan payment counts are consistent with the payroll period context.
                logger.info(
                    "[{0}/{1}] Fetching loan entries for employee {2}...".format(
                        idx, len(employees), emp.name
                    ))
                loan = frappe.db.sql(
                    """SELECT PRE.pay_code, LA.unpaid_amount, LA.total_loan, LA.paid_amount,
				   (SELECT COUNT(`name`) FROM `tabLoan Application Payments`
					WHERE parent = PRE.linked_document
					  AND payment_status = 'Paid'
					  AND payment_date <= %(pdate)s) AS count
				   FROM `tabPayroll Register` PR
				   INNER JOIN `tabPayroll Register Entries` PRE ON PRE.parent = PR.`name`
				   INNER JOIN `tabLoan Application` LA ON LA.name = PRE.linked_document
				   WHERE PRE.entry_type = 'Loan'
					 AND PR.period = %(period)s
					 AND PR.employee = %(employee)s""",
                    {"pdate": period.payroll_date,
                     "period": period_name, "employee": emp.name},
                    as_dict=True,
                )

                # Calculate leave balances for this employee
                leaves = period.get_leave_balance(
                    balances, leave_type, emp.name)

                # Create new My Payslip document with employee and company info
                ps = frappe.new_doc("My Payslip")
                ps.update({
                    "owner": emp.user_id,
                    "employee": emp.name,
                    "payroll_period": period_name,
                    "employee_name": emp.full_name,
                    "company": emp.company,
                    "sss_no": emp.sss_no,
                    "phic_no": emp.phic_no,
                    "hdmf_no": emp.hdmf_no,
                    "tin": emp.tin,
                })

                # Append loan child table rows
                for ln in loan:
                    ps.append("loan", {
                        "loan_type": ln.pay_code,
                        "number_payment": ln.count,
                        "paid_amount": ln.paid_amount,
                        "loan_amount": ln.total_loan,
                        "outstanding_balance": ln.unpaid_amount,
                    })

                # Append leave child table rows (only if balance > 0)
                for lv in leaves:
                    if lv['balance'] > 0:
                        ps.append("leave", {
                            "leave_type": lv['leave_type'],
                            "leave_balance": lv['balance'],
                        })

                # Initialize accumulator variables for payslip totals
                payroll_date = ""
                net_payroll = 0
                total_incomes = 0
                total_deductions = 0

                # Iterate through payroll register entries and populate payslip tables
                for d in register:
                    if d.pay_type == "Income":
                        ps.append("payslip_incomes", {
                            "description": d.pay_description,
                            "amount": d.amount,
                            "pay_time": d.pay_time,
                        })
                    elif d.pay_type == "Deduction":
                        ps.append("payslip_deductions", {
                            "description": d.pay_description,
                            "amount": d.amount,
                            "pay_time": d.pay_time,
                        })

                    # Capture totals from the register
                    payroll_date = d.posting_date
                    net_payroll = d.net_payroll
                    total_incomes = d.total_income
                    total_deductions = d.total_deduction

                # Set final totals and header info
                ps.update({
                    "payroll_date": payroll_date,
                    "letter_head": letter_head,
                    "net_payroll": net_payroll,
                    "total_income": total_incomes,
                    "total_deduction": total_deductions,
                })

                # Insert the payslip
                # DESIGN: ignore_permissions=True is intentional here because:
                #   1. This is a system-initiated batch process, not a user-driven action
                #   2. The background worker runs as the system ("Administrator"), not the original user
                #   3. We want to guarantee payslips are created even if user roles restrict direct insert
                #   4. This is similar to system-generated documents (e.g., auto-invoices, system notes)
                ps.insert(ignore_permissions=True)

                created_count += 1
                logger.info("[{0}/{1}] Payslip inserted for employee {2}.".format(
                    idx, len(employees), emp.name
                ))

                # Batch commit every N employees to avoid holding transaction locks too long
                # This is especially important for large payrolls (>100 employees)
                if idx % batch_size == 0:
                    frappe.db.commit()
                    logger.info(
                        "[{0}/{1}] Batch commit after {2} payslips.".format(
                            idx, len(employees), batch_size
                        ))

            except Exception:
                error_count += 1
                logger.error(
                    "[{0}/{1}] Error processing employee {2}:\n{3}".format(
                        idx, len(employees), emp.name, frappe.get_traceback()
                    )
                )
                # Continue to next employee rather than aborting the entire batch
                # This allows partial completion if one employee has bad data
                continue

        # Final commit for any remaining payslips
        frappe.db.commit()

        # ── STEP 6: Log completion summary ────────────────────────────────────────
        summary_msg = (
            "=== run_make_payslips COMPLETE | period: {0} | "
            "created: {1} | errors: {2} ==="
        ).format(period_name, created_count, error_count)
        logger.info(summary_msg)

        # Write a final completion log entry visible in Frappe UI
        finish_log = frappe.new_doc("Payroll Process Logs")
        finish_log.update({
            "user_id": "Administrator",
            "datetime": frappe.utils.now(),
            "remarks": (
                "Payroll Period {0} — Payslips Created: {1}, Errors: {2}"
            ).format(period_name, created_count, error_count),
        })
        finish_log.insert(ignore_permissions=True)
        frappe.db.commit()

    except Exception:
        logger.error(
            "Fatal error in run_make_payslips for period {0}:\n{1}".format(
                period_name, frappe.get_traceback()
            )
        )
        # Rollback any partial changes if the process fails at the DB level
        frappe.db.rollback()
        raise
