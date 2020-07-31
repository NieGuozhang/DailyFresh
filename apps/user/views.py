# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.mail import send_mail

from django.urls import reverse

from celery_tasks.tasks import send_register_active_email
from .models import User


class RegisterView(View):
    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """进行注册处理"""
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        password2 = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        # 判断两次密码是否一致
        if password != password2:
            return render(request, 'register.html', {'errmsg': '两次输入的密码不一致'})
        # 判断是否遵守协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        userList = User.objects.filter(username=username)
        if userList:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 业务处理：用户注册
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = 0
        user.save()

        # 发送激活邮件：，包含激活链接：http://127.0.0.1:8000/user/active/id
        # 激活链接中需要包含用户信息
        # 加密用户的身份信息，生成激活Token

        s = Serializer(settings.SECRET_KEY, 3600)
        token = s.dumps({'confirm': user.id})  # bytes
        token = token.decode()

        # 发邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答,跳转至首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):
        s = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 获取ID
            user_id = s.loads(token)['confirm']
            # 根据ID获取用户
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转至登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')


class LoginView(View):
    """登录"""

    def get(self, request):
        # 显示登录页面
        # 判断是否记住了用户名
        username = request.COOKIES.get('username', '')
        if username:
            checked = 'checked'
        else:
            checked = ''
        context = {
            'username': username,
            'checked': checked,
        }
        return render(request, 'login.html', context=context)

    def post(self, request):
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user:
            # 用户名密码正确
            if user.is_active:
                # 已激活
                # 记录用户的登录状态
                login(request, user)

                # 跳转至首页
                response = redirect(reverse('goods:index'))
                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 保存Cookie
                    response.set_cookie('username', username, 7 * 24 * 3600)
                else:
                    # 删除Cookie
                    response.delete_cookie('username')
                return response
            else:
                # 未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
        # 返回应答
