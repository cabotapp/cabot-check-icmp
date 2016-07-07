from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django import forms
from django.template import Context, Template
from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save

from cabot.plugins.models import StatusCheckPlugin, StatusCheckPluginModel
from cabot.cabotapp.models import Instance, StatusCheck, Service

from os import environ as env
import subprocess
import requests
import logging
logger = logging.getLogger(__name__)


class ICMPStatusCheckPlugin(StatusCheckPlugin):
    name = "ICMP"
    slug = "cabot_check_icmp"
    author = "Jonathan Balls"
    version = "0.0.1"
    font_icon = "glyphicon glyphicon-transfer"

    def target(self, check):
        instances = check.instance_set.all()
        services = check.service_set.all()
        if instances:
            return instances[0]
        elif services:
            return services[0]
        else:
            return None
    
    def run(self, check, result):
        instances = check.instance_set.all()
        services = check.service_set.all()
        
        if instances:
            target = instances[0].address
        else:
            target = services[0].url

        # We need to read both STDOUT and STDERR because ping can write to both, depending on the kind of error. Thanks a lot, ping.
        ping_process = subprocess.Popen("ping -c 1 " + target, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        response = ping_process.wait()

        if response == 0:
            result.succeeded = True
        else:
            output = ping_process.stdout.read()
            result.succeeded = False
            result.error = output

        return result

    def description(self, check):
        target = self.target(check)
        if target:
            return 'ICMP Reply from {}'.format(target.name)
        else:
            return 'ICMP Check with no target.'

