# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.


from django.contrib import messages
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from urllib2 import HTTPError

from postorius import utils
from postorius.models import (Domain, List, MailmanUser,
                              MailmanApiError)
from postorius.forms import *
from postorius.auth.decorators import *
from postorius.views.generic import MailingListView


class ListMembersView(MailingListView):
    """Display all members of a given list.
    """

    @method_decorator(list_owner_required)
    def post(self, request, fqdn_listname):
        if 'owner_email' in request.POST:
            owner_form = NewOwnerForm(request.POST)
            if owner_form.is_valid():
                try:
                    self.mailing_list.add_owner(
                        owner_form.cleaned_data['owner_email'])
                    messages.success(
                        request, _('%s has been added as list owner.'
                                   % request.POST['owner_email']))
                except HTTPError as e:
                    messages.error(request, _(e.msg))
        else:
            owner_form = NewOwnerForm()
        if 'moderator_email' in request.POST:
            moderator_form = NewModeratorForm(request.POST)
            if moderator_form.is_valid():
                try:
                    self.mailing_list.add_moderator(
                        moderator_form.cleaned_data['moderator_email'])
                    messages.success(
                        request, _('%s has been added as list moderator.'
                                   % request.POST['moderator_email']))
                except HTTPError as e:
                    messages.error(request, _(e.msg))
        else:
            moderator_form = NewModeratorForm()
        return render_to_response('postorius/lists/members.html',
                                  {'list': self.mailing_list,
                                   'owner_form': owner_form,
                                   'moderator_form': moderator_form},
                                  context_instance=RequestContext(request))

    @method_decorator(list_owner_required)
    def get(self, request, fqdn_listname):
        owner_form = NewOwnerForm()
        moderator_form = NewModeratorForm()
        return render_to_response('postorius/lists/members.html',
                                  {'list': self.mailing_list,
                                   'owner_form': owner_form,
                                   'moderator_form': moderator_form},
                                  context_instance=RequestContext(request))


class ListMetricsView(MailingListView):
    """Shows common list metrics.
    """

    @method_decorator(list_owner_required)
    def get(self, request, fqdn_listname):
        return render_to_response('postorius/lists/metrics.html',
                                  {'list': self.mailing_list},
                                  context_instance=RequestContext(request))


class ListSummaryView(MailingListView):
    """Shows common list metrics.
    """

    def get(self, request, fqdn_listname):
        user_email = getattr(request.user, 'email', None)
        return render_to_response(
            'postorius/lists/summary.html',
            {'list': self.mailing_list,
             'subscribe_form': ListSubscribe(initial={'email': user_email})},
            context_instance=RequestContext(request))


class ListSubsribeView(MailingListView):
    """Subscribe a mailing list."""

    @method_decorator(login_required)
    def post(self, request, fqdn_listname):
        try:
            form = ListSubscribe(request.POST)
            if form.is_valid():
                email = request.POST.get('email')
                self.mailing_list.subscribe(email)
                messages.success(
                    request, 'You are subscribed to %s.' %
                    self.mailing_list.fqdn_listname)
            else:
                messages.error(request, 'Something went wrong. '
                               'Please try again.')
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError, e:
            messages.error(request, e.msg)
        return redirect('list_summary', self.mailing_list.fqdn_listname)


class ListUnsubscribeView(MailingListView):
    """Unsubscribe from a mailing list."""

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        email = kwargs['email']
        try:
            self.mailing_list.unsubscribe(email)
            messages.success(request,
                             '%s has been unsubscribed from this list.' %
                             email)
        except MailmanApiError:
            return utils.render_api_error(request)
        except ValueError, e:
            messages.error(request, e)
        return redirect('list_summary', self.mailing_list.fqdn_listname)


class ListMassSubsribeView(MailingListView):
    """Mass subscription."""

    @method_decorator(list_owner_required)
    def get(self, request, *args, **kwargs):
        form = ListMassSubscription()
        return render_to_response('postorius/lists/mass_subscribe.html',
                                  {'form': form, 'list': self.mailing_list},
                                  context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = ListMassSubscription(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please fill out the form correctly.')
        else:
            emails = request.POST["emails"].splitlines()
            for email in emails:
                parts = email.split('@')
                if len(parts) != 2 or '.' not in parts[1]:
                    messages.error(request,
                                   'The email address %s is not valid.' %
                                   email)
                else:
                    try:
                        self.mailing_list.subscribe(address=email)
                        messages.success(
                            request,
                            'The address %s has been subscribed to %s.' %
                            (email, self.mailing_list.fqdn_listname))
                    except MailmanApiError:
                        return utils.render_api_error(request)
                    except HTTPError, e:
                        messages.error(request, e)
        return redirect('mass_subscribe', self.mailing_list.fqdn_listname)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_new(request, template='postorius/lists/new.html'):
    """
    Add a new mailing list.
    If the request to the function is a GET request an empty form for
    creating a new list will be displayed. If the request method is
    POST the form will be evaluated. If the form is considered
    correct the list gets created and otherwise the form with the data
    filled in before the last POST request is returned. The user must
    be logged in to create a new list.
    """
    mailing_list = None
    if request.method == 'POST':
        try:
            domains = Domain.objects.all()
        except MailmanApiError:
            return utils.render_api_error(request)
        choosable_domains = [("", _("Choose a Domain"))]
        for domain in domains:
            choosable_domains.append((domain.mail_host,
                                      domain.mail_host))
        form = ListNew(choosable_domains, request.POST)
        if form.is_valid():
            #grab domain
            domain = Domain.objects.get_or_404(
                mail_host=form.cleaned_data['mail_host'])
            #creating the list
            try:
                mailing_list = domain.create_list(
                    form.cleaned_data['listname'])
                list_settings = mailing_list.settings
                list_settings["description"] = form.cleaned_data['description']
                list_settings["owner_address"] = \
                    form.cleaned_data['list_owner']
                list_settings["advertised"] = form.cleaned_data['advertised']
                list_settings.save()
                messages.success(request, _("List created"))
                return redirect("list_summary",
                                fqdn_listname=mailing_list.fqdn_listname)
            #TODO catch correct Error class:
            except HTTPError, e:
                messages.error(request, e)
                return render_to_response(
                    'postorius/errors/generic.html',
                    {'error': e}, context_instance=RequestContext(request))
            else:
                messages.success(_("New List created"))
    else:
        try:
            domains = Domain.objects.all()
        except MailmanApiError:
            return utils.render_api_error(request)
        choosable_domains = [("", _("Choose a Domain"))]
        for domain in domains:
            choosable_domains.append((domain.mail_host, domain.mail_host))
        form = ListNew(choosable_domains,
                       initial={'list_owner': request.user.email})
    return render_to_response(template, {'form': form},
                              context_instance=RequestContext(request))


def list_index(request, template='postorius/lists/index.html'):
    """Show a table of all public mailing lists.
    """
    lists = []
    error = None
    only_public = True
    if request.user.is_superuser:
        only_public = False
    try:
        lists = List.objects.all(only_public=only_public)
    except MailmanApiError:
        return utils.render_api_error(request)
    if request.method == 'POST':
        return redirect("list_summary", fqdn_listname=request.POST["list"])
    else:
        return render_to_response(template,
                                  {'error': error,
                                   'lists': lists},
                                  context_instance=RequestContext(request))


@login_required
def list_subscriptions(request, option=None, fqdn_listname=None,
                       user_email=None,
                       template='postorius/lists/subscriptions.html',
                       *args, **kwargs):
    """
    Display the information there is available for a list. This
    function also enables subscribing or unsubscribing a user to a
    list. For the latter two different forms are available for the
    user to fill in which are evaluated in this function.
    """
    # create Values for Template usage
    message = None
    error = None
    form_subscribe = None
    form_unsubscribe = None
    if request.POST.get('fqdn_listname', ''):
        fqdn_listname = request.POST.get('fqdn_listname', '')
    # connect REST and catch issues getting the list
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except AttributeError, e:
        return render_to_response('postorius/errors/generic.html',
                                  {'error': "REST API not found / Offline"},
                                  context_instance=RequestContext(request))
    # process submitted form
    if request.method == 'POST':
        form = False
        # The form enables both subscribe and unsubscribe. As a result
        # we must find out which was the case.
        if request.POST.get('name', '') == "subscribe":
            form = ListSubscribe(request.POST)
            if form.is_valid():
                # the form was valid so try to subscribe the user
                try:
                    email = form.cleaned_data['email']
                    the_list.subscribe(
                        address=email,
                        display_name=form.cleaned_data.get('display_name', ''))
                    return render_to_response(
                        'postorius/lists/summary.html',
                        {'list': the_list, 'option': option,
                         'message': _("Subscribed ") + email},
                        context_instance=RequestContext(request))
                except HTTPError, e:
                    return render_to_response(
                        'postorius/errors/generic.html',
                        {'error': e},
                        context_instance=RequestContext(request))
            else:  # invalid subscribe form
                form_subscribe = form
                form_unsubscribe = ListUnsubscribe(
                    initial={'fqdn_listname': fqdn_listname,
                             'name': 'unsubscribe'})
        elif request.POST.get('name', '') == "unsubscribe":
            form = ListUnsubscribe(request.POST)
            if form.is_valid():
                # the form was valid so try to unsubscribe the user
                try:
                    email = form.cleaned_data["email"]
                    the_list.unsubscribe(address=email)
                    return render_to_response(
                        'postorius/lists/summary.html',
                        {'list': the_list,
                         'message': _("Unsubscribed ") + email},
                        context_instance=RequestContext(request))
                except ValueError, e:
                    return render_to_response(
                        'postorius/errors/generic.html',
                        {'error': e},
                        context_instance=RequestContext(request))
            else:  # invalid unsubscribe form
                form_subscribe = ListSubscribe(
                    initial={'fqdn_listname': fqdn_listname,
                             'option': option,
                             'name': 'subscribe'})
                form_unsubscribe = ListUnsubscribe(request.POST)
    else:
        # the request was a GET request so set the two forms to empty
        # forms
        if option == "subscribe" or not option:
            form_subscribe = ListSubscribe(
                initial={'fqdn_listname': fqdn_listname,
                         'email': request.user.username,
                         'name': 'subscribe'})
        if option == "unsubscribe" or not option:
            form_unsubscribe = ListUnsubscribe(
                initial={'fqdn_listname': fqdn_listname,
                         'email': request.user.username,
                         'name': 'unsubscribe'})
    the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    return render_to_response(template,
                              {'form_subscribe': form_subscribe,
                               'form_unsubscribe': form_unsubscribe,
                               'message': message,
                               'error': error,
                               'list': the_list},
                              context_instance=RequestContext(request))


@list_owner_required
def list_delete(request, fqdn_listname):
    """Deletes a list but asks for confirmation first.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    if request.method == 'POST':
        the_list.delete()
        return redirect("list_index")
    else:
        submit_url = reverse('list_delete',
                             kwargs={'fqdn_listname': fqdn_listname})
        cancel_url = reverse('list_index',)
        return render_to_response(
            'postorius/lists/confirm_delete.html',
            {'submit_url': submit_url, 'cancel_url': cancel_url,
             'list': the_list},
            context_instance=RequestContext(request))


@list_owner_required
def list_held_messages(request, fqdn_listname):
    """Shows a list of held messages.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response('postorius/lists/held_messages.html',
                              {'list': the_list},
                              context_instance=RequestContext(request))


@list_owner_required
def accept_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.accept_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.success(request, 'The message has been accepted.')
    return redirect('list_held_messages', the_list.fqdn_listname)


@list_owner_required
def discard_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.discard_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.success(request, 'The message has been discarded.')
    return redirect('list_held_messages', the_list.fqdn_listname)


@list_owner_required
def defer_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.defer_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.success(request, 'The message has been defered.')
    return redirect('list_held_messages', the_list.fqdn_listname)


@list_owner_required
def reject_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.reject_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.success(request, 'The message has been rejected.')
    return redirect('list_held_messages', the_list.fqdn_listname)


@list_owner_required
def list_settings(request, fqdn_listname=None, visible_section=None,
                  visible_option=None,
                  template='postorius/lists/settings.html'):
    """
    View and edit the settings of a list.
    The function requires the user to be logged in and have the
    permissions necessary to perform the action.

    Use /<NAMEOFTHESECTION>/<NAMEOFTHEOPTION>
    to show only parts of the settings
    <param> is optional / is used to differ in between section and option might
    result in using //option
    """
    message = ""
    if visible_section is None:
        visible_section = 'List Identity'
    form_sections = []
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    #collect all Form sections for the links:
    temp = ListSettings('', '')
    for section in temp.layout:
        try:
            form_sections.append((section[0],
                                  temp.section_descriptions[section[0]]))
        except KeyError:
            pass
    del temp
    # Save a Form Processed by POST
    if request.method == 'POST':
        form = ListSettings(visible_section, visible_option, data=request.POST)
        form.truncate()
        if form.is_valid():
            list_settings = the_list.settings
            for key in form.fields.keys():
                list_settings[key] = form.cleaned_data[key]
                list_settings.save()
            message = _("The list has been updated.")
        else:
            message = _("Validation Error - The list has not been updated.")
    else:
        #Provide a form with existing values
        #create form and process layout into form.layout
        form = ListSettings(visible_section, visible_option, data=None)
        #create a Dict of all settings which are used in the form
        used_settings = {}
        for section in form.layout:
            for option in section[1:]:
                used_settings[option] = the_list.settings[option]
                if option == u'acceptable_aliases':
                    used_settings[option] = '\n'.join(used_settings[option])
        # recreate the form using the settings
        form = ListSettings(visible_section, visible_option,
                            data=used_settings)
        form.truncate()
    return render_to_response(template,
                              {'form': form,
                               'form_sections': form_sections,
                               'message': message,
                               'list': the_list,
                               'visible_option': visible_option,
                               'visible_section': visible_section},
                              context_instance=RequestContext(request))


@login_required
def user_mailmansettings(request):
    try:
        the_user = MailmanUser.objects.get(address=request.user.email)
    except MailmanApiError:
        return utils.render_api_error(request)

    settingsform = MembershipSettings()
    return render_to_response('postorius/user_mailmansettings.html',
                              {'mm_user': the_user,
                               'settingsform': settingsform},
                              context_instance=RequestContext(request))


@login_required
def membership_settings(request):
    """Display a list of all memberships.
    """
