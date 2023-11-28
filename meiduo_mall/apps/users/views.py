import json, re

from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection

from apps.users.models import User


# 1. 判断用户名是否重复
"""
1.考虑的数据--创建用户数据
2.考虑的开发思路
接口文档
url：/usernames/手机号/
请求参数：路径参数
        参数名称   类型 是否必 参数含义
        username    str  是   用户名
请求方式：GET

响应格式：
        json
        参数名称   类型 参数含义
         msg      str  提示信息
         number   int  0 查无此人 1 代表重复
         
"""


def usernamecountview(request, username):
    # 1. 接收参数
    # 2. 校验参数
    # 3. 查询是否重复
    count = User.objects.filter(username=username).count()

    # 4. 返回
    return JsonResponse({'code': 0, 'errmsg': "用户名重复666", 'count': count})


# 注册的接口
"""
    url: /register/
    method: POST
    param:
          username       str  5-20字符数字字母—_
          password       str  8-20位密码 
          mobile       str    11位
          password2       str 8-20位密码 
          smscode       str   4位6位
    response：
          code 0 成功， 1失败
          errmsg str 提示信息
"""


class RegisterView(View):
    def post(self, request):
        # 1.接收参数-解析--body类型是bytes ==> json.loads()
        data_dict = json.loads(request.body)

        username = data_dict.get('username')
        password = data_dict.get('password')

        password2 = data_dict.get('password2')
        mobile = data_dict.get('mobile')
        # 获取前端输入短信验证码
        sms_code = data_dict.get('sms_code')

        allow = data_dict.get('allow')

        print(data_dict)

        # 2.校验参数--后端校验自己的 和前端无关
        # 判空
        if not all([username, password, password2, mobile, sms_code]):
            return JsonResponse({'code': 400, 'errmsg': '参数不齐'})

        # 判断参数是否有效
        if not re.match('^\w{5,20}$', username):
            return JsonResponse({'code': 400, 'errmsg': '用户名5-20位数字字母下划线'})

        if not re.match('^.{8,20}$', password):
            return JsonResponse({'code': 400, 'errmsg': '密码8-20位'})

        if not re.match('^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机号格式不正确'})

        # 两次密码是否一致
        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '两次密码必须一致！'})

        if not allow:
            return JsonResponse({'code': 400, 'errmsg': '必须同意用户协议！'})

        #  判断 短信验证码 是否正确
        # 从redis数据库获取后端存储的验证码
        redis_client = get_redis_connection('verify_code')
        sms_code_redis_bytes = redis_client.get(f'sms_{mobile}')
        if not sms_code_redis_bytes:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码失效了'})

        if sms_code != sms_code_redis_bytes.decode():
            return JsonResponse({'code': 400, 'errmsg': '短信验证码错误'})



        # 3.注册用户--Mysql-- 密码加密问题
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
            user.save()
        except Exception as e:
            settings.LOGGER.error(e)
            return JsonResponse({'code': 400, 'errmsg': '注册失败'})

        # 保持登录状态
        login(request, user)


        # 4. 返回
        return JsonResponse({'code': 0, 'errmsg': '注册成功了'})
