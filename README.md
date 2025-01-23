# UNMC Timetable to ICS Converter

A web application that converts University of Nottingham Malaysia Campus timetables into ICS calendar files. This allows students to easily import their class schedules into their preferred calendar applications (Google Calendar, Apple Calendar, Outlook, etc.).

## Features

- Converts UNMC timetable to ICS format
- Allows selection of specific classes to include/exclude
- Handles recurring events with proper Malaysia time zone

## How to Use

1. Visit the [UNMC timetabling website](http://timetablingunmc.nottingham.ac.uk:8016)
2. Find your timetable
3. **Important**: Switch to "List" view (the converter only works with list view)
4. Copy the entire URL from your browser's address bar
5. Visit the [converter website](https://unmc-timetable.streamlit.app/) and paste the URL
6. Set the academic year start date:
   - This should be the Monday of Week 1
   - Note: Undergraduate students typically start at Week 4
7. Select which classes you want to include in your calendar
8. Click "Generate Calendar" and download the ICS file
9. Import the ICS file into your preferred calendar application

## Development Setup

This app uses `poetry` to manage dependencies. Clone the repository and run `poetry install` to install the dependencies.

Run the app with `poetry run streamlit run app.py`.

## Deployment

Follow Streamlit's [deployment tutorials](https://docs.streamlit.io/deploy/tutorials).