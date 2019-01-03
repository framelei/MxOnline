from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from django.http import HttpResponse
from django.db.models import Q

from .models import CourseOrg,CityDict,Teacher
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from .forms import UserAskForm
from operation.models import UserFavorite
from course.models import Course

class OrgView(View):
    '''课程机构'''

    def get(self, request):
        # 所有课程机构
        all_orgs = CourseOrg.objects.all()

        # 所有城市
        all_citys = CityDict.objects.all()

        # 筛选课程机构关键词
        search_keywords = request.GET.get('keywords','')
        all_orgs = all_orgs.filter(Q(name__icontains=search_keywords)|Q(desc__icontains=search_keywords))


        #取出筛选城市
        city_id = request.GET.get('city', '')
        if city_id:
            all_orgs = all_orgs.filter(city_id=int(city_id))

        # 类别筛选
        category = request.GET.get('ct', '')
        if category:
            all_orgs = all_orgs.filter(category=category)
        # 有多少家符合两种条件的机构
        org_nums = all_orgs.count()
        # 对课程机构进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从allorg中取五个出来，每页显示5个
        p = Paginator(all_orgs, 5, request=request)
        orgs = p.page(page)

        return render(request, "org-list.html", {
            "all_orgs": orgs,
            "all_citys": all_citys,
            "org_nums": org_nums,
            'city_id' : city_id,
            'category': category
        })


class AddUserAskView(View):
    def post(self,request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            user_ask = userask_form.save(commit=True)
            return HttpResponse('{"status":"success"}',content_type='application/json')
        else:
            return HttpResponse('{"status":"fail","msg": "添加出错"}',content_type='application/json')


class OrgHomeView(View):
    def get(self, request, org_id):
        #用于判断当前页面是否被选中
        current_page = 'home'
        # 根据id找到课程机构
        course_org = CourseOrg.objects.get(id=int(org_id))
        # 反向查询到课程机构的所有课程和老师
        all_courses = course_org.course_set.all()[:4]
        all_teacher = course_org.teacher_set.all()[:2]
        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-homepage.html', {
            'course_org': course_org,
            'all_courses': all_courses,
            'all_teacher': all_teacher,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgCourseView(View):
    """
      机构课程列表页
    """
    def get(self, request, org_id):
        #用于判断当前页面是否被选中
        current_page = 'course'
        # 根据id取到课程机构
        course_org = CourseOrg.objects.get(id=int(org_id))
        # 通过课程机构找到课程。内建的变量，找到指向这个字段的外键引用
        all_courses = course_org.course_set.all()
        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-course.html', {
            'all_courses': all_courses,
            'course_org': course_org,
            'current_page':current_page,
            'has_fav': has_fav,
        })



class OrgDescView(View):
    '''机构介绍页'''

    def get(self, request, org_id):
        # 用于判断当前页面是否被选中
        current_page = 'desc'
        # 根据id取到课程机构
        course_org = CourseOrg.objects.get(id=int(org_id))
        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-desc.html', {
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgTeacherView(View):
    """
       机构教师页
    """
    def get(self, request, org_id):
        current_page = 'teacher'
        course_org = CourseOrg.objects.get(id=int(org_id))
        all_teacher = course_org.teacher_set.all()
        # 判断收藏状态
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-teachers.html', {
            'all_teacher': all_teacher,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class AddFavView(View):
    """
        用户收藏和取消收藏
    """
    def post(self, request):
        id = request.POST.get('fav_id', 0)  # 防止后边int(fav_id)时出错
        type = request.POST.get('fav_type', 0)  # 防止int(fav_type)出错

        if not request.user.is_authenticated:
            # 未登录时返回json提示未登录，跳转到登录页面是在ajax中做的
            return HttpResponse('{"status":"fail", "msg":"用户未登录"}', content_type='application/json')

        exist_record = UserFavorite.objects.filter(user=request.user, fav_id=int(id), fav_type=int(type))
        if exist_record:
            # 如果记录已经存在，表示用户取消收藏
            exist_record.delete()
            return HttpResponse('{"status":"success", "msg":"收藏"}', content_type='application/json')
        else:
            user_fav = UserFavorite()
            if int(id) > 0 and int(type) > 0:
                user_fav.user = request.user
                user_fav.fav_id = int(id)
                user_fav.fav_type = int(type)
                user_fav.save()
                return HttpResponse('{"status":"success", "msg":"已收藏"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail", "msg":"收藏出错"}', content_type='application/json')


class TeacherListView(View):
    '''
    讲师列表页
    '''
    def get(self,request):
        all_teachers = Teacher.objects.all()
        teacher_nums = all_teachers.count()

        # 教师搜索
        search_keywords = request.GET.get('keywords','')
        all_teachers = all_teachers.filter(name__icontains=search_keywords)

        # 人气排序
        sort = request.GET.get('sort','')
        if sort:
            if sort == 'hot':
                all_teachers = all_teachers.order_by('-click_nums')

        # 讲师排名
        sorted_teacher = Teacher.objects.order_by('-click_nums')[:3]


        # 对教师进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从allorg中取五个出来，每页显示5个
        p = Paginator(all_teachers, 3, request=request)
        teachers = p.page(page)
        return render(request,'teachers-list.html',{
            'all_teachers':teachers,
            'teacher_nums':teacher_nums,
            'sort':sort,
            'sorted_teacher':sorted_teacher,
        })


class TeacherDetailView(View):
    '''
    讲师详情页
    '''
    def get(self, request,teacher_id):
        teacher = Teacher.objects.get(id=int(teacher_id))
        teacher.click_nums += 1
        teacher.save()

        all_courses = Course.objects.filter(teacher=teacher)

        # 默认不收藏教师，如果同时满足（用户、id、type=3），改为True。3代表讲师
        has_teacher_faved = False
        if UserFavorite.objects.filter(user = request.user,fav_id=teacher.id,fav_type=3):
            has_teacher_faved = True

        #收藏培训机构
        has_org_faved = False
        if UserFavorite.objects.filter(user=request.user, fav_id=teacher.org.id, fav_type=2):
            has_org_faved = True

        # 讲师排名
        sorted_teacher = Teacher.objects.order_by('-click_nums')[:3]

        return render(request,'teacher-detail.html',{
            'teacher':teacher,
            'all_courses':all_courses,
            'sorted_teacher':sorted_teacher,
            'has_teacher_faved':has_teacher_faved,
            'has_org_faved':has_org_faved,
        })
