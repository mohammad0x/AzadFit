from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import *
import jdatetime
from .forms import *
import random


def home(request):
    return render(request, 'home.html')


def login_phone(request):
    if request.user.is_authenticated:
        return redirect('fit:home')
    if request.method == 'POST':
        global phone, random_code
        phone = request.POST.get('phone')
        if MyUser.objects.filter(phone=phone).exists():
            return redirect('app:register')
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
    return render(request, 'gyms/gym_detail.html', {'gym': gym, 'images': images})


@login_required
def timeslot_list(request):
    timeslots = TimeSlot.objects.filter(is_available=True)
    return render(request, 'timeslots/timeslot_list.html', {'timeslots': timeslots})


@login_required
def reserve_time(request, timeslot_id, gym_id):
    timeslot = get_object_or_404(TimeSlot, id=timeslot_id)
    gym = get_object_or_404(Gym, id=gym_id)

    if not timeslot.is_available:
        messages.error(request, "این بازه زمانی دیگر در دسترس نیست.")
        return redirect('timeslot_list')

    Reservation.objects.create(
        time_slot=timeslot,
        gym=gym,
        user=request.user,
    )

    timeslot.is_available = False
    timeslot.save()

    messages.success(request, "رزرو با موفقیت انجام شد.")
    return redirect('user_reservations')


@login_required
def user_reservations(request):
    reservations = Reservation.objects.filter(user=request.user)
    return render(request, 'reservations/user_reservations.html', {'reservations': reservations})


@login_required
def make_payment(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        payment = Payment.objects.create(
            reservation=reservation,
            amount=amount,
            description=description,
            status=True,
            ref_id="TEST-REF-1234"
        )
        reservation.is_pey = True
        reservation.save()

        messages.success(request, "پرداخت با موفقیت ثبت شد.")
        return redirect('user_reservations')

    return render(request, 'payments/make_payment.html', {'reservation': reservation})
