from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class UserProfile(AbstractUser):
    '''
    自定义用户模型
    '''
    api_user = models.BooleanField(verbose_name='API用户', default=False, help_text='指明是否是API用户')

    def get_full_name(self):
        if self.last_name.encode('UTF-8').isalpha() and self.first_name.encode('UTF-8').isalpha():
            return f'{self.first_name} {self.last_name}'

        return f'{self.last_name}{self.first_name}'
