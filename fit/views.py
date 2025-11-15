from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import *
import jdatetime
from .forms import *
import random
import requests
import json
from kavenegar import *
from .zarinpal import *


def home(request):
    return render(request, 'home.html')


def login_phone(request):
    if request.user.is_authenticated:
        return redirect('fit:home')
    if request.method == 'POST':
        global phone, random_code
        phone = request.POST.get('phone')
        random_code = random.randint(10000, 99999)
        print(random_code)
        # sms = KavenegarAPI(
        #     "***************")  #
        # params = {
        #     'sender': '2000660110',
        #     'receptor': phone,  #
        #     'message': f' {random_code} سلام این اولین تست است ',
        # }
        # response = sms.sms_send(params)
        return redirect('fit:register')

    return render(request, 'accounts/login.html')


def verify_login_phone(request):
    if request.user.is_authenticated:
        return redirect('fit:home')
    if request.method == 'POST':
        form = CodePhoneForm(request.POST)
        if form.is_valid():
            if str(random_code) == form.cleaned_data['verify_code']:
                if MyUser.objects.filter(phone=phone).exists():
                    user = authenticate(request, phone=phone)
                    if user is not None:
                        login(request, user)
                        return redirect('fit:home')

                # sign up
                user = MyUser.objects.create_user(phone=phone)
                user.save()

                # sign in
                user = authenticate(request, phone=phone)
                if user is not None:
                    login(request, user)
                    return redirect('fit:home')

                global verify
                verify = True
                return redirect('fit:home')
            else:
                messages.error(request, 'کد وارد شده اشتباه است', 'danger')
    else:
        form = CodePhoneForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/verify-login-phone.html', context)


def logout_view(request):
    logout(request)
    return redirect('fit:login')


def gym_list(request):
    gyms = Gym.objects.all().order_by('-created_jalali')
    return render(request, 'gyms/gym_list.html', {'gyms': gyms})


def gym_detail(request, slug):
    gym = get_object_or_404(Gym, slug=slug)
    images = gym.images.all()
    timeslots = TimeSlot.objects.filter(is_available=True)

    context = {
        'gym': gym,
        'images': images,
        'timeslots': timeslots,
    }

    return render(request, 'gyms/gym_detail.html', context)


# @login_required
# def timeslot_list(request):
#     timeslots = TimeSlot.objects.filter(is_available=True)
#     return render(request, 'timeslots/timeslot_list.html', {'timeslots': timeslots})


@login_required(login_url="/login/")
def reserve_time(request, timeslot_id, gym_id):
    timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
    gym = get_object_or_404(Gym, id=gym_id)

    if not timeslot.is_available:
        messages.error(request, "این بازه زمانی دیگر در دسترس نیست.")
        return redirect('fit:gym_list')

    if Reservation.objects.filter(user=request.user, time_slot=timeslot).exists():
        messages.error(request, "قبلا رزرو شده")
        return redirect('fit:user_reservations')

    Reservation.objects.create(
        time_slot=timeslot,
        gym=gym,
        user=request.user,
    )

    # timeslot.is_available = False
    # timeslot.save()

    messages.success(request, "رزرو با موفقیت انجام شد.")
    return redirect('fit:user_reservations')


@login_required(login_url="/login/")
def user_reservations(request):
    global pricee
    pricee = 0
    reservations = Reservation.objects.filter(user=request.user,is_pey=False)
    if Reservation.objects.filter(user=request.user.id, is_pey=False, contract=False).exists():
        for reservation in reservations:
            pricee += int(reservation.gym.price)
    return render(request, 'reservations/user_reservations.html', {'reservations': reservations , 'price':pricee})

@login_required(login_url="/login/")
def history(request):
    reservations = Reservation.objects.filter(user=request.user, is_pey=True)
    return render(request , 'history/history.html' , {'reservations':reservations})


def reservDelete(request , id):
    Reservation.objects.filter(user = request.user , id = id).delete()
    return redirect('fit:user_reservations')


@login_required(login_url="/login/")
def request_payment(request):
    if request.method == 'POST':
        global amount
        amount = request.POST['amount']
        description = request.POST['description']

        if str(pricee) == str(amount):
            data = {
                "merchant_id": settings.MERCHANT,
                "amount": amount,
                "description": description,
                "callback_url": CallbackURL,
            }
            data = json.dumps(data)

            headers = {'content-type': 'application/json', 'content-length': str(len(data))}

            response = requests.post(ZP_API_REQUEST, data=data, headers=headers)

            if response.status_code == 200:
                response = response.json()

                if response["data"]['code'] == 100:
                    url = f"{ZP_API_STARTPAY}{response['data']['authority']}"
                    return redirect(url)

                else:
                    messages.error(request, f'{str(response["errors"])}', 'danger')
                    return redirect('fit:user_reservations')

            else:
                messages.error(request, 'مشکلی پیش آمد.', 'danger')
                return redirect('fit:user_reservations')
        else:
            return redirect('fit:user_reservations')
    return redirect('fit:user_reservations')


@login_required(login_url="/login/")
def verify(request):
    status = request.GET.get('Status')
    authority = request.GET['Authority']

    if status == "OK":
        data = {
            "merchant_id": settings.MERCHANT,
            "amount": amount,
            "authority": authority
        }
        data = json.dumps(data)

        headers = {'content-type': 'application/json', 'Accept': 'application/json'}

        response = requests.post(ZP_API_VERIFY, data=data, headers=headers)
        if response.status_code == 200:
            response = response.json()
            if response['data']['code'] == 100:
                # put your logic here
                reserv = Reservation.objects.filter(user=request.user.id)
                for res in reserv:
                    if not res.is_pey:
                        Payment.objects.create(reservation_id =res.id,amount=amount,status=True)
                        TimeSlot.objects.filter(id=res.time_slot.id).update(is_available=False)
                Reservation.objects.filter(user=request.user.id).update(is_pey=True, contract=True)

                messages.success(request, 'خرید شما با موفقیت انجام شد.', 'success')
                return redirect('fit:history')

            elif response['data']['code'] == 101:
                messages.error(request, 'این پرداخت قبلا انجام شده است.', 'danger')
                return redirect('fit:history')

            else:
                messages.error(request, 'پرداخت شما ناموفق بود.', 'danger')
                return redirect('fit:user_reservations')

        else:
            messages.error(request, 'پرداخت شما ناموفق بود.', 'danger')
            return redirect('fit:user_reservations')


    else:
        messages.error(request, 'پرداخت شما ناموفق بود.', 'danger')
        return redirect('fit:user_reservations')
