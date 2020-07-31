# -*- encoding:utf-8 -*-
import sys  # reload()之前必须要引入模块
import time

reload(sys)
sys.setdefaultencoding('utf-8')

# 使用celery
from celery import Celery

# 创建一个celery实例对象
from django.conf import settings
from django.core.mail import send_mail

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DailyFresh.settings")
django.setup()

app = Celery('celery_tasks.task', broker='redis://127.0.0.1:6379/8')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""

    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    reciver = [to_email]
    htmlmessage = '<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面的链接激活您的账号：<br/>' \
                  '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
                      username, token, token)

    send_mail(subject, message=message, from_email=settings.EMAIL_FROM, recipient_list=reciver,
              html_message=htmlmessage)


"""
celery发送邮件总结：
任务发出者：Django项目代码
任务队列：redis
任务处理者：celery作为处理者

环境安装
pip install celery

三者可不在同一电脑。处理者也需要任务的代码

启动任务处理者：
celery -A celery_tasks.tasks worker -l info
"""
