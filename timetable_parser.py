import os
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
import pytz

# Timeout in seconds, default to 10 if not set
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))


def parse_time(time_str):
    """convert time string (e.g. '9:00') to datetime.time object"""
    return datetime.strptime(time_str, '%H:%M').time()


def get_date_for_week(week_num, academic_year_start):
    """Calculate the date for a given week number

    Args:
        week_num: Week number
        academic_year_start: First Monday of Week 1

    Returns:
        datetime: Date of the Monday of the specified week
    """
    target_date = academic_year_start + timedelta(weeks=week_num-1)
    return target_date


def parse_table_row(cells, day_offset, cal, academic_year_start, class_filter=None):
    """Parse a single row from the timetable and create events

    Args:
        cells: List of table cells containing class information
        day_offset: Integer offset from Monday (0 = Monday, 1 = Tuesday, etc.)
        cal: Calendar object to add events to
        academic_year_start: First Monday of Week 1
        class_filter: Optional function to filter classes
    """
    # Extract information from cells
    module_code = cells[0].text.strip()
    module_name = cells[1].text.strip()
    event_type = cells[2].text.strip()
    size = cells[3].text.strip()
    start_time = cells[5].text.strip()
    end_time = cells[6].text.strip()
    location = cells[8].text.strip()
    staff = cells[11].text.strip()
    weeks_text = cells[12].text.strip()

    # Check if the class should be included
    if class_filter and not class_filter(module_code, module_name, event_type):
        return

    # Parse weeks (e.g., "23-30, 32-35")
    week_ranges = weeks_text.split(',')

    # Map day offsets to iCalendar day abbreviations
    day_abbr = ['MO', 'TU', 'WE', 'TH', 'FR']

    for week_range in week_ranges:
        start, end = 0, 0
        if '-' in week_range:
            start, end = map(int, week_range.strip().split('-'))
        else:
            start = end = int(week_range.strip())

        # Create a single event with a repeating rule for the current range of weeks
        event = Event()
        event.add('summary', f"{module_name} ({event_type})")

        # Calculate event date and time for the first occurrence in this range
        base_date = get_date_for_week(start, academic_year_start)
        event_date = base_date + timedelta(days=day_offset)

        # Set start and end times
        start_dt = datetime.combine(event_date, parse_time(start_time))
        end_dt = datetime.combine(event_date, parse_time(end_time))

        # Specify timezone
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        start_dt = malaysia_tz.localize(start_dt)
        end_dt = malaysia_tz.localize(end_dt)

        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('location', location)
        event.add('description', f"Module: {
                  module_code}\nStaff: {staff}\nSize: {size}")

        event.add('rrule', {
            'freq': 'WEEKLY',
            'interval': 1,
            'count': end - start + 1,
            'byday': day_abbr[day_offset]
        })

        cal.add_component(event)


def parse_day_table(table, day_offset, cal, academic_year_start, class_filter=None):
    """Parse a single day's table and add events to the calendar

    Args:
        table: BeautifulSoup table element containing the day's schedule
        day_offset: Integer offset from Monday (0 = Monday, 1 = Tuesday, etc.)
        cal: Calendar object to add events to
        academic_year_start: First Monday of Week 1 (default)
        class_filter: Optional function to filter classes
    """
    # Process each row in the table
    rows = table.find_all('tr')[1:]  # Skip header row
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) != 13:
            raise ValueError(
                "Invalid timetable format: Missing columns in row")

        parse_table_row(cells, day_offset, cal,
                        academic_year_start, class_filter)


def create_ics(url, academic_year_start, class_filter=None):
    """Create an ICS file from the timetable

    Args:
        url: The timetable URL
        academic_year_start: First Monday of Week 1
        class_filter: Optional function to filter classes
    """
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//UNMC Timetable//EN')
    cal.add('version', '2.0')

    # Map day names to numbers (0 = Monday)
    day_map = {'Monday': 0, 'Tuesday': 1,
               'Wednesday': 2, 'Thursday': 3, 'Friday': 4}

    # Find all day headers and their corresponding tables
    day_headers = soup.find_all(
        'p', string=lambda s: s and s.strip() in day_map)

    for day_header in day_headers:
        day_name = day_header.text.strip()
        day_offset = day_map[day_name]

        # Get the table that follows this day header
        table = day_header.find_next('table')
        if not table:
            continue

        parse_day_table(table, day_offset, cal,
                        academic_year_start, class_filter)

    return cal.to_ical()


def get_available_classes(url):
    """Fetch the timetable and extract available classes

    Args:
        url: The timetable URL

    Returns:
        List of available classes in the format "Module Code - Module Name"
    """
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    soup = BeautifulSoup(response.text, 'html.parser')

    class_options = set()
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 12:
                continue
            module_code = cells[0].text.strip()
            module_name = cells[1].text.strip()
            class_options.add(f"{module_code} - {module_name}")

    return list(class_options)
