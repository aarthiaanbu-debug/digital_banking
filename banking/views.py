from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from decimal import Decimal
import random

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.db.models import Q

from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors
from reportlab.platypus import TableStyle

from .models import Account, Transaction


# ---------------- SIGNUP ----------------
def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        # Create account
        Account.objects.create(user=user, balance=1000)

        messages.success(request, "Account created")
        return redirect("login")

    return render(request, "signup.html")


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        request.session["username"] = username
        return redirect("dashboard")

    return render(request, "login.html")


# ---------------- DASHBOARD ----------------
def dashboard(request):
    username = request.session.get("username")

    if not username:
        return redirect("login")

    user = User.objects.get(username=username)

    account, created = Account.objects.get_or_create(user=user)

    return render(request, "dashboard.html", {"account": account})


# ---------------- TRANSFER ----------------
def transfer_view(request):
    if request.method == "POST":
        sender_username = request.session.get("username")
        receiver_username = request.POST["receiver"]
        amount = request.POST["amount"]

        # Save transfer data
        request.session["transfer_data"] = {
            "sender": sender_username,
            "receiver": receiver_username,
            "amount": amount
        }

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        request.session["otp"] = otp

        # 🔥 SEND EMAIL
        sender_user = User.objects.get(username=sender_username)

        send_mail(
            "Banking OTP Verification",
            f"Your OTP is: {otp}",
            settings.EMAIL_HOST_USER,  # sender mail
            ["aarthia290302@gmail.com"],  # receiver mail (your requirement)
            fail_silently=False,
        )

        print("OTP:", otp)

        return redirect("otp")

    return render(request, "transfer.html")


# ---------------- VERIFY OTP ----------------
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("otp")

        if entered_otp == str(session_otp):

            sender = request.user
            receiver_username = request.session.get("receiver")
            amount = request.session.get("amount")

            from django.contrib.auth.models import User
            receiver = User.objects.filter(username=receiver_username).first()

            if not receiver:
                return HttpResponse("Receiver not found ❌")

            sender_account = sender.account
            receiver_account = receiver.account

            if sender_account.balance >= amount:
                sender_account.balance -= amount
                receiver_account.balance += amount

                sender_account.save()
                receiver_account.save()

                return HttpResponse("Money Sent Successfully ✅")
            else:
                return HttpResponse("Insufficient Balance ❌")

        else:
            return HttpResponse("Invalid OTP ❌")

    return render(request, "otp.html")

# ---------------- HISTORY ----------------
def history(request):
    username = request.session.get("username")

    if not username:
        return redirect("login")

    user = User.objects.get(username=username)
    account, created = Account.objects.get_or_create(user=user)

    txns = Transaction.objects.filter(sender=account) | Transaction.objects.filter(receiver=account)

    return render(request, "history.html", {"txns": txns})


# ---------------- DOWNLOAD PDF ----------------
def download_pdf(request):
    if not request.session.get("username"):
        return redirect("login")

    username = request.session.get("username")
    account = Account.objects.get(user__username=username)

    transactions = Transaction.objects.filter(
        Q(sender=account) | Q(receiver=account)
    )

    if not transactions.exists():
        return HttpResponse("No transactions found")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="statement.pdf"'

    doc = SimpleDocTemplate(response)

    data = [["Sender", "Receiver", "Amount"]]

    for t in transactions:
        data.append([
            t.sender.user.username,
            t.receiver.user.username,
            f"₹{t.amount}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    doc.build([table])

    return response


# ---------------- LOGOUT ----------------
def logout_view(request):
    request.session.flush()
    return redirect("login")