#_*_ encoding:utf-8 _*_
from django import forms
from captcha.fields import CaptchaField

from .views import UserProfile

# 登录表单验证
class LoginForm(forms.Form):
    # 用户名密码不能为空
    username = forms.CharField(required=True)
    password = forms.CharField(required=True,min_length=5)


class RegisterForm(forms.Form):
    '''注册验证表单'''
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True,min_length=5)
    # 验证码，字段里面可以自定义错误提示信息
    captcha = CaptchaField(error_messages={'invalid':'验证码错误'})


class ForgetPwdForm(forms.Form):
    '''忘记密码'''
    email = forms.EmailField(required=True)
    captcha = CaptchaField(error_messages={'invalid': '验证码错误'})


class ModifyPwdForm(forms.Form):
    '''重置密码'''
    password1 = forms.CharField(required=True, min_length=5)
    password2 = forms.CharField(required=True, min_length=5)


class UploadImageFrom(forms.ModelForm):
    '''
    修改用户头像
    '''
    class Meta:
        model = UserProfile
        fields = ['image']
