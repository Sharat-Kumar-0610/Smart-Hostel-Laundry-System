from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hostel_laundry_secret_2024"

@app.context_processor
def inject_now():
    return {"now": datetime.now().strftime("%a, %d %b %Y")}

# ─── Database Configuration ────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sharat",   # ← your password kept as-is
    "database": "da2"
}

def get_db_connection():
    """Create and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def query_db(sql, params=None, fetch=True):
    """Execute a SQL query and optionally return results."""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        cursor.close()
        conn.close()
        return result, None
    except Error as e:
        conn.close()
        return None, str(e)

# ─── Home / Dashboard ──────────────────────────────────────────────────────────
@app.route("/")
def home():
    students,   _ = query_db("SELECT COUNT(*) AS cnt FROM Student")
    orders,     _ = query_db("SELECT COUNT(*) AS cnt FROM LaundryOrder")
    payments,   _ = query_db("SELECT COUNT(*) AS cnt FROM Payment")
    complaints, _ = query_db("""
                            SELECT COUNT(*) AS cnt 
                            FROM Complaint 
                            WHERE Status != 'Resolved'
                            AND Description IS NOT NULL AND Description != ''
                            """)
    pending,    _ = query_db("SELECT COUNT(*) AS cnt FROM LaundryOrder WHERE OrderStatus='Pending'")
    revenue,    _ = query_db("SELECT COALESCE(SUM(Amount),0) AS total FROM Payment WHERE PaymentStatus='Paid'")

    recent_orders, _ = query_db("""
        SELECT lo.OrderID, lo.OrderDate, lo.TotalClothes, lo.OrderStatus, s.Name
        FROM   LaundryOrder lo
        JOIN   Student s ON lo.StudentID = s.StudentID
        ORDER  BY lo.OrderID DESC LIMIT 5
    """)

    # NEW — last 4 complaints for dashboard widget
    recent_complaints, _ = query_db("""
        SELECT c.ComplaintID, c.ComplaintDate,c.Description AS ComplaintDescription, c.Status,
               s.Name AS StudentName
        FROM   Complaint c
        JOIN   Student s ON c.StudentID = s.StudentID
        ORDER  BY c.ComplaintID DESC LIMIT 4
    """)

    stats = {
        "students":   students[0]["cnt"]    if students   else 0,
        "orders":     orders[0]["cnt"]      if orders     else 0,
        "payments":   payments[0]["cnt"]    if payments   else 0,
        "complaints": complaints[0]["cnt"]  if complaints else 0,   # NEW
        "pending":    pending[0]["cnt"]     if pending    else 0,
        "revenue":    revenue[0]["total"]   if revenue    else 0,
    }
    return render_template(
        "index.html",
        stats=stats,
        recent_orders=recent_orders or [],
        recent_complaints=recent_complaints or []   # NEW
    )

# ─── Students ──────────────────────────────────────────────────────────────────
@app.route("/students")
def students():
    data, err = query_db("SELECT * FROM Student ORDER BY StudentID DESC")
    return render_template("students.html", students=data or [], error=err)

@app.route("/students/add", methods=["POST"])
def add_student():
    name   = request.form.get("name", "").strip()
    reg_no = request.form.get("register_number", "").strip()
    block  = request.form.get("hostel_block", "").strip()
    room   = request.form.get("room_number", "").strip()
    phone  = request.form.get("phone_number", "").strip()

    if not all([name, reg_no, block, room, phone]):
        flash("All fields are required.", "error")
        return redirect(url_for("students"))

    sql = """INSERT INTO Student (Name, RegisterNumber, HostelBlock, RoomNumber, PhoneNumber)
             VALUES (%s, %s, %s, %s, %s)"""
    _, err = query_db(sql, (name, reg_no, block, room, phone), fetch=False)
    if err:
        flash(f"Error adding student: {err}", "error")
    else:
        flash(f"Student '{name}' added successfully!", "success")
    return redirect(url_for("students"))

# API endpoint for AJAX add
@app.route("/api/students/add", methods=["POST"])
def api_add_student():
    data       = request.get_json()
    student_id = data.get("student_id")
    name       = data.get("name", "").strip()
    reg_no     = data.get("register_number", "").strip()
    block      = data.get("hostel_block", "").strip()
    room       = data.get("room_number", "").strip()
    phone      = data.get("phone_number", "").strip()

    if not all([name, reg_no, block, room, phone]):
        return jsonify({"success": False, "message": "All fields are required."}), 400

    sql = """INSERT INTO Student (StudentID, Name, RegisterNumber, HostelBlock, RoomNumber, PhoneNumber)
             VALUES (%s, %s, %s, %s, %s, %s)"""
    new_id, err = query_db(sql, (student_id, name, reg_no, block, room, phone), fetch=False)
    if err:
        return jsonify({"success": False, "message": err}), 500
    return jsonify({"success": True, "message": f"Student '{name}' added!", "id": new_id})

@app.route("/api/students")
def api_students():
    data, err = query_db("SELECT * FROM Student ORDER BY StudentID DESC")
    if err:
        return jsonify({"success": False, "message": err}), 500
    return jsonify({"success": True, "students": data})

# ─── Laundry Orders ────────────────────────────────────────────────────────────
# MODIFIED — now JOINs ClothingItem, RegularClothes, DelicateClothes
@app.route("/orders")
def orders():
    data, err = query_db("""
        SELECT
            o.OrderID,
            o.OrderDate,
            o.TotalClothes,
            o.OrderStatus,
            o.StaffID,
            s.Name        AS StudentName,
            s.HostelBlock,
            ci.ClothType,
            ci.Color,
            ci.FabricType
        FROM      LaundryOrder  o
        JOIN      Student       s  ON s.StudentID = o.StudentID
        LEFT JOIN ClothingItem  ci ON ci.OrderID  = o.OrderID
        ORDER BY  o.OrderID DESC
    """)
    return render_template("orders.html", orders=data or [], error=err)

@app.route("/api/orders")
def api_orders():
    data, err = query_db("""
        SELECT
            o.OrderID,
            o.OrderDate,
            o.TotalClothes,
            o.OrderStatus,
            o.StaffID,
            s.Name        AS StudentName,
            s.HostelBlock,
            ci.ClothType,
            ci.Color,
            ci.FabricType
        FROM      LaundryOrder  o
        JOIN      Student       s  ON s.StudentID = o.StudentID
        LEFT JOIN ClothingItem  ci ON ci.OrderID  = o.OrderID
        ORDER BY  o.OrderID DESC
    """)
    if err:
        return jsonify({"success": False, "message": err}), 500

    # ── Serialise date/datetime objects so jsonify doesn't crash ──
    for row in (data or []):
        for k, v in row.items():
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()

    return jsonify({"success": True, "orders": data or []})

# ─── Payments ──────────────────────────────────────────────────────────────────
@app.route("/payments")
def payments():
    data, err = query_db("""
        SELECT p.*, s.Name AS StudentName, lo.TotalClothes
        FROM   Payment p
        JOIN   Student s       ON p.StudentID = s.StudentID
        JOIN   LaundryOrder lo ON p.OrderID   = lo.OrderID
        ORDER  BY p.PaymentID DESC
    """)
    return render_template("payments.html", payments=data or [], error=err)

@app.route("/api/payments")
def api_payments():
    data, err = query_db("""
        SELECT
            p.PaymentID,
            p.OrderID,
            p.Amount,
            p.PaymentMode,
            p.PaymentStatus,
            p.PaymentDate,
            s.Name        AS StudentName,
            lo.TotalClothes,
            lo.OrderDate
        FROM   Payment      p
        JOIN   LaundryOrder lo ON p.OrderID   = lo.OrderID
        JOIN   Student      s  ON lo.StudentID = s.StudentID
        ORDER  BY p.PaymentID DESC
    """)
    if err:
        return jsonify({"success": False, "message": err}), 500
    for row in data:
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
    return jsonify({"success": True, "payments": data})

# ─── Complaints ─────────────────────────────────────────────────────────────── NEW
@app.route("/complaints")
def complaints():
    data, err = query_db("""
        SELECT
            c.ComplaintID,
            c.ComplaintDate,
            c.Description AS ComplaintDescription,
            c.Status,
            s.Name        AS StudentName,
            s.HostelBlock,
            s.RoomNumber
        FROM   Complaint c
        JOIN   Student   s ON s.StudentID = c.StudentID
        ORDER  BY c.ComplaintID DESC
    """)
    return render_template("complaints.html", complaints=data or [], error=err)

@app.route("/api/complaints")
def api_complaints():
    data, err = query_db("""
        SELECT c.*, s.Name AS StudentName, s.HostelBlock, s.RoomNumber
        FROM   Complaint c
        JOIN   Student   s ON s.StudentID = c.StudentID
        ORDER  BY c.ComplaintID DESC
    """)

    if err:
        return jsonify({"success": False, "message": err}), 500
    for row in data:
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
    return jsonify({"success": True, "complaints": data})

# # ─── Add Complaint ─────────────────────────────────────────────────────────────
@app.route("/api/complaints/add", methods=["POST"])
def api_add_complaint():
    data = request.get_json()

    student_id = data.get("student_id")   # 🔥 ADD THIS
    description = (data.get("description") or "").strip()

    if not student_id or not description:
        return jsonify({"success": False, "message": "All fields required"}), 400

    sql = """
    INSERT INTO Complaint (StudentID, Description, ComplaintDate, Status)
    VALUES (%s, %s, CURDATE(), 'Open')
    """

    _, err = query_db(
        sql,
        (student_id, description),   # 🔥 FIXED TUPLE
        fetch=False
    )

    if err:
        return jsonify({"success": False, "message": err}), 500

    return jsonify({"success": True, "message": "Complaint submitted successfully."})

# ─── Update Complaint Status (PUT) ────────────────────────────────────────────
@app.route("/api/complaints/<int:complaint_id>", methods=["PUT"])
def api_put_complaint_status(complaint_id):
    data       = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip()

    VALID = {"Open", "In Progress", "Resolved"}
    if new_status not in VALID:
        return jsonify({
            "success": False,
            "message": f"Invalid status. Choose one of: {', '.join(sorted(VALID))}"
        }), 400

    print(f"[DEBUG] PUT /api/complaints/{complaint_id} — new_status='{new_status}'")

    _, err = query_db(
        "UPDATE Complaint SET Status = %s WHERE ComplaintID = %s",
        (new_status, complaint_id),
        fetch=False
    )

    if err:
        print(f"[DEBUG] DB error: {err}")
        return jsonify({"success": False, "message": err}), 500

    print(f"[DEBUG] Complaint {complaint_id} updated to '{new_status}' — commit OK")
    return jsonify({
        "success": True,
        "message": f"Complaint {complaint_id} updated to '{new_status}'."
    })

# DELETE the entire update_complaint function and its decorator — do not leave any trace of it.

# ─── Update Order Status ───────────────────────────────────────────────────────
@app.route("/api/orders/update-status", methods=["POST"])
def api_update_order_status():
    data       = request.get_json()
    order_id   = data.get("order_id")
    new_status = data.get("status", "").strip()

    VALID = {"Pending", "Processing", "Completed", "Delivered"}
    if not order_id or new_status not in VALID:
        return jsonify({"success": False, "message": "Invalid input."}), 400

    _, err = query_db(
        "UPDATE LaundryOrder SET OrderStatus = %s WHERE OrderID = %s",
        (new_status, order_id),
        fetch=False
    )
    if err:
        return jsonify({"success": False, "message": err}), 500
    return jsonify({"success": True, "message": f"Order status updated to '{new_status}'."})

# # ─── Staff API ─────────────────────────────────────────────────────────────────
# @app.route("/api/staff")
# def api_staff():
#     data, err = query_db("SELECT StaffID, Name FROM Staff ORDER BY Name")
#     if err:
#         return jsonify({"success": False, "message": err}), 500
#     return jsonify({"success": True, "staff": data})

# ─── Add Order ─────────────────────────────────────────────────────────────────
@app.route("/api/orders/add", methods=["POST"])
def api_orders_add():
    data = request.get_json(silent=True) or {}

    # ── Pull all fields from request ─────────────────────────────
    student_id    = data.get("student_id")
    staff_id      = data.get("staff_id")
    total_clothes = data.get("total_clothes")
    status        = data.get("status", "Pending")
    cloth_type    = data.get("cloth_type")
    color         = data.get("color")        # optional
    fabric_type   = data.get("fabric_type")

    print("DEBUG incoming data:", data)      # ← see exactly what arrives

    # ── Server-side validation ───────────────────────────────────
    if not all([student_id, staff_id, total_clothes, cloth_type, fabric_type]):
        missing = [k for k, v in {
            "student_id":    student_id,
            "staff_id":      staff_id,
            "total_clothes": total_clothes,
            "cloth_type":    cloth_type,
            "fabric_type":   fabric_type,
        }.items() if not v]
        print("DEBUG missing fields:", missing)
        return jsonify(success=False, message=f"Missing required fields: {missing}"), 400

    try:
        total_clothes = int(total_clothes)
        if total_clothes < 1:
            raise ValueError("total_clothes must be >= 1")
    except (ValueError, TypeError) as e:
        print("DEBUG validation error:", e)
        return jsonify(success=False, message="Total clothes must be a positive integer."), 400

    valid_statuses = {"Pending", "Processing", "Completed", "Delivered"}
    if status not in valid_statuses:
        status = "Pending"

    # ── Two-step DB insert ───────────────────────────────────────
    conn   = None
    cursor = None
    try:
        conn   = get_db_connection()     # your existing helper
        cursor = conn.cursor()

       # STEP 1 ── Insert into laundryorder with OrderDate
        cursor.execute(
            """
            INSERT INTO LaundryOrder (StudentID, StaffID, TotalClothes, OrderStatus, OrderDate)
            VALUES (%s, %s, %s, %s, CURDATE())
            """,
            (student_id, staff_id, total_clothes, status)
        )
        print("DEBUG laundryorder insert OK")

        # STEP 2 ── Capture the auto-generated OrderID
        order_id = cursor.lastrowid
        print("DEBUG new order_id:", order_id)

        # STEP 3 — Insert into clothingitem
        cursor.execute(
            """INSERT INTO clothingitem (OrderID, ClothType, Color, FabricType)
            VALUES (%s, %s, %s, %s)""",
            (order_id, cloth_type, color, fabric_type)
        )

        # ── NEW STEP 4 — Auto-create a Pending payment record ─────────────────
        cursor.execute(
            """INSERT INTO Payment (OrderID, StudentID, Amount, PaymentMode, PaymentStatus, PaymentDate)
            VALUES (%s, %s, 0, 'Cash', 'Pending', CURDATE())""",
            (order_id, student_id)
        )

        # STEP 5 — Commit all three inserts atomically
        conn.commit()
        print("DEBUG commit OK")

        return jsonify(success=True, message="Order created successfully"), 201

    except Exception as e:
        # Roll back so no partial data is left in the DB
        if conn:
            conn.rollback()
        print("ERROR:", e)                          # ← full error in terminal
        return jsonify(success=False, message=f"Database error: {str(e)}"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ─── Staff API ─────────────────────────────────────────────────────────────────
@app.route("/api/staff")
def api_staff():
    # Adjust column names below if yours differ
    data, err = query_db("SELECT StaffID, Name FROM LaundryStaff ORDER BY Name")
    if err:
        return jsonify({"success": False, "message": err}), 500
    return jsonify({"success": True, "staff": data})

@app.route("/api/payments/<int:payment_id>", methods=["PUT"])
def api_update_payment(payment_id):
    data   = request.get_json(silent=True) or {}
    amount = data.get("amount")
    mode   = data.get("mode", "").strip()
    status = data.get("status", "").strip()

    VALID_MODES   = {"Cash", "UPI", "Card"}
    VALID_STATUS  = {"Pending", "Paid", "Failed"}

    if amount is None or mode not in VALID_MODES or status not in VALID_STATUS:
        return jsonify({"success": False, "message": "Invalid input."}), 400

    try:
        amount = float(amount)
        if amount < 0:
            raise ValueError("negative")
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Amount must be a non-negative number."}), 400

    _, err = query_db(
        """UPDATE Payment
              SET Amount = %s, PaymentMode = %s, PaymentStatus = %s
            WHERE PaymentID = %s""",
        (amount, mode, status, payment_id),
        fetch=False
    )
    if err:
        return jsonify({"success": False, "message": err}), 500
    return jsonify({"success": True, "message": f"Payment {payment_id} updated."})
# ─── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
