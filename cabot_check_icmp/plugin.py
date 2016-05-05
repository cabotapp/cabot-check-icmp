from os import environ as env

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import Context, Template

from cabot.plugins.models import CheckPlugin

import requests
import logging

class ICMPCheckPlugin(CheckPlugin):
    name = "ICMP"
    slug = "icmp"
    author = "Jonatham Balls"
    version = "0.0.1"
    
    def _run(self):
        result = StatusCheckResult(status_check=self)
        instances = self.instance_set.all()
        target = self.instance_set.get().address

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

class ICMPStatusCheckForm(StatusCheckForm):

    class Meta:
        model = ICMPStatusCheck
        fields = (
            'name',
            'frequency',
            'importance',
            'active',
            'debounce',
        )
        widgets = dict(**base_widgets)

