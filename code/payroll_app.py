"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

import streamlit as st
from payroll import build_payroll, load_employees, load_timesheet, payroll_export

st.title("Salt City Coffee — Weekly Payroll")
st.write(
    "Upload this week's **timesheet export**. The roster is loaded automatically. "
    "Check the totals, fix anything flagged, then download the file for the payroll provider."
)

roster = load_employees()
uploaded_file = st.file_uploader(
    "Upload weekly timesheet (CSV)",
    type=["csv"],
    key="timesheet",
)

if uploaded_file is not None:
    timesheet = load_timesheet(uploaded_file)
    payroll = build_payroll(timesheet, roster)

    payroll_date = payroll["payroll_date"].iloc[0] if len(payroll) > 0 else ""
    st.subheader(f"Pay period ending {payroll_date}")

    paid_employees = len(payroll[payroll["pay_type"] != "unmatched"])
    total_hours = payroll["hours_worked"].sum()
    total_pay = payroll["gross_pay"].sum()
    overtime_weeks = len(payroll[payroll["pay_type"] == "overtime"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Employees paid", paid_employees)
    with col2:
        st.metric("Total hours", round(float(total_hours), 2))
    with col3:
        st.metric("Total gross pay", f"${total_pay:,.2f}")
    with col4:
        st.metric("Overtime weeks", overtime_weeks)

    unmatched = payroll[payroll["pay_type"] == "unmatched"]
    if len(unmatched) > 0:
        unmatched_ids = ", ".join(unmatched["employee_id"])
        st.warning(
            f"{len(unmatched)} timesheet row(s) have an employee_id that is not on the roster: "
            f"{unmatched_ids}. They are NOT in the export — add them to HR's roster and re-upload."
        )
    else:
        st.success("All employees matched to the roster.")

    st.subheader("Payroll table")
    st.caption("Raw values on the left, computed columns on the right — nothing is overwritten.")
    st.dataframe(payroll)

    export = payroll_export(payroll)
    st.download_button(
        "Download payroll CSV for the provider",
        data=export.to_csv(index=False),
        file_name=f"payroll_{payroll_date}.csv",
        mime="text/csv",
        key="download",
    )
