# 💰 Digital Banking System

A simple banking web application built using **Django** and integrated with **FastAPI** for handling transactions.

---

## 🚀 Features

* 🔐 User Signup & Login
* 🏦 Dashboard
* 💸 Money Transfer
* 📊 Transaction History
* 📄 Download Transaction Statement (PDF)
* ⚡ FastAPI integration

---

## 🛠️ Tech Stack

* **Frontend & Backend:** Django
* **API Service:** FastAPI
* **Database:** SQLite
* **PDF Generation:** ReportLab
* **Authentication:** Django Auth

---

## 📂 Project Structure

```
digital/
│── banking/
│   ├── models.py
│   ├── views.py
│   ├── templates/
│   │   ├── signup.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── history.html
│   │   └── base.html
│   └── urls.py
│
│── digital/
│   ├── settings.py
│   ├── urls.py
│
│── db.sqlite3
│── manage.py
```

---

## ⚙️ Installation

### 1️⃣ Clone the Repository

```
git clone https://github.com/aarthiaanbu-debug/digital_banking.git
cd digital_banking
```

### 2️⃣ Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```
pip install django fastapi uvicorn reportlab requests
```

---

## ▶️ Run the Project

### Step 1: Run FastAPI Server

```
python -m uvicorn main:app --reload --port 8001
```

### Step 2: Run Django Server

```
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000
```

---

## 🔄 Application Flow

1. Signup
2. Login
3. Redirect to Dashboard
4. Transfer Money
5. View Transaction History
6. Download PDF Statement

---

## 📊 Models

### 👤 UserData

* username
* email
* password
* balance

### 💸 Transaction

* sender (ForeignKey)
* receiver (ForeignKey)
* amount
* status
* timestamp

---

## 📄 PDF Statement

* Shows all transactions
* Includes:

  * Sender
  * Receiver
  * Amount
  * Type (Sent / Received)

---

## ❗ Common Errors & Fixes

### ❌ Error:

```
Cannot resolve keyword 'username' into field
```

### ✅ Fix:

```
from django.db.models import Q

transactions = Transaction.objects.filter(
    Q(sender=user_data) | Q(receiver=user_data)
)
```

---

### ❌ Login not redirecting to dashboard

### ✅ Fix:

```
if user:
    login(request, user)
    return redirect('dashboard')
```

---

## 🔮 Future Improvements

* 💳 Payment Gateway Integration
* 📱 Mobile Responsive UI
* 🔔 Notifications
* 📈 Analytics Dashboard



If you like this project, give it a ⭐ on GitHub!
