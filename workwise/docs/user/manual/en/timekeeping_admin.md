# Attendance Management Admin

Click **Attendance Management**, upon click below window will appear:

![](\docs\assets\img\hrp\ATTM.png)


## **Attendance Management Setup** ##

![](\docs\assets\img\hrp\setup.png)


### **Timekeeping Settings** ###
  - Timekeeping Settings is where you can set a policy that you want in Timekeeping.

### **Biometrics Upload** ###
- **Biometrics Upload** a manual upload of time logs.

**a.** To upload time logs, select **Biometrics Upload** from Biometrics.
Upon selection, below window will appear.

![](docs\assets\img\timekeeping\biometrics_select.png)

**b.** To select file to be upload, click **Browse** then select the file.

![](docs\assets\img\timekeeping\biometrics_select_001.png)

**c.** Upon selection, click **Attach** to upload the file. 

![](docs\assets\img\timekeeping\biometrics_attach.png)

**d.** Once the file was successfully uploaded. The below activity log will appear.

![](docs\assets\img\timekeeping\biometrics_attached.png)


### **Leave Balance** ###

**a.** To set **Leave Balance**, select **Leave Balance** from setup.

![](docs\assets\img\timekeeping\leave_balance.png)


**b.** From Leave Balance, click **New**.

![](docs\assets\img\timekeeping\leave_balance_new.png)

**c.** Upon click, below window will appear.

![](docs\assets\img\timekeeping\leave_balance_new_01.png)


**d.** To set Leave Balance, you need to setup the following:

![](docs\assets\img\timekeeping\leave_balance_new_1.png)

1. **Employee** - Employee ID number.
2. **From** - starting date of leave balance's validity.
3. **To** - ending date of leave balance's validity.
4. **Leave Type** - type of leave.
5. **Credits** - leave credits.
6. **Balance** - total unused leave credits.

**e.** Upon completion of data, click **Save** to save the Leave Balance.

![](docs\assets\img\timekeeping\leave_balance_save.png)


### **Leave Type** ###

**a.** To set **Leave Type**, select **Leave Type** from setup.

![](\docs\assets\img\hrp\LT.png)

**b.** From Leave Type, click **New**.

![](docs\assets\img\timekeeping\leave_type_new_001.png)

**c.** Upon click, below window will appear.

![](\docs\assets\img\hrp\LT2.png)

**d.** To set Leave Balance, you need to setup the following:


![](\docs\assets\img\hrp\ltsetup.png)

1. **Leave Name** - name of Leave Type.
2. **Leave Code** - code of Leave Type.
3. **Max Number of Days** - max number of days leave allowed to file.
4. **Days Before Filing** - number of days before the day of leave must file.
5. **Deduct To** - type of leave that will deduct the current leave.
6.  **Is Leave Without Pay** - tick box if leave is without pay.
7. **Is Carry Over** - tick box if leave will carry over on leave's anniversary date.
8. **Include Holidays** - tick box if holiday on the leave balance of the leave type is included.
9. **Allow Negative** - tick box if employee can file leave even in negative leave credits.
10. **Allow Beyond Max Days** - tick box if the leave type will allow to beyond on the max number of days setup.
11. **Female Only** - tick box if leave type is for female only.
12. **Male Only** - tick box if leave type is for male only.
13. **Married Only** - tick box if leave type is for married only.
14. **Solo Parent** - tick box if leave type is for solo parent only.
15. **Convertible** - tick box if leave type is convertible.
16. **Employment Status** - status of employee.

**e.** Upon completion of data, click **Save** to save the Leave Type.

![](docs\assets\img\timekeeping\leave_type_save.png)


### **Holiday** ###

**a.** To set **Holiday**, select **Holiday** from setup.

![](\docs\assets\img\hrp\Holiday.png)


**b.** From Holiday, click **New**.

![](docs\assets\img\timekeeping\holiday_new.png)

**c.** Upon click, below window will appear.

![](docs\assets\img\timekeeping\holiday_new_001.png)


**d.** To set Holiday, you need to setup the following:

![](docs\assets\img\timekeeping\holiday_new_002.png)

1. **Holiday Name** - name of holiday.
2. **Date** - date of holiday.
3. **Company** - select company name for the particular holiday.
4. **Location** - select location for the particular holiday.
5. **Special Non-Working** - tick box if the Holiday is special non-working.
6. **Description** - description of holiday.


### **Timekeeping Settings** ###

**a.** To set **Timekeeping Settings**, select **Timekeeping Settings** from setup.

![](\docs\assets\img\hrp\TKsettings.png)

**b.** To set Timekeeping Settings, you need to setup the following:

![](docs\assets\img\timekeeping\timekeeping_settings_001.png)

1. **OT Require Break Time** - If total Overtime hours is greater than OT Require Break Time Value, Break Time will be Required.
2. **Max Overtime Hours** - Max Overtime Hours allowed.
3. **Days to Require Medical Certificate** - If leave days is greater than or equal to value, medical certificate will be required.

**c.** Upon completion, click **Save** to save **Timekeeping Settings**.

![](docs\assets\img\timekeeping\timekeeping_settings_save.png)



## **Work Shift and Schedules** ##

### **Work Shift** ###


**a.** To create work Shift, select **Work Shift** from Work Shift and Schedules.

![](\docs\assets\img\hrp\workshift.png)


**b.** To add new, click **New**.

![](\docs\assets\img\timekeeping\work_shift_list.png)


**c.** Upon click **New**, below window will appear:

![](\docs\assets\img\timekeeping\workshift_set_up.png)


**d.** To have new **Work Shift**, you need to set up the following:

![](\docs\assets\img\timekeeping\workshift_define.png)

1. **Shift Name** - name of work shift.
2. **Company** - select company for the particular work shift.
3. **Shift Type** - automated based on work shift's First Half Start and Second Half End.
4. **First Half Start** - will be the first half time in of work shift.
5. **First Half End** - will be the first half time out of work shift.
6. **Second Half Start** - will be the second half time in of work shift.
7. **Second Half End** - will be the second half time out of work shift.
8. **Working Hours** - automated based on work shift's First Half Start and Second Half End.
9. **Break Start** - will be the Break time in of work shift.
10. **Break End** - will be the Break time out of work shift.
11. **Break Mins** - automated based on work shift's Break time in and out.
12. **Is Restday** - tick box if the work shift is Rest day.
13. **Is Flexible** - tick box if the work shift is Flexible, which is not calculating late but will calculate undertime if the particular day does not fulfill the required working hours.
14. **Ignore Late** - tick box if the work shift shall not consider late.
15. **Grace Period** - a period of time in minutes after consider as late.
16. **Break Time Grace  Period** - a period of time in minutes after consider as late on break time.
17. **Setup Pre-Shift** - hours before First Half Start will be the basis of range to read the time in based on time logs.
18. **Setup Post-Shift** - hours after Second Half End will be the basis of range to read the time out based on time logs.
19. **Night Diff Start** -the basis on when the Night Differential computation will start.
20. **Night Diff End** -the basis on when the Night Differential computation will end.

**e.** Once the Work Shift was already setup, you may now save the work shift by clicking **Save**.

![](\docs\assets\img\timekeeping\work_shift_done.png)

###To filter record###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.


## **Work Schedule Template** ##

**a.** To create Work Schedule Template, select **Work Schedule Template** from Work Shift and Schedules.

![](\docs\assets\img\hrp\worksched.png)

**b.** To add new, select **New**.

![](\docs\assets\img\timekeeping\work_sched_new.png)

**c.** Upon click **New**, below window will appear:

![](\docs\assets\img\timekeeping\work_sched_new_001.png)

**d.** To have new Template, you need to set up the following:

![](\docs\assets\img\timekeeping\work_sched_new_002.png)

1. **Template Name** - name of Template
2. **Company** - Select Company for the particular template.
3. **Monday - Sunday** - select work shift for every day schedule.

**e.** Upon completion of data, click **Save** to save the Work Schedule Template.

![](\docs\assets\img\timekeeping\work_sched_template_save.png)

### To filter record ###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.


## **Work Schedule Assignment** ##

**a.** To assign work schedule, select **Work Schedule Assignment** from Work Shift and Schedules.

![](\docs\assets\img\timekeeping\work_sched_assign_select.png)

**b.** Upon click **Work Schedule Assignment** below window will appear:

![](\docs\assets\img\timekeeping\work_sched_assign_new.png)

**c.** To assign work schedule, you need to setup the following:

![](\docs\assets\img\timekeeping\work_sched_assign_new-001.png)

1. **Apply Template** - select the Work Schedule Template.
2. **From** - starting date to assign schedule.
3. **To** - ending date to assign schedule.
4. **Company** - select the company for the particular schedule assignment.
5. **Filter Type** - filter by Department or Employee
6. **Filter Value** - it will be chosen depends on Filter Type.


**d.** Once the said fields were already setup, you may use the following button to select employees which will automatically list the employees on the table below:

![](\docs\assets\img\timekeeping\work_sched_assignment_add_employees.png)

1. **Add Employees** - this can use to add employees based on Filter Type and Filter Value.
2. **Get Subordinates** - this can use to add employees based on assigned Subordinates per user.
3. **Get Company** - this can use to get all the employees under the Company selected.  

**e.** Once all the set up has already set up, click **Assign Schedule** to assign the work schedule of every employee on the table list. It also provided **Activity Log** for the reference of Schedule Created.

![](\docs\assets\img\timekeeping\assigned_sched.png)



### Attendance Processing ###

**a.** To process the attendance, select **Attendance Processing** from Work Shift and Schedule.

![](docs\assets\img\timekeeping\attendance_processing.png)

**b.** Upon select, below window will appear.

![](docs\assets\img\timekeeping\attendance_processing_select.png)


**c.** To process, you need to setup the following:

![](docs\assets\img\timekeeping\attendance_processing_select_001.png)

1. **Payroll Period** - period to be process.
2. **Company** - name of company.
3. **Employee** - it is optional, this filter can be use if you want to process specific employee.


**d.** Once done, click **Process Attendance** to process the Attendance Management data. Once processed there will be **Activity Log** below for the reference of Attendance processed.

![](docs\assets\img\timekeeping\attendance_processing_process.png)
![](docs\assets\img\timekeeping\attendance_processing_activity.png)


## **Applications** ##

### **Leave Application** ###


**a.** To create Leave Application, select **Leave Application** from Applications.

![](\docs\assets\img\hrp\leave.png)

**b.** To add new, click **New**.

![](\docs\assets\img\timekeeping\leave_aaplication_new.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\timekeeping\leave_application_setup.png)


1. **Employee** - select employee.
2. **Leave type** - select particular leave type.
3. **Posting Date** - will be the filing date.
4. **From Date** - starting date of the application.
5. **To Date** - end date of the application.
6. **Total Leave Days** - automated based on Application's From and To Date.
7. **Current Leave Balance** - automated based on balance on Leave Balance Setup.
8. **Medical Certificate** - this attachment will be mandated on Sick Leave base on the Timekeeping Settings.
9. **Reason** - Reason of filing leave.
10. **Workflow State** - Current status of the Application.
11. **Owner** - the one who create the Application.

**d.** For Half Day Leave Setup, select the arrow down on child table,

![](\docs\assets\img\timekeeping\leave_application_save_001_001.png)

- **Type**
 1. **Whole Day** - if leave is on whole day.
 2. **2nd Half** - if leave is on 2nd half.
 3. **1st Half** - if leave is on 1st half.
 4. **Exclude** - if you want to exclude the particular date. 

- **Holiday** - automatically tick box based on Holiday Setup.


**e.** Upon creation of the Application below More Information will appear:

![](\docs\assets\img\timekeeping\leave_application_more_info.png)


1. **Is LWOP** - automatically tick box once the Leave Type is leave without pay.
2. **Is Blanket** - automatically tick box once the Leave Application created thru Blanket.
3. **From Balance** - the basis of the Leave Balance created for the particular employee and leave type.
4. **Company** - automated based on Employee's Company.

**f.** Upon completion of data, you may now save the Leave Application by clicking **Save**. The status will automatically update into **Pending**. On pending status the application was still allowed to edit and ready to have an action by Leave Approver.

![](\docs\assets\img\timekeeping\leave_application_save_002.png)
![](\docs\assets\img\timekeeping\leave_application_pending_002.png)

- Employee can **Discontinue** application from **Pending** Status, click **Discontinue** from **Actions**, the Application's Status will automatically update into **Discontinued**.

![](\docs\assets\img\timekeeping\leave_application_discontinue.png)
![](\docs\assets\img\timekeeping\leave_application_discontinue_0001.png)

- To **Continue** application from **Discontinued** Status, click **Continue** from **Actions**, the Application's Status will automatically update into **Pending**.

![](\docs\assets\img\timekeeping\leave_application_discontinue_0003.png)
![](\docs\assets\img\timekeeping\leave_application_discontinue_0002.png)



- To **Reject** application, click **Reject** from **Actions**, the Application's Status will automatically update into **Rejected**.

![](\docs\assets\img\timekeeping\leave_application_approve_002.png)
![](\docs\assets\img\timekeeping\leave_application_rejected.png)


- To **Unreject** application, click **Reject** under **Actions** button, the application's status will automatically update into **Pending**

![](\docs\assets\img\timekeeping\leave_application_intopending.png)


- To **Approve** application, click **Approve** from **Actions**, the Application's Status will automatically update into **Approved**. Once the Application is on **Approved**, the Application was not allowed to edit. 

![](\docs\assets\img\timekeeping\leave_application_approved.png)

- On **Approved** status, Approver can **Cancel** the application, the Application's Status will automatically update into **Cancelled**.

![](\docs\assets\img\timekeeping\leave_application_cancel.png)

![](\docs\assets\img\timekeeping\leave_application_cancelled.png)

-  On **Cancelled** status, Approver can **Amend** the application, to amend the application click **Amend**. From here, you can modify the application. The application's series will be link from the amended application. 

![](\docs\assets\img\timekeeping\leave_application_amend.png)
![](\docs\assets\img\timekeeping\leave_application_amended.png)


**g.** Once the Leave Application is approved, the Leave Balance will update.

![](\docs\assets\img\timekeeping\leave_balance_update.png)


### To filter record ###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.



### **Overtime Application** ###


**a.** To create Overtime Application, select **Overtime Application** from Applications.

![](\docs\assets\img\hrp\ot.png)

**b.** To add new, click **New**.

![](\docs\assets\img\timekeeping\overtime_new.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\otapp.png)

1. **Employee** - Employee ID Numbers	.
2. **Is Previous** - this feature use for shift that crossing to the next day. Tick box if the application's target date will base on from date.
3. **Posting Date** - date of overtime application posted.
4. **From** - from date of the application.
5. **To** - end date of the application.
6. **From Time** - from time of the application. 
7. **To Time** - end time of the application.
8. **Break Hours** - break hours of the overtime application, this can be mandated base on timekeeping settings.
9. **Reason** - reason of filing overtime application.
10. **Owner** - the one who created the application

**d.** Upon completion of data, you may now save the Overtime Application by clicking **Save**. The status will automatically update into **Pending**. On pending status the application was still allowed to edit and ready to have an action by Overtime Approver.

![](\docs\assets\img\hrp\otapp1.png)
![](\docs\assets\img\timekeeping\overtime_pending_0001.png)

- Employee can **Discontinue** application from **Pending** Status, click **Discontinue** from **Actions**, the Application's Status will automatically update into **Discontinued**.

![](\docs\assets\img\timekeeping\overtime_discontinue.png)
![](\docs\assets\img\timekeeping\overtime_discontinued.png)

- To **Continue** application from **Discontinued** Status, click **Continue** from **Actions**, the Application's Status will automatically update into **Pending**.

![](\docs\assets\img\timekeeping\overtime_continue.png)
![](\docs\assets\img\timekeeping\overtime_pending_0001.png)


- To **Reject** application, click **Reject** from **Actions**, the Application's Status will automatically update into **Rejected**.

![](\docs\assets\img\timekeeping\overtime_action.png)
![](\docs\assets\img\timekeeping\overtime_rejected.png)


- To **Unreject** application, click **Reject** under **Actions** button, the application's status will automatically update into **Pending**. 

![](\docs\assets\img\timekeeping\overtime_reject_pending.png)
![](\docs\assets\img\timekeeping\overtime_reject_pending_001.png)


- To **Approve** application, click **Approve** from **Actions**, the Application's Status will automatically update into **Approved**. Once the Application is on **Approved**, the Application was not allowed to edit. 

![](\docs\assets\img\timekeeping\overtime_approved.png)

- On **Approved** status, Approver can **Cancel** the application, the Application's Status will automatically update into **Cancelled**.

![](\docs\assets\img\timekeeping\overtime_cancel.png)
![](\docs\assets\img\timekeeping\overtime_cancelled.png)

-  On **Cancelled** status, Approver can **Amend** the application, to amend the application click **Amend**. From here, you can modify the application. The application's series will be link from the amended application. 

![](\docs\assets\img\timekeeping\overtime_amend.png)
![](\docs\assets\img\timekeeping\overtime_amended.png)


### To filter record ###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.



### **Official Business Application** ###

**a.** To create Official Business Application, select **Official Business Application** from Applications.

![](\docs\assets\img\hrp\ob.png)

**b.** To add new, click **New**.

![](\docs\assets\img\timekeeping\official_business_new.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\obapp1.png)
![](\docs\assets\img\hrp\obapp2.png)

1. **Employee** - Employee ID Number.
2. **Client Name** - name of Client.
3. **Posting Date** - the date of OB application posted.
4. **Reason** - reason of filing official business application.
5. **From** - starting date of application.
6. **To** - end date of application.
7. **From time** - starting time of application.
8. **To time** - end time of application.
9. **Attachment** - can attach file for proof of OB. (if there's any)
10. **Expense Items** - list of expense of items.
11. **Expense Amount** - total amount of expense items.
12. **Address** - client's address.
13. **Contact Person** - contact person on client.
14. **Owner** - the one who created application.


**d.** Additional Setup for not whole day application, click the **arrow down** of child table.

![](\docs\assets\img\timekeeping\official_business_new.png)

1. **Type** - type of application if **Whole Day**, **1st Half**, **2nd Half** or **Exclude**.
2. **From** - it will automated based on from and to time field below the table, it can also modify.
3. **Travel** - total minutes of Official Business Application.


**e.** Upon completion of data, you may now save the Overtime Application by clicking **Save**. The status will automatically update into **Pending**. On pending status the application was still allowed to edit and ready to have an action by Official Business Approver.

![](\docs\assets\img\hrp\obapp02.png)
![](\docs\assets\img\hrp\obapp002.png)

- Employee can **Discontinue** application from **Pending** Status, click **Discontinue** from **Actions**, the Application's Status will automatically update into **Discontinued**.

![](\docs\assets\img\timekeeping\offficial_business_discontinue.png)
![](\docs\assets\img\timekeeping\offficial_business_discontinued.png)

- To **Continue** application from **Discontinued** Status, click **Continue** from **Actions**, the Application's Status will automatically update into **Pending**.

![](\docs\assets\img\timekeeping\offficial_business_continue.png)
![](\docs\assets\img\timekeeping\official_business_pending.png)


- To **Reject** application, click **Reject** from **Actions**, the Application's Status will automatically update into **Rejected**.

![](\docs\assets\img\timekeeping\official_business_saved.png)
![](\docs\assets\img\timekeeping\official_business_rejected.png)


- To **Unreject** application, click **Reject** under **Actions** button, the application's status will automatically update into **Pending**. 

![](\docs\assets\img\timekeeping\official_business_rejecttopending.png)
![](\docs\assets\img\timekeeping\official_business_pending.png)


- To **Approve** application, click **Approve** from **Actions**, the Application's Status will automatically update into **Approved**. Once the Application is on **Approved**, the Application was not allowed to edit. 

![](\docs\assets\img\timekeeping\official_business_approved.png)

- On **Approved** status, Approver can **Cancel** the application, the Application's Status will automatically update into **Cancelled**.

![](\docs\assets\img\timekeeping\official_business_cancel.png)
![](\docs\assets\img\timekeeping\official_business_cancelled.png)

-  On **Cancelled** status, Approver can **Amend** the application, to amend the application click **Amend**. From here, you can modify the application. The application's series will be link from the amended application. 

![](\docs\assets\img\timekeeping\official_business_amend.png)
![](\docs\assets\img\timekeeping\official_business_amended1.png)


### To filter record ###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.


### **Change Schedule Application** ###

**a.** To create Change Schedule Application, select **Change Schedule Application** from Applications.

![](\docs\assets\img\hrp\changesched.png)

**b.** To add new, click **New**.

![](\docs\assets\img\timekeeping\change_schedule_new.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\changesched1.png)

1. **Date** - target date of change schedule.
2. **Employee** - Employee ID Number.
3. **Posting Date** - date of Change Schedule posted.
4. **Shift** - shift to be change from current shift.
5. **Remarks** - reason of filing change schedule application or any description of filing.
6. **Owner** - the one who created application.


**d.** Upon completion of data, you may now save the Change Schedule Application by clicking **Save**. The status will automatically update into **Pending**. On pending status the application was still allowed to edit and ready to have an action by Change Schedule Approver. The **Current Shift**, **Time In and Out** will automatically appear upon selection of date and employee.

![](\docs\assets\img\timekeeping\change_schedule_save.png)
![](\docs\assets\img\timekeeping\change_schedule_pending.png)

- Employee can **Discontinue** application from **Pending** Status, click **Discontinue** from **Actions**, the Application's Status will automatically update into **Discontinued**.

![](\docs\assets\img\timekeeping\change_schedule_discontinue.png)
![](\docs\assets\img\timekeeping\change_schedule_discontinued.png)

- To **Continue** application from **Discontinued** Status, click **Continue** from **Actions**, the Application's Status will automatically update into **Pending**.

![](\docs\assets\img\timekeeping\change_schedule_continue.png)
![](\docs\assets\img\timekeeping\change_schedule_pending.png)


- To **Reject** application, click **Reject** from **Actions**, the Application's Status will automatically update into **Rejected**.

![](\docs\assets\img\timekeeping\change_schedule_approve.png)
![](\docs\assets\img\timekeeping\change_schedule_rejected.png)


- To **Unreject** application, click **Reject** under **Actions** button, the application's status will automatically update into **Pending**. 

![](\docs\assets\img\timekeeping\change_schedule_unreject_001.png)
![](\docs\assets\img\timekeeping\change_schedule_pending.png)


- To **Approve** application, click **Approve** from **Actions**, the Application's Status will automatically update into **Approved**. Once the Application is on **Approved**, the Application was not allowed to edit. 

![](\docs\assets\img\timekeeping\change_schedule_approved_001.png)

- On **Approved** status, Approver can **Cancel** the application, the Application's Status will automatically update into **Cancelled**.

![](\docs\assets\img\timekeeping\change_schedule_cancel.png)
![](\docs\assets\img\timekeeping\change_schedule_cancelled.png)


-  On **Cancelled** status, Approver can **Amend** the application, to amend the application click **Amend**. From here, you can modify the application. The application's series will be link from the amended application. 

![](\docs\assets\img\timekeeping\change_schedule_amend.png)
![](\docs\assets\img\timekeeping\change_schedule_amended1.png)

### To filter record ###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.




### **Excuse Tardiness Application** ###

**a.** To create Excuse Tardiness Application, select **Excuse Tardiness Application** from Applications.

![](\docs\assets\img\hrp\excuse1.png)

**b.** To add new, click **New**.

![](\docs\assets\img\hrp\excusenew.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\excuse01.png)

![](\docs\assets\img\hrp\excuse001.png)

1. **Employee** - name of employee.
2. **Date** - date of excuse tardiness.
3. **Posting Date** - enter the date of Excuse Tardiness posted.
4. **Type** - choose type of Excuse Tardiness (Late or Undertime)
5. **From Time** - from time of application.
6. **To Time** - end time of application.
7. **Reason** - reason of application.
8. **Attachment** - can attach file if there's any.
9. **Owner** - the one who create the Application.


**d.** Upon completion of data, click **Save** to save the Excuse Tardiness Application.

![](\docs\assets\img\hrp\excusesave.png)


### **Undertime Application** ###

**a.** To create Undertime Application, select **Undertime Application** from Applications.

![](\docs\assets\img\hrp\undertime.png)

**b.** To add new, click **New**.

![](\docs\assets\img\hrp\utnew.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\ut01.png)

![](\docs\assets\img\hrp\ut001.png)

1. **Employee** - name of employee.
2. **Date** - date of Undertime Application.
3. **Posting Date** - enter the date of Undertime posted.
4. **From Time** - from time of application.
5. **To Time** - end time of application.
6. **Reason** - reason of application.
7. **Attachment** - can attach file if there's any.
8. **Owner** - the one who create the Application.


**d.** Upon completion of data, click **Save** to save the Undertime Application.


![](\docs\assets\img\hrp\ut02.png)

![](\docs\assets\img\hrp\ut002.png)


### **DTR Problem Application** ###

**a.** To create DTR Problem Application, select **DTR Problem Application** from Applications.

![](\docs\assets\img\hrp\dtr.png)

**b.** To add new, click **New**.

![](\docs\assets\img\hrp\dtrnew.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\excuse01.png)

![](\docs\assets\img\hrp\excuse001.png)

1. **Employee** - name of employee.
2. **Date** - date of excuse tardiness.
3. **Posting Date** - enter the date of Excuse Tardiness posted.
4. **Type** - choose type of Excuse Tardiness (Late or Undertime)
5. **From Time** - from time of application.
6. **To Time** - end time of application.
7. **Reason** - reason of application.
8. **Attachment** - can attach file if there's any.
9. **Owner** - the one who create the Application.


**d.** Upon completion of data, click **Save** to save the DTR Problem Application.

![](\docs\assets\img\hrp\dtrsave.png)


### **Compensatory Time Off** ###

**a.** To create Compensatory Time Off, select **Compensatory Time Off** from Applications.

![](\docs\assets\img\hrp\cto.png)

**b.** To add new, click **New**.

![](\docs\assets\img\hrp\ctonew.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\cto01.png)

1. **Employee** - name of employee.
2. **Type** - choose type of Compensatory Time Off.
3. **Posting Date** - enter the date of Excuse Tardiness posted.
4. **Owner** - the one who create the Application.


**d.** Upon completion of data, click **Save** to save the Compensatory Time Off.

![](\docs\assets\img\timekeeping\compen.png)

# Tools #


### **Blanket** ###

- **Blanket** can be use by manager to create multiple applications for multiple employees, this can be done without approval.

**a.** To create Blanket, select **Blanket** from Applications.

![](\docs\assets\img\hrp\blanket.png)

**b.** To add new, click **New**.

![](\docs\assets\img\timekeeping\blanket_new.png)

**c.** To have new Blanket, you need to set up the following:

![](\docs\assets\img\timekeeping\blanket_new_001.png)

1. **Application Type** - can be **Leave Application**, **Overtime Application** or **Official Business**.
2. **Location** - location of the employees.
3. **Posting Date** - filing date.
4. **Company** - company name.
5. **From Date** - starting date of blanket.
6. **To Date** - end date of blanket.
7. The **Date** automated based on **From** and **To Date** field below. **Type** can be **Whole Day**, **1st Half**, **2nd Half** or **Exclude**, this may apply on **Leave and Official Business Application**.
8. Select **Employee ID Number**, once the it was selected the **Employee Name** will automatically appear based on ID Number.

**d.** Upon completion of data, you may now save the Work Suspension by clicking **Save**. The status will automatically update into **Draft**. On draft status the application was still allowed to edit.

![](\docs\assets\img\timekeeping\blanket_save.png)
![](\docs\assets\img\timekeeping\blanket_draft.png)

**e.** To submit the application, click **Submit**. the Application's Status will automatically update into **Submitted**.

![](\docs\assets\img\timekeeping\blanket_submit.png)
![](\docs\assets\img\timekeeping\blanket_submitted.png)
     
### To filter record ###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.

- All application shall be **Approved** or **Submitted** to consider on Timekeeping up to Payroll processing.



### **Batch Approval** ###

**a.** To create Batch Approval, select **Batch Approval** from Tools.

![](\docs\assets\img\hrp\ba.png)

**b.** To add new, click **New**.

![](\docs\assets\img\hrp\banew.png)

**c.** To have new Application, you need to set up the following:

![](\docs\assets\img\hrp\bapp.png)

1. **Company** - Select a company name.
2. **Posting Date** - enter the date of application posted.
3. **Application Type** - select the type of application
4. **Employee** - select name of employee 
5. **From Date** - starting date of batch approval.
6. **To Date** - end date of batch approval.




**d.** Upon completion of data, you may now save the Batch Approval by clicking **Save**. The status will automatically update into **Draft**. 

![](\docs\assets\img\hrp\badraft.png)


**e.** To submit the application, click **Submit**. the Application's Status will automatically update into **Submitted**.

![](\docs\assets\img\hrp\basubmit.png)

![](\docs\assets\img\hrp\basubmit01.png)


### **Work Suspension** ###


**a.** To create Work Suspension, select **Work Suspension** from Applications.

![](\docs\assets\img\hrp\worksuspension.png)

**b.** To add new, click **New**.

![](\docs\assets\img\timekeeping\work_suspension_new.png)

**c.** To have new Work Suspension, you need to set up the following:

![](\docs\assets\img\timekeeping\work_suspension_new_002.png)

1. **Company** - name of company.
2. **From Date** - starting date of work suspension.
3. **To Date** end date of work suspension.
4. The **Apply to** can be **Location**, **Department** or **Employee** and **Apply Value** will depends on what you've select on **Apply to**.

**d.** Upon completion of data, you may now save the Work Suspension by clicking **Save**. The status will automatically update into **Draft**. On draft status the application was still allowed to edit.

![](\docs\assets\img\timekeeping\work_suspension_save_001.png)

**e.** To submit the application, click **Submit**. the Application's Status will automatically update into **Submitted**.

![](\docs\assets\img\timekeeping\work_suspension_submit.png)
![](\docs\assets\img\timekeeping\work_suspension_submitted.png)
     
### To filter record ###

**a.** Click **Add Filter** button.![](docs\assets\img\timekeeping\employee_company_6.png)

**b.** Upon click, new window will appear to add filter of the preferred field.
![](docs\assets\img\timekeeping\employee_company_7.png)

**c.** Click ![](docs\assets\img\timekeeping\employee_company_8.png) to appear items for selected field.

**d.** Click ![](docs\assets\img\timekeeping\employee_company_9.png) to remove filter.


### Timelogs Override ###

**a.** To Override Timelogs, select **Timelogs Override** from Tools.

![](\docs\assets\img\timekeeping\timelogs.png)


**c.** To Override Timelogs, you need to set up the following:

![](\docs\assets\img\timekeeping\timelogs1.png)

1. **Payroll Period** - select a payroll period.
2. **Employee** - select a name of employee.

**c.1** Upon setup the assigned schedule will appear in child table.

![](\docs\assets\img\timekeeping\timelogs2.png)

**c.2** Select a date or a work schedule that you want to override. Upon selection, set a date and time. 

![](\docs\assets\img\timekeeping\timelogs3.png)

**d.** Upon completion of data, click Override Timelogs to Override the timelogs.

![](\docs\assets\img\timekeeping\timelogs4.png)
![](\docs\assets\img\timekeeping\timelogs5.png)



## **Generation of Reports** ##

![](docs\assets\img\timekeeping\reports.png)


### **Attendance Summary** ###
 - **Attendance Summary** is a real time report where in the employee can view his/her timelogs and applications which are applied and approved without doing the attendance processing.
 - Report shows every tagging if **Undertime**, **Late**, **No In/No Out**, **Overtime**, **Leave**, **Absent** or **Holiday**.
 - To generate the report, you need to set the following filters:
 

![](docs\assets\img\timekeeping\timekeeping_reports_attendance_summary.png)

1. **Payroll Period** - period to generate.
2. **Employee** - Employee ID Number.
3. **Mins/Hr** - if time is in minutes/hours.
4. **Show Break Time** - tick if the break in and out column will display on reports. It can also hide by untick box.
5. **Show Approved OT** - tick if only approved Overtime will show.


### **Attendance Summary Processed** ###
- **Attendance Summary Processed** is a generated report based on processed attendance. It can be use for payroll purposes. Also, provided the total hours of **Working hours**, **Break**, **Late**, **Overtime** and **Undertime** below.
- To generate the report, you need to set the following filters:
 

![](docs\assets\img\timekeeping\timekeeping_reports_attendance_summary_processed.png)

![](docs\assets\img\timekeeping\total.png)

1. **Payroll Period** - period to generate.
2. **Company** - name of Company
3. **Employee** - Employee ID Number.
4. **Department** - name of department.


### **Employee Schedule** ###
- **Employee Schedule** is a report wherein the employee can generate the schedule of  every employee in a particular period.
- To generate the report, you need to set the following filters:

![](docs\assets\img\timekeeping\timekeeping_reports_employee_sched.png)

1. **Payroll Period** - period to generate.
2. **Employee** - Employee ID Number.


### **Leave Balance Report** ###
- **Leave Balance Report** is a report wherein can generate the balances of every leave type.


![](\docs\assets\img\hrp\leavereport.png)



### **Employee Tardiness Report** ###
- **Employee Tardiness Report** is a report wherein can generate the tardiness of employee.

### **Tardiness Summary Report** ###
- **Tardiness Summary Report** is a report wherein can generate the tardiness of employees by payroll period.


![](\docs\assets\img\hrp\tardisummary.png)


### **Overtime Summary Report** ###
- **Overtime Summary Report** is a report wherein can generate the overtime of employees.

![](\docs\assets\img\hrp\otsummary.png)

### **Official Business Summary Report** ###
- **Official Business Summary Report** is a report wherein can generate the Official Business of employees.

![](\docs\assets\img\hrp\obsummary.png)


### **Leave Summary Report** ###
- **Leave Summary Report** is a report wherein can generate the leave of employees.

![](\docs\assets\img\hrp\leavesummary.png)

### **Incomplete Attendance** ###
- **Incomplete Attendance Report** is a report wherein can generate the list of employees with incomplete attendance.

![](\docs\assets\img\hrp\incomplete.png)

### **Perfect Attendance** ###
- **Perfect Attendance** is a report wherein can generate the list of employees with complete attendance.

![](\docs\assets\img\hrp\perfect.png)