from urllib.parse import urlparse
from datetime import datetime
import streamlit as st
import timetable_parser


@st.cache_data
def fetch_class_options(url):
    """Fetch available classes from the timetable URL."""
    classes = timetable_parser.get_available_classes(url)
    # Sort classes alphabetically by module name
    classes.sort(key=lambda x: x.split(" - ")[1])
    return classes


def validate_url(url):
    """Validate the URL is a valid UNMC timetable URL in list view.
    We don't check the port number, as it seems it's different for different years
    (i.e 23/24 is 8006, 24/25 is 8016) """
    parsed_url = urlparse(url)
    return (parsed_url.netloc.split(":")[0] == "timetablingunmc.nottingham.ac.uk"
            and parsed_url.path.startswith("/reporting/TextSpreadsheet"))


def render_page():
    st.set_page_config(
        page_title="UNMC Timetable to ICS Converter", page_icon=":calendar:")
    st.title("UNMC Timetable to ICS Converter")

    st.info("""
    ### How to use:
    1. Go to your timetable on the UNMC timetabling website
    2. Select list view
    3. Paste the URL into the input field above
    4. Select the start date of the academic year (week 1, undegraduates start studying at week 4)
    5. Click "Generate Calendar"
    6. Download and import the ICS file into your preferred calendar application
    """)

    # Input fields
    timetable_url = st.text_input(
        "Timetable URL",
        placeholder="i.e http://timetablingunmc.nottingham.ac.uk:8016/reporting/TextSpreadsheet;programme+of+study;id;..."
    )

    academic_year_start = st.date_input(
        "Week 1 start date (Undergraduates start studying at week 4)", datetime(2024, 9, 2))

    if timetable_url and validate_url(timetable_url):
        class_options = fetch_class_options(timetable_url)
        # Allow user to select classes using pills
        selected_classes = st.pills(
            "Classes to include", class_options, selection_mode="multi", default=class_options)

        if st.button("Generate Calendar"):
            # Define a filter function
            def class_filter(module_code, module_name, _event_type):
                return f"{module_code} - {module_name}" in selected_classes

            # Generate the calendar
            calendar_data = timetable_parser.create_ics(
                timetable_url, academic_year_start, class_filter=class_filter)

            # Create a download button
            st.download_button(
                label="Download ICS File",
                data=calendar_data,
                file_name="unmc_timetable.ics",
                mime="text/calendar"
            )

            st.success(
                "Calendar generated successfully! Click the download button above to save it.")
    elif timetable_url:
        st.error(
            "Please make sure the timetable is in list view and the URL is from timetablingunmc.nottingham.ac.uk")


render_page()
