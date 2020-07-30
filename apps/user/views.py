# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from django.shortcuts import render, redirect

from django.urls import reverse

from .models import User


def register(request):
    """显示注册页面"""
    return render(request, 'register.html')


def register_handle(request):
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

    # 返回应答,跳转至首页
    return redirect(reverse('goods:index'))
