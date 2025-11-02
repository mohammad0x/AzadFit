from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
import jdatetime


class MyUserManager(BaseUserManager):
    def create_user(self, phone, verify_code, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not phone:
            raise ValueError("Users must have an phone number")

        user = self.model(
            phone=phone,
            verify_code=verify_code,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, verify_code, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            phone,
            password=password,
            verify_code=verify_code,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser):
    phone = models.CharField(max_length=11, unique=True, verbose_name="شماره تلفن")
    verify_code = models.CharField(max_length=5, verbose_name="کد تایید")
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["verify_code"]

    def __str__(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Gym(models.Model):
    name = models.CharField(max_length=150, blank=False, null=False, verbose_name="نام")
    slug = models.CharField(max_length=150, unique=True, blank=False, null=False, verbose_name="عنوان")
    address = models.CharField(max_length=150, verbose_name="آدرس")
    description = models.TextField(verbose_name="توضیحات")
    price = models.CharField(max_length=150, verbose_name="قیمت")
    created_jalali = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت پست")
    contract = models.TextField(blank=False, null=False, verbose_name="متن قرار داد")

    def __str__(self):
        return self.name

    @property
    def created_jalali_full(self):
        return self.created_jalali.strftime('%Y/%m/%d - %H:%M')


class Image(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class TimeSlot(models.Model):
    DAYS_OF_WEEK = [
        (0, 'شنبه'),
        (1, 'یکشنبه'),
        (2, 'دوشنبه'),
        (3, 'سه شنبه'),
        (4, 'چهارشنبه'),
        (5, 'پنجشنبه'),
        (6, 'جمعه'),
    ]

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="روز های هفته")
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")
    is_available = models.BooleanField(default=True, verbose_name="وضعیت")
    date = models.DateField(verbose_name="تاریخ شمسی")

    class Meta:
        ordering = ['date', 'start_time']

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = jdatetime.date.today()
        super().save(*args, **kwargs)

    def get_jalali_date(self):
        return jdatetime.date.fromgregorian(date=self.date)

    def get_day_display(self):
        """نمایش نام روز بر اساس choices"""
        for day_num, day_name in self.DAYS_OF_WEEK:
            if day_num == self.day_of_week:
                return day_name
        return "نامشخص"

    def __str__(self):
        return f"{self.get_day_display()} {self.get_jalali_date()} - {self.start_time} تا {self.end_time}"


class Reservation(models.Model):
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    contract = models.BooleanField(default=False, verbose_name="وضعیت قرار داد")
    is_pey = models.BooleanField(default=False, verbose_name="پرداخت")
    created_jalali = models.DateTimeField(auto_now_add=True)

    @property
    def created_jalali_full(self):
        return self.created_jalali.strftime('%Y/%m/%d - %H:%M')


class Payment(models.Model):
    gym = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name="مبلغ به ریال")
    description = models.TextField(verbose_name="توضیحات")
    ref_id = models.CharField(max_length=255, blank=True, verbose_name="کد پیگیری")
    status = models.BooleanField(default=False, verbose_name="وضعیت پرداخت")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.gym.name} - {self.amount}"

    @property
    def created_jalali_full(self):
        return self.created.strftime('%Y/%m/%d - %H:%M')
