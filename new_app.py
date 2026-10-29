from flask import Flask, jsonify, request, render_template
import mysql.connector
from datetime import date, datetime, time, timedelta  # για μετατροπή σε string
from decimal import Decimal

app = Flask(__name__)

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",   # βάλε τον δικό σου κωδικό
        database="uni_app" # η βάση σου
    )
    return conn

# επιτρέπουμε μόνο αυτούς τους πίνακες στις φόρμες
ALLOWED_TABLES = { "flight", "airline", "airport", "passengers", "aircraft"}


def normalize_rows(rows):
    """
    Μετατρέπει date/datetime/time/timedelta τιμές σε string,
    ώστε να είναι JSON serializable για το jsonify().
    """
    for row in rows:
        for k, v in row.items():
            if isinstance(v, (date, datetime, time, timedelta)):
                row[k] = str(v)
    return rows


@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()

    # Μοναδικές πόλεις αναχώρησης
    cur.execute("""
        SELECT DISTINCT city
        FROM airport
        WHERE city IS NOT NULL
        ORDER BY city
    """)
    cities = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    # ονόματα πινάκων για το dropdown
    table_names = sorted(ALLOWED_TABLES)

    return render_template(
        "new_app.html",
        departure_cities=cities,
        arrival_cities=cities,
        table_names = table_names,
    )

#εμφανισε τα αποτελεσματα του 1ου κουτιου
@app.route("/view_table", methods=["GET"])
def view_table():
    
    table = request.args.get("table")

    if not table or table not in ALLOWED_TABLES:
        return jsonify({
            "status": "error",
            "message": "Μη έγκυρο όνομα πίνακα."
        })

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # ΠΡΟΣΟΧΗ: χρησιμοποιούμε το ALLOWED_TABLES για να είμαστε ασφαλείς
    sql = f"SELECT * FROM {table}"
    cursor.execute(sql)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    rows = normalize_rows(rows)

    return jsonify({
        "status": "success",
        "table": table,
        "rows": rows
    })

    

#εμφανισε τα αποτελεσματα του 2ου κουτιου
@app.route("/insert_flight", methods=["POST"])
def insert_flight():
    data = request.get_json()

    

    try:
        airline_id = int(data.get("airline_id"))
        dep_airport_id = int(data.get("departure_airport_id"))
        arr_airport_id = int(data.get("arrival_airport_id"))
        flight_date_str = data.get("flight_date")  # "2026-04-01"
        flight_time_str = data.get("flight_time")  # "14:10"
        price_str = data.get("price")
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Έλεγξε ότι όλα τα πεδία έχουν σωστή μορφή."
        })
    
    if not all([airline_id, dep_airport_id, arr_airport_id,
                flight_date_str, flight_time_str]):
        return jsonify({
            "status": "error",
            "message": "Συμπλήρωσε όλα τα απαραίτητα πεδία."
        })
    
    # Μετατροπές ημερομηνίας/ώρας/τιμής
    flight_date = datetime.strptime(flight_date_str, "%Y-%m-%d").date()
    flight_time = datetime.strptime(flight_time_str, "%H:%M").time()
    price = float(price_str) if price_str not in (None, "") else None

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    insert_sql = """
        INSERT into flight
        (airline_id, departure_airport_id, arrival_airport_id,
        flight_date, flight_time, price)
        VALUES (%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(
        insert_sql,
        (
            airline_id, dep_airport_id, arr_airport_id,
            flight_date, flight_time, price
        )
    )
    conn.commit()

    new_id = cursor.lastrowid

    cursor.execute(
        """
        select f.id,
        f.airline_id,
        f.departure_airport_id,
        f.arrival_airport_id,
        ad.city as departure_city,
        aa.city as arrival_city,
        f.flight_date,
        f.flight_time,
        f.price
        from flight f 
        join airport ad on f.departure_airport_id = ad.airport_id
        join airport aa on f.arrival_airport_id = aa.airport_id
        where f.id = %s
        """,
        (new_id,)
    )
    #cursor.execute("SELECT * FROM flight WHERE id = %s", (new_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        if isinstance(row["flight_date"], (date, datetime)):
            row["flight_date"] = row["flight_date"].strftime("%Y-%m-%d")
        row["flight_time"] = str(row["flight_time"])
        if isinstance(row["price"], Decimal):
            row["price"] = float(row["price"])
        
    return jsonify({
        "status": "success",
        "message": "Η πτήση καταχωρήθηκε με επιτυχία",
        "flight": row
    })



#εμφανισε τα αποτελεσματα του 3ου κουτιου
@app.route("/delete_flight", methods=["POST"])
def delete_flight():
    data = request.get_json()
    flight_id = data.get("id")

    if not flight_id:
        return jsonify({"status": "error", "message": "Δεν δόθηκε κωδικός πτήσης."})

    conn = get_connection()
    cursor = conn.cursor()

    # Εκτέλεση διαγραφής
    sql = "DELETE FROM flight WHERE id = %s"
    cursor.execute(sql, (flight_id,))
    conn.commit()

    rows_deleted = cursor.rowcount  # πόσες γραμμές διαγράφηκαν

    cursor.close()
    conn.close()

    if rows_deleted > 0:
        return jsonify({"status": "success", 
                        "message": f"Η πτήση με κωδικό {flight_id} διαγράφηκε με επιτυχία."})
    else:
        return jsonify({"status": "not_found", 
                        "message": f"Δεν βρέθηκε πτήση με κωδικό {flight_id}."})


#εμφανισε τα αποτελεσματα του 4ου κουτιου
@app.route("/search_flights", methods=["GET"])
def search_flights():
    from_city = request.args.get("fromCity")
    to_city = request.args.get("toCity")
    total_days = request.args.get("days", type=int)
    date_str = request.args.get("flightDate")   

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # query αναχωρησης
    query = """
        SELECT f.id, ad.airport_name AS airport_name, ad.country as country, ad.city AS departure_city, aa.city AS arrival_city, f.flight_date, f.flight_time, f.price
        FROM flight f
        JOIN airport ad ON f.departure_airport_id = ad.airport_id   -- departure airport
        JOIN airport aa ON f.arrival_airport_id = aa.airport_id     -- arrival airport
        where 1=1
    """
    params = []

    if from_city:
        query += " AND ad.city = %s"
        params.append(from_city)

    if to_city:
        query += " AND aa.city = %s"
        params.append(to_city)

    selected_date = None
    if date_str:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        prev_date = selected_date - timedelta(days=2)
        next_date = selected_date + timedelta(days=2)
        query += " AND f.flight_date BETWEEN %s AND %s"
        params.extend([prev_date, next_date])

    query += " ORDER BY f.flight_date, f.flight_time"

    cur.execute(query, params)
    rows = cur.fetchall()

    # query επιστροφης (ιδιο με πανω αλλα αντιστρεφω τις πολεις)
    return_rows = []
    return_date = None
    if from_city and to_city and selected_date and total_days is not None:
        return_date = selected_date + timedelta(days=total_days)
        dep_city = to_city
        arr_city = from_city
        cur.execute(
            """
            SELECT f.id, ad.airport_name AS airport_name, ad.country as country, ad.city AS departure_city, aa.city AS arrival_city, f.flight_date, f.flight_time, f.price
            FROM flight f
            JOIN airport ad ON f.departure_airport_id = ad.airport_id   -- departure airport
            JOIN airport aa ON f.arrival_airport_id = aa.airport_id     -- arrival airport
            where ad.city=%s and aa.city=%s and f.flight_date BETWEEN %s AND %s
            ORDER BY f.flight_date, f.flight_time
            """,(dep_city, arr_city, return_date - timedelta(days=2), return_date + timedelta(days=2),)
        )
        return_rows = cur.fetchall()

    cur.close()
    conn.close()

    # Μετατροπή για JSON + flag is_selected

    # αποτελεσματα αναχωρησης
    results = []
    for row in rows:
        fdate = row["flight_date"]
        if isinstance(fdate, (datetime, )):
            fdate = fdate.date()
        date_out = fdate.strftime("%Y-%m-%d")

        ftime = str(row["flight_time"])
        price = row["price"]
        if isinstance(price, Decimal):
            price = float(price)

        is_selected = (selected_date is not None and fdate == selected_date)

        results.append({
            "id": row["id"],
            "airport_name": row["airport_name"],
            "country": row["country"],
            "departure_city": row["departure_city"],
            "arrival_city": row["arrival_city"],
            "flight_date": date_out,
            "flight_time": ftime,
            "price": price,
            "is_selected": is_selected,
        })

    # αποτελεσματα επιστροφης
    return_results = []
    for row in return_rows:
        fdate = row["flight_date"]
        if isinstance(fdate, (datetime, )):
            fdate = fdate.date()
        date_out = fdate.strftime("%Y-%m-%d")

        ftime = str(row["flight_time"])
        price = row["price"]
        if isinstance(price, Decimal):
            price = float(price)
        
        is_selected_ret = (return_date is not None and fdate == return_date)

        return_results.append({
            "id": row["id"],
            "airport_name": row["airport_name"],
            "country": row["country"],
            "departure_city": row["departure_city"],
            "arrival_city": row["arrival_city"],
            "flight_date": date_out,
            "flight_time": ftime,
            "price": price,
            "is_selected": is_selected_ret, 
        })  

    return jsonify({
        "outbound":results,
        "return":return_results})

#εμφανισε τα αποτελεσματα του 5ου κουτιου
@app.route("/search_best_offers", methods=["GET"])
def search_best_offers():
    from_city = request.args.get("fromCity")
    month_str = request.args.get("month")  # "4" για Απρίλιο κτλ.

    if not from_city or not month_str:
        # Αν δεν έχει δώσει και τα δύο, γύρνα κενά αποτελέσματα
        return jsonify([])

    month = int(month_str)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT ad.city as departure_city, aa.city as arrival_city, f.flight_date, f.flight_time, f.price
        FROM flight f
        JOIN airport ad ON f.departure_airport_id = ad.airport_id   -- departure airport
        JOIN airport aa ON f.arrival_airport_id = aa.airport_id     -- arrival airport
        WHERE  ad.city = %s
        AND MONTH(f.flight_date) = %s
        ORDER BY f.price ASC
    """
    cur.execute(query, (from_city, month))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for row in rows:
        fdate = row["flight_date"]
        if isinstance(fdate, (datetime, date)):
            fdate = fdate.strftime("%Y-%m-%d")
        else:
            fdate = str(fdate)

        ftime = str(row["flight_time"])
        price = row["price"]
        if isinstance(price, Decimal):
            price = float(price)

        results.append({
            "departure_city": row["departure_city"],
            "arrival_city": row["arrival_city"],
            "flight_date": fdate,
            "flight_time": ftime,
            "price": price,
        })

    return jsonify(results)

#εμφανισε αποτελεσματα 6ου κουτιου
@app.route("/search_passengers", methods=["GET"])
def search_passengers():
    # 1. Παίρνουμε το id της πτήσης από τα query params
    flight_id = request.args.get("flight_id", type=int)

    if not flight_id:
        return jsonify({
            "status": "error",
            "message": "Δεν δόθηκε ID πτήσης."
        })

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # 2. Βρίσκουμε το capacity για αυτή την πτήση
    # (όπως στο query που έδειξες, με join aircraft → airline → flight)
    cur.execute(
        """
        SELECT ac.capacity
        FROM aircraft ac
        JOIN airline ai ON ac.airline_id = ai.airline_id
        JOIN flight f ON f.airline_id = ai.airline_id
        WHERE f.id = %s
        """,
        (flight_id,)
    )
    cap_row = cur.fetchone()

    if not cap_row:
        cur.close()
        conn.close()
        return jsonify({
            "status": "not_found",
            "message": f"Δεν βρέθηκε πτήση με id {flight_id}."
        })

    capacity = cap_row["capacity"]

    # 3. Φέρνουμε όλους τους επιβάτες αυτής της πτήσης
    cur.execute(
        """
        SELECT *
        FROM passengers
        WHERE flight_id = %s
        ORDER BY id
        """,
        (flight_id,)
    )
    passengers = cur.fetchall()
    passenger_count = len(passengers)

    remaining_seats = capacity - passenger_count

    cur.execute(
        """
        select ad.airport_name as airport_name, ad.city as departure_city, aa.city as arrival_city, f.flight_date, f.flight_time, f.price
        from flight f
        join airport ad ON f.departure_airport_id = ad.airport_id
        JOIN airport aa ON f.arrival_airport_id = aa.airport_id
        where f.id = %s
        """,
        (flight_id,)
    )

    flight_row = cur.fetchone()

    flight_info = None
    if flight_row:
        fdate = flight_row["flight_date"]
        if isinstance(fdate, (datetime, date)):
            fdate = fdate.strftime("%Y-%m-%d")
        else:
            fdate = str(fdate)

        ftime = str(flight_row["flight_time"])
        price = flight_row["price"]
        if isinstance(price, Decimal):
            price = float(price)

        flight_info = {
            "airport_name": flight_row["airport_name"],
            "departure_city": flight_row["departure_city"],
            "arrival_city": flight_row["arrival_city"],
            "flight_date": fdate,
            "flight_time": ftime,
            "price": price,
        }

    cur.close()
    conn.close()

    return jsonify({
        "status": "success",
        "flight_id": flight_id,
        "capacity": capacity,
        "passenger_count": passenger_count,
        "remaining_seats": remaining_seats,
        "passengers": passengers,
        "flight_info": flight_info
    })





#main
if __name__ == "__main__":
    app.run(debug=True)