# Flight-Management-Web-Application

Aerofind is a web application for searching and comparing flights and managing flight records. Its Python/Flask backend runs SQL queries against a relational MySQL database that stores flights, airports, airlines, passengers, and aircraft information. The web interface uses HTML, CSS, and JavaScript to display results and send requests to the Flask endpoints.

## Features

- **Browse database tables** to inspect flight records and look up airline and airport IDs.
- **Add and delete flights** using the web interface.
- **Search round-trip flights** by departure city, destination, departure date, and number of nights. Compare fares across a window of two days on either side of the selected date.
- **Compare monthly fares** by choosing a departure city and month to see flights sorted by price.
- **Check seat availability** by flight ID to see the passenger list, passenger count, aircraft capacity, and remaining seats.

## Repository structure

| Path | Contents |
| --- | --- |
| [`new_app.py`](new_app.py) | Python backend with Flask routes, the MySQL connection, and SQL queries for the application features. |
| [`uni_app_database.sql`](uni_app_database.sql) | SQL dump containing the relational schema and project data. |
| [`template/`](template/) | Frontend template with HTML, CSS, and JavaScript. |
| [`report.pdf`](report.pdf) | Project report with installation instructions, schema diagrams, screenshots, and a code walkthrough. |
| [`Presentation.pdf`](Presentation.pdf) | Project presentation. |

## Run locally

You need Python 3 and a running MySQL server. Clone or download this repository and open a terminal in the project directory.

1. Install the Python dependencies.

   ```bash
   python -m pip install flask mysql-connector-python
   ```

2. Create the `uni_app` database if it does not already exist.

   ```bash
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS uni_app CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
   ```

3. Import the SQL dump from the repository. Run this command in a shell that supports input redirection, such as Bash or Windows Command Prompt.

   ```bash
   mysql -u root -p uni_app < uni_app_database.sql
   ```

4. Update the MySQL connection settings in `new_app.py` to match your local MySQL host, username, and password. Keep `uni_app` as the database name.

5. Check the template directory. The repository lists it as `template/`, while the report uses Flask's default `templates/` directory. If the app uses the default, rename your local `template/` folder to `templates/` so Flask can find `new_app.html`.

6. Start the app and open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser by running:

   ```bash
   python new_app.py
   ```

## Documentation

The [project report](report.pdf) is in Greek. Section 2 describes the relational schema, Section 3 covers database import, local setup, and example searches, and Section 4 explains the Flask routes and SQL queries. Section 5 describes the dataset and its limitations.

## Academic context

Aerofind was developed as a team project for **Database Systems II** at the Department of Electrical and Computer Engineering, University of Thessaly, during the fall semester of the 2025–2026 academic year.
