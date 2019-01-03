#_*_ encoding:utf-8 _*_

from django.shortcuts import render
from django.contrib.auth import authenticate,login,logout
from django.views.generic.base import View
from django.http import HttpResponse
import json
from django.contrib.auth.backends import ModelBackend
from utils.mixin_utils import LoginRequiredMixin
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger


from .models import UserProfile,EmailVerifyRecord
from django.db.models import Q
from .forms import LoginForm,RegisterForm,ForgetPwdForm,ModifyPwdForm,UploadImageFrom
from django.contrib.auth.hashers import make_password
from utils.email_send import send_register_eamil
from operation.models import UserCourse,UserFavorite,UserMessage
from organization.models import CourseOrg,Teacher
from course.models import Course

#邮箱和用户名都可以登录
# 基础ModelBackend类，因为它有authenticate方法
class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 不希望用户存在两个，get只能有一个。两个是get失败的一种原因 Q为使用并集查询
            user = UserProfile.objects.get(Q(username=username)|Q(email=username))

            # django的后台中密码加密：所以不能password==password
            # UserProfile继承的AbstractUser中有def check_password(self, raw_password):
            if user.check_password(password):
                return user
        except Exception as e:
            return None


class LoginView(View):
    def get(self,request):
        return render(request, 'login.html')

    def post(self,request):
        # 实例化
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            # 获取用户提交的用户名和密码
            # 获取用户提交的用户名和密码
            user_name = request.POST.get('username', '')
            pass_word = request.POST.get('password', '')
            # 成功返回user对象,失败None
            user = authenticate(username=user_name, password=pass_word)
            # 如果不是null说明验证成功
            if user is not None:
                if user.is_active:
                    # 只有注册激活才能登录
                    login(request, user)
                    return render(request, 'index.html')
                else:
                    return render(request, 'login.html', {'msg': '用户未激活'})
            # 只有当用户名或密码不存在时，才返回错误信息到前端
            else:
                return render(request, 'login.html', {'msg': '用户名或密码错误'})
        else:
            return render(request, 'login.html', {'login_form':login_form})


class LogoutView(View):
    def get(self,request):
        logout(request)
        return






# 激活用户
class ActiveUserView(View):
    def get(self, request, active_code):
        # 查询邮箱验证记录是否存在
        all_record = EmailVerifyRecord.objects.filter(code = active_code)

        if all_record:
            for record in all_record:
                # 获取到对应的邮箱
                email = record.email
                # 查找到邮箱对应的user
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
         # 验证码不对的时候跳转到激活失败页面
        else:
            return render(request,'active_fail.html')
        # 激活成功跳转到登录页面
        return render(request, "login.html", )


class RegisterView(View):
    '''用户注册'''
    def get(self,request):
        register_form = RegisterForm()
        return render(request,'register.html',{'register_form':register_form})

    def post(self,request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get('email', None)
            # 如果用户已存在，则提示错误信息
            if UserProfile.objects.filter(email = user_name):
                return render(request, 'register.html', {'register_form':register_form,'msg': '用户已存在'})

            pass_word = request.POST.get('password', None)
            # 实例化一个user_profile对象
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False
            # 对保存到数据库的密码加密
            user_profile.password = make_password(pass_word)
            user_profile.save()

            # 写入欢迎注册消息
            user_message = UserMessage()
            # 注意：UserMessage和UserProfile没有通过外键链接，此处传递的是id
            user_message.user = user_profile.id
            user_message.message = '欢迎注册此网站'
            user_message.save()


            # 发送邮箱验证码
            send_register_eamil(user_name,'register')
            return render(request,'login.html')
        else:
            return render(request,'register.html',{'register_form':register_form})




class ForgetPwdView(View):
    '''找回密码'''
    def get(self,request):
        forget_form = ForgetPwdForm()
        return render(request,'forgetpwd.html',{'forget_form':forget_form})

    def post(self,request):
        forget_form = ForgetPwdForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get('email',None)
            send_register_eamil(email,'forget')
            return render(request, 'send_success.html')
        else:
            return render(request,'forgetpwd.html',{'forget_form':forget_form})


class ResetView(View):
    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                return render(request, "password_reset.html", {"email": email})
        else:
            return render(request, "active_fail.html")
        return render(request, "login.html")


class ModifyPwdView(View):
    '''
    修改用户密码
    '''
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            email = request.POST.get("email", "")
            if pwd1 != pwd2:
                return render(request, "password_reset.html", {"email":email, "msg":"密码不一致！"})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd2)
            user.save()

            return render(request, "login.html")
        else:
            email = request.POST.get("email", "")
            return render(request, "password_reset.html", {"email":email, "modify_form":modify_form })


class UserinfoView(LoginRequiredMixin,View):
    '''
    个人基本信息,继承LoginRequiredMixin只有登录才可以访问的页面
    '''
    def get(self,request):
        current_page = 'info'
        return render(request,'usercenter-info.html',({
            'current_page':current_page
        }))


class UploadImageView(View):
    '''
    修改用户头像
    '''
    def post(self,request):
        # 上传的文件都在request.FILES里面获取，所以这里要多传一个这个参数
        image_from = UploadImageFrom(request.POST,request.FILES)
        if image_from.is_valid():
            image = image_from.cleaned_data['image']
            request.user.image = image
            request.user.save()
            return HttpResponse('{"status":"success" }', content_type='application/json')
        else:
            return HttpResponse('{"status":"file" }', content_type='application/json')


class UpdatePwdView(View):
    '''
    在个人中心修改密码
    '''
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")

            if pwd1 != pwd2:
                return HttpResponse('{"status":"fail","msg":"密码不一致！" }', content_type='application/json')
            user = request.user
            user.password = make_password(pwd2)
            user.save()

            return HttpResponse('{"status":"success","msg":"修改密码成功" }', content_type='application/json')
        else:
            # return HttpResponse('{"status":"fail","msg":"密码不能少于5位！" }', content_type='application/json')
            return HttpResponse(json.dumps(modify_form.errors), content_type='application/json')


class SendEmailCodeView(LoginRequiredMixin,View):
    '''
    修改邮箱发送邮箱验证码，必须先登录
    '''
    def get(self,request):
        email = request.GET.get('email','')
        if UserProfile.objects.filter(email=email):
            return HttpResponse('{"email":"邮箱已存在，请更换！" }', content_type='application/json')
        send_register_eamil(email, 'update_email')
        return HttpResponse('{"status":"success"}', content_type='application/json')


class UpdateEmailView(LoginRequiredMixin,View):
    '''
    通过验证码更改邮箱,必须先登录
    '''
    def post(self,request):
        email = request.POST.get('email','')
        code = request.POST.get('code','')
        new_email = EmailVerifyRecord.objects.filter(code=code,email=email,send_type='update_email')
        if new_email:
            user = request.user
            user.email = email
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"email":"验证码无效"}', content_type='application/json')


class MyCourseView(LoginRequiredMixin,View):
    '''
    学习课程展示
    '''
    def get(self,request):
        current_page = 'course'
        courses = UserCourse.objects.filter(user=request.user)
        return render(request,'usercenter-mycourse.html',({
            'courses':courses,
            'current_page':current_page
        }))


class MyFavOrgView(LoginRequiredMixin,View):
    '''
    用户收藏的教育机构
    '''
    def get(self,request):
        current_page = 'fav'
        current_fav_page = 'org'
        org_list = []
        # av_orgs只是存放了id。我们还需要通过id找到机构对象
        fav_orgs = UserFavorite.objects.filter(user=request.user,fav_type=2)
        for fav_org in fav_orgs:
            # 取出fav_id也就是机构的id。
            org_id = fav_org.fav_id
            # 获取这个机构对象
            org = CourseOrg.objects.get(id=org_id)
            org_list.append(org)
        return render(request,'usercenter-fav-org.html',({
            'org_list':org_list,
            'current_page':current_page,
            'current_fav_page':current_fav_page
        }))


class MyFavTeacherView(LoginRequiredMixin,View):
    '''
    用户收藏的教师
    '''
    def get(self,request):
        current_page = 'fav'
        current_fav_page = 'teacher'
        teacher_list = []
        fav_teachers = UserFavorite.objects.filter(user=request.user,fav_type=3)
        for fav_teacher in fav_teachers:
            teacher_id = fav_teacher.fav_id
            teacher = Teacher.objects.get(id = teacher_id)
            teacher_list.append(teacher)

        return render(request,'usercenter-fav-teacher.html',({
            'teacher_list':teacher_list,
            'current_page': current_page,
            'current_fav_page':current_fav_page
        }))


class MyFavCourseView(LoginRequiredMixin, View):
    '''
    用户收藏的课程
    '''
    def get(self, request):
        current_page = 'fav'
        current_fav_page = 'course'
        course_list = []
        fav_courses = UserFavorite.objects.filter(user=request.user,fav_type='1')
        for fav_course in fav_courses:
            course_id = fav_course.fav_id
            course = Course.objects.get(id = course_id)
            course_list.append(course)

        return render(request, 'usercenter-fav-course.html', ({
            'course_list':course_list,
            'current_page': current_page,
            'current_fav_page':current_fav_page
        }))


class MyMessageView(LoginRequiredMixin,View):
    '''
    用户消息
    '''
    def get(self,request):
        current_page = 'message'
        all_message = UserMessage.objects.filter(user=request.user.id)

        # 对消息进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从allorg中取五个出来，每页显示5个
        p = Paginator(all_message, 3, request=request)
        messages = p.page(page)
        return render(request,'usercenter-message.html',({
            'current_page':current_page,
            'all_message':messages
        }))













