from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django import forms
from django.template import Context, Template
from django.dispatch import receiver
from django.db.models.signals import post_save

from cabot.plugins.models import StatusCheckPlugin, StatusCheckPluginModel
from cabot.plugins.forms import CheckConfigForm
from cabot.cabotapp.models import Instance, StatusCheck

from os import environ as env
import subprocess
import requests
import logging


class ICMPStatusCheckForm(CheckConfigForm):
    name = forms.CharField(max_length=80)


class ICMPStatusCheckPlugin(StatusCheckPlugin):
    name = "ICMP"
    slug = "icmp"
    author = "Jonathan Balls"
    version = "0.0.1"
    font_icon = "glyphicon glyphicon-transfer"

    config_form = ICMPStatusCheckForm

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

# Autocreate a ping check for an instance when it is created.
@receiver(post_save, sender=Instance)
def icmp_check_auto_create(sender, instance, created, **kwargs):
    if created:
        s = StatusCheck.objects.create(
                check_plugin = StatusCheckPluginModel.objects.get(slug='icmp'),
                name = 'Default Ping Check for {}'.format(instance.name)
                )
        instance.status_checks.add(s)

