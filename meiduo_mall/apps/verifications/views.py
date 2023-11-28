import random

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from meiduo_mall.utils.captcha.captcha import captcha


"""
url:  /smscode/uuid/imgcode/mobile/
method: GET
params: 
       uuid
       imgcode
       mobile
       
response:json
       code 0 
       errmsg 短信发送成功！
         
"""
class SmsCodeView(View):
    def get(self, request, mobile):
        data_dict = request.GET
        img_code_front = data_dict.get('image_code')
        uuid = data_dict.get('image_code_id')

        # 判空， 正则校验uuid

        # 判断 图片验证码是否正确
        # 根据 uuid 去redis数据库取出 后端存储的图片验证码值 做对比
        redis_client = get_redis_connection('verify_code')
        # 注意点： python 读取redis的数据 返回类型是 bytes
        img_code_redis_bytes = redis_client.get(f'img_{uuid}')
        if not img_code_redis_bytes:
            return JsonResponse({'code':400, 'errmsg':"图片验证码已失效！"})

        # 只要用过了验证码， 就失效了
        redis_client.delete(f'img_{uuid}')

        # 判断是否相等
        if img_code_front.lower() != img_code_redis_bytes.decode('utf-8').lower() :
            return JsonResponse({'code':400, 'errmsg':"图片验证码不正确！"})

        # 判断是否 应该发送短信
        # 1. 是否发短信标志
        is_send = redis_client.get(f'send_flag_{mobile}')

        # 如果标志是存在的， 代表60s还没有过去--不能发短信
        if is_send:
            return JsonResponse({'code': 400, 'errmsg': "短信发送频繁！"})


        # 发短信-阿里云-容联云
        sms_code = random.randint(100000, 999999)
        # sms_code = "%06d" % random.randint(0,1000000)
        settings.LOGGER.info(f"短信验证码--{sms_code}")
        print(f"短信验证码--{sms_code}")

        # 1.创建管道 爬虫框架--web框架--pipeline
        pipeline = redis_client.pipeline()

        # 2.将redis的任务放到 管道里面
        # 存储短信验证码--2号库
        pipeline.setex(f'sms_{mobile}', 300, sms_code)
        # 2. 计时器60s倒计时-redis
        pipeline.setex(f'send_flag_{mobile}', 60, 1)

        # 3.让管道执行任务
        pipeline.execute()


        # 返回
        return JsonResponse({'code':0, 'errmsg':"图片验证码已失效！"})




# 图片验证码
class ImageCodeView(View):
    def get(self, request, uuid):
        # 1. 生成 图片验证码
        text, imgcodebyts = captcha.generate_captcha()

        # 2. 使用 django-redis
        from django_redis import get_redis_connection
        redis_clit = get_redis_connection('verify_code')
        redis_clit.setex(f"img_{uuid}", 300, text)
        redis_clit.close()

        # 3. 返回图片
        #  content_type 内容类型 默认是 text/html
        #  JsonResponse: content_type == application/json
        #  图片  content_type = 'image/jpg'
        #  学名： MIME

        return HttpResponse(content=imgcodebyts, content_type='image/jpeg')

