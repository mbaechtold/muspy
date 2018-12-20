# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 Alexander Kojevnikov <alexander@kojevnikov.com>
#
# muspy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# muspy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with muspy.  If not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from app.models import *


class ResetForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "Your email address"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if not UserProfile.get_by_email(email):
            raise forms.ValidationError("Unknown email address. " "Please enter another.")
        return email


class SettingsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "Your email address"}),
        help_text="We will send you notifications about new releases to this address",
    )
    new_password = forms.CharField(
        label="Password",
        max_length=100,
        required=False,
        widget=forms.PasswordInput(render_value=True, attrs={"class": "input"}),
    )
    notify = forms.BooleanField(label="Receive new release notifications by email.", required=False)
    notify_safari = forms.BooleanField(
        label="Receive new release notifications in Safari.", required=False
    )
    notify_album = forms.BooleanField(label="Album", required=False)
    notify_single = forms.BooleanField(label="Single", required=False)
    notify_ep = forms.BooleanField(label="EP", required=False)
    notify_live = forms.BooleanField(label="Live", required=False)
    notify_compilation = forms.BooleanField(label="Compilation", required=False)
    notify_remix = forms.BooleanField(label="Remix", required=False)
    notify_other = forms.BooleanField(label="Other", required=False)

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if self.profile.user.email != email and User.objects.filter(email=email):
            raise forms.ValidationError("This email is already in use. " "Please enter another.")
        return email

    def save(self):
        if self.profile.user.email != self.cleaned_data["email"]:
            self.profile.user.email = self.cleaned_data["email"]
            self.profile.email_activated = False
            with transaction.atomic():
                self.profile.user.save()
                self.profile.save()
            self.profile.send_activation_email(self.request)
        changed = False
        if self.cleaned_data["new_password"]:
            self.profile.user.set_password(self.cleaned_data["new_password"])
            self.profile.user.save()
        if self.profile.notify != self.cleaned_data["notify"]:
            self.profile.notify = self.cleaned_data["notify"]
            changed = True
        if self.profile.notify_safari != self.cleaned_data["notify_safari"]:
            self.profile.notify_safari = self.cleaned_data["notify_safari"]
            changed = True
        if self.profile.notify_album != self.cleaned_data["notify_album"]:
            self.profile.notify_album = self.cleaned_data["notify_album"]
            changed = True
        if self.profile.notify_single != self.cleaned_data["notify_single"]:
            self.profile.notify_single = self.cleaned_data["notify_single"]
            changed = True
        if self.profile.notify_ep != self.cleaned_data["notify_ep"]:
            self.profile.notify_ep = self.cleaned_data["notify_ep"]
            changed = True
        if self.profile.notify_live != self.cleaned_data["notify_live"]:
            self.profile.notify_live = self.cleaned_data["notify_live"]
            changed = True
        if self.profile.notify_compilation != self.cleaned_data["notify_compilation"]:
            self.profile.notify_compilation = self.cleaned_data["notify_compilation"]
            changed = True
        if self.profile.notify_remix != self.cleaned_data["notify_remix"]:
            self.profile.notify_remix = self.cleaned_data["notify_remix"]
            changed = True
        if self.profile.notify_other != self.cleaned_data["notify_other"]:
            self.profile.notify_other = self.cleaned_data["notify_other"]
            changed = True
        if changed:
            self.profile.save()


class SignInForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget = forms.EmailInput(
            attrs={"class": "input", "placeholder": "Your email address"}
        )
        self.fields["password"].widget.attrs = {"class": "input", "placeholder": "Your password"}


class SignUpForm(forms.Form):

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "Your email address"}),
        label="Email",
        max_length=75,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            render_value=False, attrs={"class": "input", "placeholder": "Your password"}
        ),
        label="Password",
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email):
            raise forms.ValidationError(
                "This email address is already in use. Please supply a different email address."
            )
        return email

    def save(self, request):
        return UserProfile.create_user(
            email=self.cleaned_data["email"], password=self.cleaned_data["password"]
        )
