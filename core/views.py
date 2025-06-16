from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
import random
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Profile, Transaction, Transfer, Send, VerificationCode


def home(request):
    if request.user.is_authenticated:
        return render(request, 'core/dashboard.html')
    return redirect('/accounts/login/')


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')


@login_required
def send(request):
    return render(request, 'core/send.html')


@login_required
@csrf_exempt
def sendTwo(request):
    user = request.user

    if request.method == "POST":
        otp = request.POST.get('otp')

        if not otp:
            # Stage 1: Save temp form data and generate OTP
            account_number = request.POST.get('account')
            amount_str = request.POST.get('amount')
            note = request.POST.get('note', '')

            try:
                Decimal(amount_str)
            except:
                return JsonResponse({'success': False, 'error': 'Invalid amount.'})

            request.session['temp_transaction'] = {
                'account_number': account_number,
                'amount': amount_str,
                'note': note,
            }

            code = random.randint(100000, 999999)

            try:
                amount = Decimal(amount_str)
                transaction: Transaction = Transaction.objects.create(
                    user=user,
                    transaction_type='Send',
                    amount=amount
                )
                VerificationCode.objects.create(
                    transaction=transaction,
                    code=code,
                    expired=False
                )
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

            request.session['otp_code'] = str(code)
            request.session['transaction_id'] = transaction.id

            # Removed print statement for OTP

            return JsonResponse({'success': True, 'message': 'OTP sent'})

        else:
            # Stage 2: Validate OTP and process transaction
            temp = request.session.get('temp_transaction')
            session_otp = request.session.get('otp_code')
            transaction_id = request.session.get('transaction_id')

            if not temp or not session_otp or not transaction_id:
                return JsonResponse({'success': False, 'error': 'Session expired. Please try again.'})

            if str(otp) != session_otp:
                return JsonResponse({'success': False, 'error': 'Invalid OTP'})

            try:
                profile = Profile.objects.get(user=user)
                recipient_profile = Profile.objects.get(account_number=temp['account_number'].strip())
                amount = Decimal(temp['amount'])

                if profile.balance < amount:
                    return JsonResponse({'success': False, 'error': 'Insufficient balance'})

                transaction = Transaction.objects.get(id=transaction_id)

                # Mark the verification code as expired
                verification_code = VerificationCode.objects.get(transaction=transaction, code=int(otp), expired=False)
                verification_code.expired = True
                verification_code.save()

                Send.objects.create(
                    transaction=transaction,
                    reciever=recipient_profile.user,
                    note=temp['note']
                )

                profile.balance -= amount
                profile.save()

                recipient_profile.balance += amount
                recipient_profile.save()

                del request.session['temp_transaction']
                del request.session['otp_code']
                del request.session['transaction_id']

                return JsonResponse({'success': True})

            except VerificationCode.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid or expired OTP'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

    else:
        profile = Profile.objects.get(user=user)
        return render(request, 'core/send-two.html', {'balance': profile.balance})


@require_GET
def lookup_account_name(request):
    account_number = request.GET.get('account_number')
    try:
        profile = Profile.objects.select_related('user').get(account_number=account_number)
        full_name = f"{profile.user.first_name} {profile.user.last_name}"
        return JsonResponse({'success': True, 'name': full_name})
    except Profile.DoesNotExist:
        return JsonResponse({'success': False})


@login_required
def transfer(request):
    return render(request, 'core/transfer-one.html')


import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def transferTwo(request):
    user = request.user

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nickname = data.get('nickname', '').strip()
            account_name = data.get('account_name', '').strip()
            account_number = data.get('account_number', '').strip()
            note = data.get('note', '').strip()

            if not account_number or not account_name:
                return JsonResponse({'success': False, 'error': 'Account name and number are required.'})

            # Validate account number length (assuming 12 digits)
            if len(account_number) != 12 or not account_number.isdigit():
                return JsonResponse({'success': False, 'error': 'Account number must be 12 digits.'})

            # Check if recipient profile exists
            try:
                recipient_profile = Profile.objects.get(account_number=account_number)
            except Profile.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Recipient account not found.'})

            # Create transaction
            transaction = Transaction.objects.create(
                user=user,
                transaction_type='Transfer',
                amount=Decimal('0.00')  # Amount to be updated later or handled differently
            )

            # Generate verification code
            code = random.randint(100000, 999999)
            VerificationCode.objects.create(
                transaction=transaction,
                code=code,
                expired=False
            )

            # Store transaction id and code in session for later verification if needed
            request.session['transaction_id'] = transaction.id
            request.session['verification_code'] = str(code)

            return JsonResponse({'success': True, 'message': 'Verification code created. Please enter the code to confirm.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        profile = Profile.objects.get(user=user)
        return render(request, 'core/transfer-two.html', {'balance': profile.balance})


@login_required
def success(request):
    return render(request, 'core/transfer-successful.html')


@login_required
def amen(request):
    return render(request, 'core/amen.html')
