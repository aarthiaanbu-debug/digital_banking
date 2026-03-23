from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
import requests

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

from .models import Transaction, UserData

FASTAPI_URL = "http://127.0.0.1:8001"


# ---------------- SIGNUP ----------------
def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)

        UserData.objects.create(user=user, username=username, balance=0)

        messages.success(request, "Account created successfully")
        return redirect('login')

    return render(request, 'signup.html')


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')   # 🔥 direct URL use
        else:
            messages.error(request, "Invalid login")

    return render(request, 'login.html')


# ---------------- DASHBOARD ----------------
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'dashboard.html')


# ---------------- TRANSFER ----------------
def transfer(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == "POST":
        receiver_username = request.POST.get('receiver').strip()
        amount = request.POST.get('amount')

        try:
            response = requests.post(
                f"{FASTAPI_URL}/account/transfer",
                json={
                    "sender": request.user.username,
                    "receiver": receiver_username,
                    "amount": int(amount)
                }
            )

            data = response.json()

            if response.status_code == 200:

                # ✅ Convert Django User → UserData
                try:
                    sender_data = UserData.objects.get(username=request.user.username)
                    receiver_data = UserData.objects.get(username=receiver_username)
                except UserData.DoesNotExist:
                    messages.error(request, "User not found in database")
                    return redirect('dashboard')

                # ✅ SAVE TRANSACTION (THIS IS YOUR FIX)
                Transaction.objects.create(
                    sender=sender_data,
                    receiver=receiver_data,
                    amount=amount,
                    status="SUCCESS"
                )

                messages.success(request, "Transfer successful!")

            else:
                messages.error(request, data.get('detail', 'Transfer failed'))

        except requests.exceptions.ConnectionError:
            messages.error(request, "FastAPI server not running!")

    return redirect('dashboard')


# ---------------- HISTORY ----------------
from django.db.models import Q

def history(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        user_data = UserData.objects.get(username=request.user.username)
    except UserData.DoesNotExist:
        return HttpResponse("User data not found")

    transactions = Transaction.objects.filter(
        Q(sender=user_data) | Q(receiver=user_data)
    ).order_by('-timestamp')

    return render(request, 'history.html', {'transactions': transactions})


# ---------------- DOWNLOAD PDF ----------------
def download_pdf(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        user_data = UserData.objects.get(username=request.user.username)
    except UserData.DoesNotExist:
        return HttpResponse("User data not found")

    transactions = Transaction.objects.filter(
        Q(sender=user_data) | Q(receiver=user_data)
    ).order_by('-timestamp')

    if not transactions.exists():
        return HttpResponse("No transactions found")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="statement.pdf"'

    doc = SimpleDocTemplate(response)

    data = [["Sender", "Receiver", "Amount", "Type"]]

    for t in transactions:
        if t.sender == user_data:
            tx_type = "Sent"
        else:
            tx_type = "Received"

        data.append([
            t.sender.username,
            t.receiver.username,
            f"₹{t.amount}",
            tx_type
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    doc.build([table])

    return response


# ---------------- ADD MONEY ----------------
def add_money(request):
    if request.method == "POST":
        messages.success(request, "Money added (dummy)")

    return redirect('dashboard')


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('login')