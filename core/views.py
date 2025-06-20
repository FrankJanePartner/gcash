from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
import random
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Profile, Transaction, Transfer, Send, VerificationCode
import json
from django.views.decorators.http import require_http_methods
import os
from django.conf import settings


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
    userProfile = Profile.objects.get(user=user)

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
                    amount=amount,
                    status='pending'
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

            return JsonResponse({'success': True, 'message': 'OTP sent'})

        else:
            # Stage 2: Validate OTP and process transaction
            temp = request.session.get('temp_transaction')
            session_otp = request.session.get('otp_code')
            transaction_id = request.session.get('transaction_id')

            if not temp or not session_otp or not transaction_id:
                return JsonResponse({'success': False, 'error': 'Session expired. Please try again.'})

            if str(otp) != session_otp:
                # Update transaction status to failed due to invalid OTP
                try:
                    transaction = Transaction.objects.get(id=transaction_id)
                    transaction.status = 'failed'
                    transaction.save(update_fields=['status'])
                except:
                    pass
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
                if not verification_code.check_validity():
                    transaction.status = 'failed'
                    transaction.save(update_fields=['status'])
                    return JsonResponse({'success': False, 'error': 'OTP expired'})

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

                transaction.status = 'successful'
                transaction.save(update_fields=['status'])

                # Store transaction details in session for success page
                request.session['success_transaction'] = {
                    'id': transaction.id,
                    'amount': str(transaction.amount),
                    'date_time': transaction.date_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'reciever_username': recipient_profile.user.username,
                    'reciever_account_number': recipient_profile.account_number,
                }

                del request.session['temp_transaction']
                del request.session['otp_code']
                del request.session['transaction_id']

                return JsonResponse({'success': True})

            except VerificationCode.DoesNotExist:
                transaction = Transaction.objects.get(id=transaction_id)
                transaction.status = 'failed'
                transaction.save(update_fields=['status'])
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
        full_name = f"{profile.user.username}"
        return JsonResponse({'success': True, 'name': full_name})
    except Profile.DoesNotExist:
        return JsonResponse({'success': False})


@login_required
def transfer(request):
    return render(request, 'core/transfer-one.html')

@login_required
def transferTwo(request):
    import os
    import json
    from django.conf import settings

    # Load banks.json
    banks_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'banks.json')
    with open(banks_path, 'r') as f:
        banks_data = json.load(f)

    # Convert keys from dash-case to underscore_case for template compatibility
    universal_banks_raw = banks_data.get('universal_banks', [])
    universal_banks = []
    for bank in universal_banks_raw:
        universal_banks.append({
            'bank_name': bank.get('bank-name', ''),
            'bank_logo': bank.get('bank-logo', ''),
            'bank_code': bank.get('bank-code', ''),
        })

    return render(request, 'core/transfer-two.html', {'universal_banks': universal_banks})


@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def transferThree(request):

    user = request.user
    profile = Profile.objects.get(user=user)

    # Load banks.json for bank info lookup
    banks_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'banks.json')
    with open(banks_path, 'r') as f:
        banks_data = json.load(f)
    universal_banks = banks_data.get('universal_banks', [])

    selected_bank_code = None
    selected_bank = None

    if request.method == "POST":
        otp = request.POST.get('otp', None)
        amount = request.POST.get('amount', '').strip()

        if not otp:
            account_name = request.POST.get('account_name', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            note = request.POST.get('note', '').strip()
            selected_bank_code = request.POST.get('bank_code', '').strip()


            # Validate account number length (assuming 12 digits)
            if len(account_number) != 12 or not account_number.isdigit():
                return JsonResponse({'success': False, 'error': 'Account number must be 12 digits.'})
            try:
                transaction = Transaction.objects.create(
                    user=user,
                    transaction_type='Transfer',
                    amount=Decimal(amount),  # Amount to be updated later or handled differently
                    status='pending'
                )

                code = random.randint(100000, 999999)
                VerificationCode.objects.create(
                    transaction=transaction,
                    code=code,
                    expired=False
                )

                request.session['transaction_id'] = transaction.id
                request.session['verification_code'] = str(code)

                return JsonResponse({'success': True, 'message': 'Verification code created. Please enter the code to confirm.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        else:
            # Stage 2: Validate OTP and update transaction status
            transaction_id = request.session.get('transaction_id')
            session_otp = request.session.get('verification_code')

            account_name = request.POST.get('account_name', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            note = request.POST.get('note', '').strip()

            if not transaction_id or not session_otp:
                return JsonResponse({'success': False, 'error': 'Session expired. Please try again.'})

            if str(otp) != session_otp:
                try:
                    transaction = Transaction.objects.get(id=transaction_id)
                    transaction.status = 'failed'
                    transaction.save(update_fields=['status'])
                except:
                    pass
                return JsonResponse({'success': False, 'error': 'Invalid OTP'})

            try:
                transaction = Transaction.objects.get(id=transaction_id)
                verification_code = VerificationCode.objects.get(transaction=transaction, code=int(otp), expired=False)
                if not verification_code.check_validity():
                    transaction.status = 'failed'
                    transaction.save(update_fields=['status'])
                    return JsonResponse({'success': False, 'error': 'OTP expired'})

                verification_code.expired = True
                verification_code.save()

                transaction.status = 'successful'
                transaction.save(update_fields=['status'])

                amount_decimal = Decimal(amount)
                profile.balance -= amount_decimal
                profile.save()

                # Store transaction details in session for success page
                request.session['success_transaction'] = {
                    'id': transaction.id,
                    'amount': str(transaction.amount),
                    'date_time': transaction.date_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'account_name': account_name,
                    'account_number': account_number,
                    'note': note,
                }

                return JsonResponse({'success': True})
            except VerificationCode.DoesNotExist:
                transaction = Transaction.objects.get(id=transaction_id)
                transaction.status = 'failed'
                transaction.save(update_fields=['status'])
                return JsonResponse({'success': False, 'error': 'Invalid or expired OTP'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

    else:
        selected_bank_code = request.GET.get('bank_code', '').strip()
        amount = request.GET.get('amount', '').strip()
        username = request.GET.get('username', '').strip()
        account_name = request.GET.get('account_name', '').strip()
        account_number = request.GET.get('account_number', '').strip()
        note = request.GET.get('note', '').strip()

        selected_bank = None
        if selected_bank_code:
            for bank in universal_banks:
                # keys in universal_banks are dash-case, convert to underscore for comparison
                if bank.get('bank-code') == selected_bank_code:
                    selected_bank = {
                        'bank_name': bank.get('bank-name', ''),
                        'bank_logo': bank.get('bank-logo', ''),
                        'bank_code': bank.get('bank-code', ''),
                    }
                    break

        profile = Profile.objects.get(user=user)
        context = {
            'balance': profile.balance,
            'selected_bank': selected_bank,
            'amount': amount,
            'username': username,
            'account_name': account_name,
            'account_number': account_number,
            'note': note,
        }
        return render(request, 'core/transfer-three.html', context)


@login_required
def success(request):
    success_transaction = request.session.get('success_transaction')
    send = None
    transfer = None
    transaction = None

    if success_transaction:
        transaction = {
            'id': success_transaction.get('id'),
            'amount': success_transaction.get('amount'),
            'date_time': success_transaction.get('date_time'),
        }
        # Determine if it's a send or transfer based on keys
        if 'reciever_username' in success_transaction:
            send = {
                'reciever': {
                    'username': success_transaction.get('reciever_username'),
                    'profile': {
                        'account_number': success_transaction.get('reciever_account_number')
                    }
                }
            }
        else:
            transfer = {
                'account_name': success_transaction.get('account_name'),
                'account_number': success_transaction.get('account_number'),
                'note': success_transaction.get('note'),
            }

        # Clear session data after use
        del request.session['success_transaction']

    return render(request, 'core/transfer-successful.html', {
        'send': send,
        'transfer': transfer,
        'transaction': transaction,
    })


@login_required
def amen(request):
    return render(request, 'core/amen.html')
