from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.conf import settings


class UserProfile(AbstractUser):
    """
    自定义用户模型
    """
    telephone = models.CharField(verbose_name='电话', max_length=11, default='')
    company = models.CharField(verbose_name='公司/单位', max_length=255, default='')
    # api_user = models.BooleanField(verbose_name='API用户', default=False, help_text='指明是否是API用户')

    def get_full_name(self):
        if self.last_name.encode('UTF-8').isalpha() and self.first_name.encode('UTF-8').isalpha():
            return f'{self.first_name} {self.last_name}'

        return f'{self.last_name}{self.first_name}'


class Email(models.Model):
    """
    邮箱
    """
    email_host = models.CharField(max_length=255)
    sender = models.EmailField(verbose_name='发送者')
    receiver = models.EmailField(verbose_name='接收者')
    message = models.CharField(verbose_name='邮件内容', max_length=1000)
    send_time = models.DateTimeField(verbose_name='发送时间', auto_now_add=True)

    class Meta:
        verbose_name = '邮件'
        verbose_name_plural = verbose_name

    def send_email(self, subject='EVCloud', receiver=None, message=None):
        """
        发送用户激活邮件

        :param subject: 标题
        :param receiver: 接收者邮箱
        :param message: 邮件内容
        :return: True(发送成功)；False(发送失败)
        """
        if receiver:
            self.receiver = receiver
        # if message:
        #     self.message = message
        self.sender = settings.EMAIL_HOST_USER
        self.email_host = settings.EMAIL_HOST

        ok = send_mail(
            subject=subject,  # 标题
            message=message,  # 内容
            from_email=self.sender,  # 发送者
            recipient_list=[self.receiver],  # 接收者
            # html_message=self.message,        # 内容
            fail_silently=True,  # 不抛出异常
        )
        if ok == 0:
            return False

        self.save()  # 邮件记录
        return True
