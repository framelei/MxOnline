from django.shortcuts import render
from django.views.generic import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.db.models import Q

from .models import Course,CourseResource,Video
from operation.models import UserFavorite,CourseComments,UserCourse
from apps.utils.mixin_utils import LoginRequiredMixin

class CourseListView(View):
    def get(self, request):
        all_courses = Course.objects.all().order_by('-add_time')
        # 根据点击量选出热门课程前三名，用于推荐
        hot_courses = Course.objects.all().order_by('-click_nums')[:3]

        # 课程搜索
        search_keywords = request.GET.get('keywords','')
        if search_keywords:
            all_courses = all_courses.filter(Q(name__icontains=search_keywords)|Q(desc__icontains=search_keywords)
                                             |Q(detail__icontains=search_keywords))

        # 课程分页，一定要先分页再排序
        sort = request.GET.get('sort', '')
        if sort:
            # 参与人数按学生数量降序排列：
            if sort == 'students':
                all_courses = all_courses.order_by('-students')
            # 最热门按收藏排列：
            elif sort == 'hot':
                all_courses = all_courses.order_by('-fav_nums')

        # 对课程进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从all_courses中取五个出来，每页显示5个
        p = Paginator(all_courses, 6, request=request)
        courses = p.page(page)

        return render(request, "course-list.html", {
            'all_courses': courses,
            'sort':sort,
            'hot_courses':hot_courses
        })


class CourseDetailView(View):
    '''课程详情'''
    def get(self, request, course_id):

        course = Course.objects.get(id=int(course_id))
        # 课程的点击数加1
        course.click_nums += 1
        course.save()

        # 是否收藏课程
        has_fav_course = False
        # 是否收藏机构
        has_fav_org = False
        # 必须是用户已登录我们才需要判断。
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course.id, fav_type=1):
                has_fav_course = True
            if UserFavorite.objects.filter(user=request.user, fav_id=course.course_org.id, fav_type=2):
                has_fav_org = True

        # 课程标签
        # 通过当前标签，查找数据库中的课程
        tag = course.tag
        if tag:
            # 需要从1开始不然会推荐自己
            relate_courses = Course.objects.filter(tag=tag)[1:3]
        else:
            relate_courses = []
        return render(request, "course-detail.html", {
            'course': course,
            'relate_courses': relate_courses,
            "has_fav_course": has_fav_course,
            "has_fav_org": has_fav_org,
        })


class CourseInfoView(LoginRequiredMixin,View):
    """
    课程章节信息
    """
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))

        #查询用户是否已经关联了该课程
        user_courses = UserCourse.objects.filter(user =request.user,course=course)
        # 如果没有关联，让他们关联起来
        if not user_courses:
            user_course = UserCourse(user = request.user,course= course)
            user_course.save()

        # 找到学习这门课的所有用户
        user_courses = UserCourse.objects.filter(course = course)
        # 找到学习这门课的所有用户的id
        user_ids = [user_course.user.id for user_course in user_courses]
        # 通过所有用户的id,找到所有用户学习过的所有课程
        all_user_courses = UserCourse.objects.filter(user_id__in= user_ids)
        # 取出所有课程id
        course_ids = [all_user_course.course.id for all_user_course in all_user_courses]
        # 通过所有课程的id,找到所有的课程，按收藏数取五个
        relate_courses = Course.objects.filter(id__in = course_ids).order_by('-fav_nums')[:5]

        # 课程资源
        all_resources = CourseResource.objects.filter(course = course)
        return render(request,'course-video.html',{
            'course': course,
            'course_resources':all_resources,
            'relate_courses':relate_courses
        })


class CommentsView(LoginRequiredMixin,View):
    """
    课程评论
    """
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))

        # 查询用户是否已经关联了该课程
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        # 如果没有关联，让他们关联起来
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()

        # 找到学习这门课的所有用户
        user_courses = UserCourse.objects.filter(course=course)
        # 找到学习这门课的所有用户的id
        user_ids = [user_course.user.id for user_course in user_courses]
        # 通过所有用户的id,找到所有用户学习过的所有课程
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 取出所有课程id
        course_ids = [all_user_course.course.id for all_user_course in all_user_courses]
        # 通过所有课程的id,找到所有的课程，按收藏数取五个
        relate_courses = Course.objects.filter(id__in=course_ids).order_by('-fav_nums')[:5]

        # 课程资源
        course_resources = CourseResource.objects.filter(course=course)
        all_comments = CourseComments.objects.filter(course=course).order_by('-add_time')
        return render(request,'course-comment.html',{
            'course': course,
            'course_resources':course_resources,
            'all_comments':all_comments,
            'relate_courses':relate_courses
        })


class AddCommentsView(View):
    """
        用户课程评论
    """

    def post(self,request):
        if not request.user.is_authenticated:
            # 未登录时返回json提示未登录，跳转到登录页面是在ajax中做的
            return HttpResponse('{"status":"fail", "msg":"用户未登录"}', content_type='application/json')

        course_id = request.POST.get('course_id',0)
        comments = request.POST.get('comments','')
        if int(course_id) > 0 and comments:
            course_comments = CourseComments()
            course = Course.objects.get(id = int(course_id))
            course_comments.course = course
            course_comments.comments = comments
            course_comments.user = request.user
            course_comments.save()
            return HttpResponse('{"status":"success", "msg":"评论添加成功"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail", "msg":"评论添加失败"}', content_type='application/json')


class VideoPlayView(LoginRequiredMixin, View):
    '''课程章节视频播放页面'''
    def get(self,request,video_id):
        video = Video.objects.get(id=int(video_id))
        #通过外键找到章节再找到视频对应的课程
        course = video.lesson.course

        course.students += 1
        course.save()

        # 查询用户是否已经学习了该课程
        user_courses = UserCourse.objects.filter(user=request.user,course=course)
        if not user_courses:
            # 如果没有学习该门课程就关联起来
            user_course = UserCourse(user=request.user,course=course)
            user_course.save()

        #相关课程推荐
        # 找到学习这门课的所有用户
        user_courses = UserCourse.objects.filter(course=course)
        # 找到学习这门课的所有用户的id
        user_ids = [user_course.user_id for user_course in user_courses]
        # 通过所有用户的id,找到所有用户学习过的所有过程
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 取出所有课程id
        course_ids = [all_user_course.course_id for all_user_course in all_user_courses]
        # 通过所有课程的id,找到所有的课程，按点击量去五个
        relate_courses = Course.objects.filter(id__in=course_ids).order_by("-click_nums")[:5]

        # 资源
        all_resources = CourseResource.objects.filter(course=course)
        return render(request,'course-play.html',{
            'course':course,
            'all_resources':all_resources,
            'relate_courses':relate_courses,
            'video':video,
        })









