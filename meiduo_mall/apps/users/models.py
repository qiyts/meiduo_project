from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # 自定义User-- mobile
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    class Meta:
        db_table = 'tb_users'
