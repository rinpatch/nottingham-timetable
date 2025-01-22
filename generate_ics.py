import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vRecur
from datetime import datetime, timedelta
import pytz
import re

# Academic year configuration
ACADEMIC_YEAR_START = datetime(2024, 9, 2)  # Monday of Week 1
ACADEMIC_YEAR = "2024/25"

def parse_time(time_str):
    """Convert time string (e.g. '9:00') to datetime.time object"""
    return datetime.strptime(time_str, '%H:%M').time()

def get_date_for_week(week_num, academic_year_start=ACADEMIC_YEAR_START):
    """Calculate the date for a given week number
    
    Args:
        week_num: Week number
        academic_year_start: First Monday of Week 1 (default: ACADEMIC_YEAR_START)
    
    Returns:
        datetime: Date of the Monday of the specified week
    """
    target_date = academic_year_start + timedelta(weeks=week_num-1)
    return target_date

def parse_table_row(cells, day_offset, cal, academic_year_start=ACADEMIC_YEAR_START):
    """Parse a single row from the timetable and create events
    
    Args:
        cells: List of table cells containing class information
        day_offset: Integer offset from Monday (0 = Monday, 1 = Tuesday, etc.)
        cal: Calendar object to add events to
        academic_year_start: First Monday of Week 1 (default: ACADEMIC_YEAR_START)
    """
    # Extract information from cells
    module_code = cells[0].text.strip()
    module_name = cells[1].text.strip()
    event_type = cells[2].text.strip()
    start_time = cells[5].text.strip()
    end_time = cells[6].text.strip()
    location = cells[8].text.strip()
    staff = cells[11].text.strip()
    weeks_text = cells[12].text.strip()
    
    # Parse weeks (e.g., "23-30, 32-35")
    week_ranges = weeks_text.split(',')
    
    # Map day offsets to iCalendar day abbreviations
    day_abbr = ['MO', 'TU', 'WE', 'TH', 'FR']
    
    for week_range in week_ranges:
        start, end = map(int, week_range.strip().split('-'))
        
        # Create a single event with a repeating rule for the current range of weeks
        event = Event()
        event.add('summary', f"{module_name} ({event_type})")
        
        # Calculate event date and time for the first occurrence in this range
        base_date = get_date_for_week(start, academic_year_start)
        event_date = base_date + timedelta(days=day_offset)
        
        # Set start and end times
        start_dt = datetime.combine(event_date, parse_time(start_time))
        end_dt = datetime.combine(event_date, parse_time(end_time))
        
        # Convert to UTC
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        start_dt = malaysia_tz.localize(start_dt)
        end_dt = malaysia_tz.localize(end_dt)
        
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('location', location)
        event.add('description', f"Module: {module_code}\nStaff: {staff}\nAcademic Year: {ACADEMIC_YEAR}")
        
        event.add('rrule', {
            'freq': 'WEEKLY',
            'interval': 1,
            'count': end - start + 1,
            'byday': day_abbr[day_offset]
        })
        
        cal.add_component(event)

def parse_day_table(table, day_offset, cal, academic_year_start=ACADEMIC_YEAR_START):
    """Parse a single day's table and add events to the calendar
    
    Args:
        table: BeautifulSoup table element containing the day's schedule
        day_offset: Integer offset from Monday (0 = Monday, 1 = Tuesday, etc.)
        cal: Calendar object to add events to
        academic_year_start: First Monday of Week 1 (default: ACADEMIC_YEAR_START)
    """
    # Process each row in the table
    rows = table.find_all('tr')[1:]  # Skip header row
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 12:  # We need at least these many columns
            continue
            
        parse_table_row(cells, day_offset, cal, academic_year_start)

def create_ics(academic_year_start=ACADEMIC_YEAR_START):
    """Create an ICS file from the timetable
    
    Args:
        academic_year_start: First Monday of Week 1 (default: ACADEMIC_YEAR_START)
    """
    url = "http://timetablingunmc.nottingham.ac.uk:8016/reporting/TextSpreadsheet;programme+of+study;id;UG/M1059/M6UCMPSC/F/02%0D%0A?days=1-5&weeks=23-30;32-35&periods=3-20&template=SWSCUST+programme+of+study+TextSpreadsheet&height=100&week=100"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//UNMC Timetable//EN')
    cal.add('version', '2.0')
    
    # Map day names to numbers (0 = Monday)
    day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4}
    
    # Find all day headers and their corresponding tables
    day_headers = soup.find_all('p', string=lambda s: s and s.strip() in day_map.keys())
    
    for day_header in day_headers:
        day_name = day_header.text.strip()
        day_offset = day_map[day_name]
        
        # Get the table that follows this day header
        table = day_header.find_next('table')
        if not table:
            continue
            
        parse_day_table(table, day_offset, cal, academic_year_start)
    
    # Write to file
    with open('unmc_timetable.ics', 'wb') as f:
        f.write(cal.to_ical())
    print(f"Calendar file created successfully for academic year {ACADEMIC_YEAR}!")

if __name__ == "__main__":
    create_ics()
