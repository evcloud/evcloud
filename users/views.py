from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language

from rest_framework.authtoken.models import Token

from utils.permissions import APIIPRestrictor
from .forms import UserRegisterForm, PasswordChangeForm, ForgetPasswordForm, PasswordResetForm
from .models import Email
from utils.jwt import JWTokenTool

# 获取用户模型
User = get_user_model()


def get_or_create_token(user):
    """
    获取用户或为用户创建一个token，会在数据库表中产生一条token记录

    :param user: 用户对象
    :return: Token对象
    """
    token, created = Token.objects.get_or_create(user=user)
    if not token:
        return None

    return token


def reflesh_new_token(token):
    """
    更新用户的token

    :param token: token对象
    :return: 无
    """
    token.delete()
    token.key = token.generate_key()
    token.save()


def get_active_link(request, user):
    """
    获取账户激活连接

    :param request: 请求对象
    :param user: 用户对象
    :return: 正常: url
            错误：None
    """
    token = get_or_create_token(user=user)
    if not token:
        return None

    try:
        active_link = reverse('users:active')
    except Exception:
        return None

    active_link = request.build_absolute_uri(active_link)
    active_link += f'?token={token.key}'
    return active_link


def send_active_url_email(request, to_email, user):
    """
    发送用户激活连接邮件

    :param to_email: 邮箱
    :param user: 用户对象
    :return: True(发送成功)，False(发送失败)
    """
    active_link = get_active_link(request, user)
    if not active_link:
        return False

    message = f"""
        亲爱的用户：
            欢迎使用EVCloud,您已使用本邮箱成功注册账号，请访问下面激活连接以激活账户,如非本人操作请忽略此邮件。
            激活连接：{active_link}
        """
    if get_language() == 'en':
        message = f"""
                Dear user
                    Welcome to EVCloud. You have successfully registered your account using this email. Please visit the activation link below to activate your account. If it is not your own operation, please ignore this email.
                    Activate Connection：{active_link}
                """
    return send_one_email(subject=_('EVCloud账户激活'), receiver=to_email, message=message, log_message=active_link)


def send_one_email(receiver, message, subject='EVCloud', log_message=''):
    """
    发送一封邮件

    :param subject: 标题
    :param receiver: 接收邮箱
    :param message: 邮件内容
    :param log_message: 邮件记录中要保存的邮件内容(邮件内容太多，可以只保存主要信息)
    :return: True(发送成功)，False(发送失败)
    """
    email = Email()
    email.message = log_message
    ok = email.send_email(subject=subject, receiver=receiver, message=message)
    if ok:
        return True
    return False


def register_user(request):
    """
    用户注册函数视图
    """
    use_register = getattr(settings, 'USE_REGISTER_USER', False)
    if not use_register:
        return render(request, 'message.html', context={'message': _('不允许个人注册，请联系管理员')})

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        # 表单数据验证通过
        if form.is_valid():
            user = form.get_or_creat_unactivated_user()
            if user:
                logout(request)  # 登出用户（确保当前没有用户登陆）

                # 向邮箱发送激活连接
                if send_active_url_email(request, user.email, user):
                    return render(request, 'message.html',
                                  context={'message': _('用户注册成功，请登录邮箱访问收到的连接以激活用户')})

                form.add_error(None, _('邮件发送失败，请检查邮箱输入是否有误'))
            else:
                form.add_error(None, _('用户注册失败，保存用户数据是错误'))
    else:
        form = UserRegisterForm()

    content = {'form_title': _('用户注册'), 'submit_text': _('注册'), 'action_url': reverse('users:register'),
               'form': form}
    return render(request, 'form.html', content)


def active_user(request):
    """
    激活用户
    :param request:
    :return:
    """
    urls = []
    try:
        urls.append({'url': reverse('users:login'), 'name': _('登录')})
        urls.append({'url': reverse('users:register'), 'name': _('注册')})
    except Exception:
        pass

    key = request.GET.get('token', None)
    try:
        token = Token.objects.select_related('user').get(key=key)
    except Token.DoesNotExist:
        return render(request, 'message.html',
                      context={'message': _('用户激活失败，无待激活账户，或者账户已被激活，请直接尝试登录'), 'urls': urls})

    user = token.user
    user.is_active = True
    user.save()

    reflesh_new_token(token)

    return render(request, 'message.html', context={'message': _('用户已激活'), 'urls': urls})


@login_required
def change_password(request):
    """
    修改密码函数视图
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            # 修改密码
            new_password = form.cleaned_data['new_password']
            user = request.user
            user.set_password(new_password)
            user.save()

            # 注销当前用户，重新登陆
            logout(request)
            return redirect(to=reverse('users:login'))
    else:
        form = PasswordChangeForm()

    content = {'form_title': _('修改密码'), 'submit_text': _('修改'),
               'action_url': reverse('users:change_password'), 'form': form}
    return render(request, 'form.html', content)


def forget_password(request):
    """
    忘记密码视图
    """
    if request.method == 'POST':
        form = ForgetPasswordForm(request.POST)
        if form.is_valid():
            urls = []
            try:
                urls.append({'url': reverse('users:login'), 'name': _('登录')})
            except Exception:
                pass

            user = form.cleaned_data['user']
            email = form.cleaned_data['username']
            # new_password = form.cleaned_data.get('new_password')
            # user.email = new_password # 用于email字段暂存要重置的密码
            # 是否是未激活的用户
            if not user.is_active:
                if send_active_url_email(request, email, user):
                    return render(request, 'message.html', context={
                        'message': _('用户未激活，请先登录邮箱访问收到的链接以激活用户'), 'urls': urls})

                form.add_error(None, _('邮件发送失败，请检查用户名输入是否有误，稍后重试'))
            else:
                if send_forget_password_email(request, email, user):
                    return render(request, 'message.html', context={
                        'message': _(
                            '重置密码确认邮件已发送，请尽快登录邮箱访问收到的链接以完成密码重置，以防链接过期无效')})

                form.add_error(None, _('邮件发送失败，请检查用户名输入是否有误，稍后重试'))
    else:
        form = ForgetPasswordForm()

    content = {'form_title': _('找回密码'), 'submit_text': _('提交'), 'form': form}
    return render(request, 'form.html', content)


def forget_password_confirm(request):
    """
    忘记密码链接确认，完成密码修改
    :param request:
    :return:
    """
    urls = []
    try:
        urls.append({'url': reverse('users:login'), 'name': _('登录')})
        urls.append({'url': reverse('users:register'), 'name': _('注册')})
    except Exception:
        pass

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('new_password')
            user = form.cleaned_data.get('user')
            user.set_password(password)
            user.save()
            return render(request, 'message.html', context={'message': _('用户重置密码成功，请尝试登录'), 'urls': urls})
    else:
        jwtt = JWTokenTool()
        try:
            ret = jwtt.authenticate_query(request)
        except Exception:
            ret = None
        if not ret:
            return render(request, 'message.html',
                          context={'message': _('链接无效或已过期，请重新找回密码获取新的链接'), 'urls': urls})

        jwt_value = ret[-1]
        form = PasswordResetForm(initial={'jwt': jwt_value})

    content = {'form_title': _('重置密码'), 'submit_text': _('确定'), 'form': form}
    return render(request, 'form.html', context=content)


def send_forget_password_email(request, to_email, user):
    """
    发送忘记密码连接邮件

    :param to_email: 邮箱
    :param user: 用户对象
    :return: True(发送成功)，False(发送失败)
    """
    link = get_find_password_link(request, user)
    if not link:
        return False

    message = f"""
        亲爱的用户：
            欢迎使用EVCloud,您正在为以本邮箱注册的账号找回密码，请访问下面连接以完成账户密码修改,如非本人操作请忽略此邮件。
            连接：{link}
        """
    if get_language() == 'en':
        message = f"""
                Dear user
                    Welcome to EVCloud. You are currently trying to retrieve the password for the account registered with this email. Please visit the link below to complete the account password modification. If it is not your own operation, please ignore this email.
                    link：{link}
                """
    return send_one_email(subject=_('EVCloud账户找回密码'), receiver=to_email, message=message, log_message=link)


def get_find_password_link(request, user):
    """
    获取找回密码连接
    :param request:
    :param user:
    :return: 正常：url; 错误：None
    """
    jwt = JWTokenTool()
    token = jwt.obtain_one_jwt(user=user)
    if not token:
        return None

    try:
        url = reverse('users:forget_confirm')
    except Exception:
        return None

    url = request.build_absolute_uri(url)
    return url + '?jwt=' + token


class CustomLoginView(LoginView):

    # template_name = 'login.html'
    def dispatch(self, request, *args, **kwargs):

        response = super().dispatch(request, *args, **kwargs)

        try:
            APIIPRestrictor().check_restricted(request=self.request)
        except Exception as e:
            ip_error = str(e)
            return render(request=request, template_name=self.template_name, context={'ip_error': ip_error})

        return response
