🧺 Hostel Laundry Management System

A full-stack web application designed to digitize and streamline hostel laundry operations.
This system manages laundry orders, payments, and complaints with real-time updates and a clean user interface.

---

🚀 Features

🧾 Order Management

- Create laundry orders with:
  - Cloth Type
  - Color
  - Fabric Type (Regular / Delicate)
- Track order status:
  - Pending → Processing → Completed → Delivered
- Dynamic updates from UI

---

💳 Payment System

- Automatic payment record creation for each order
- Update:
  - Amount
  - Payment Mode (Cash / UPI / Card)
  - Payment Status (Pending / Paid)
- Integrated with orders using foreign keys

---

🛠 Complaint Management

- Raise complaints linked to users
- Status workflow:
  - Open → In Progress → Resolved
- Row-level status update with Save button
- Dashboard reflects only active complaints

---

📊 Dashboard

- Overview of:
  - Total Orders
  - Payments
  - Revenue
  - Active Complaints
- Real-time statistics

---

🧠 Tech Stack

- Backend: Flask (Python)
- Database: MySQL (Relational schema with constraints)
- Frontend: HTML, CSS, JavaScript
- Architecture: REST API-based

---

🗄 Database Design

- Normalized relational schema
- Tables include:
  - Student
  - LaundryOrder
  - ClothingItem
  - Payment
  - Complaint
- Uses:
  - Primary Keys
  - Foreign Keys
  - Auto-increment fields

---

⚙️ Key Learnings

- Building REST APIs using Flask
- Handling MySQL constraints & foreign key relationships
- Debugging real-world database errors
- Integrating frontend with backend APIs
- Designing clean and user-friendly UI

---

🔧 Setup Instructions

1. Clone the repository:

git clone https://github.com/your-username/laundry-management-system.git
cd laundry-management-system

2. Install dependencies:

pip install flask mysql-connector-python

3. Configure MySQL:

- Create database: "da2"
- Update credentials in "app.py"

4. Run the application:

python app.py

5. Open in browser:

http://localhost:5000

---

📸 Screenshots

(Add screenshots of dashboard, orders, payments, complaints here)

---

📌 Future Improvements

- Multi-item order support
- Automated pricing system
- Role-based authentication (Admin/User)
- Notifications system

---

🤝 Contributing

Feel free to fork this repo and contribute!

---

⭐ If you found this useful, give it a star!
