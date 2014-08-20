# -*- coding: utf-8 -*-

import datetime
from django.contrib import auth
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from models import Order, OrganizationUser, Organization, OrderPriority, OrderStatus, OrderForm, UserForm, UserInfo, \
    Building, BuildingForm, Street, StreetForm, OrganizationForm, StatusForm, OrderPriorityForm

# Create your views here.


def get_user_organizations(user):

    if is_user_controller(user):
        organizations_id = Organization.objects.all()
    else:
        organizations_id = OrganizationUser.objects.filter(user_id=user.id).values_list('organization_id',
                                                                                        flat=True)

    return Organization.objects.filter(id__in=organizations_id)


def is_user_controller(user):
    try:
        is_controller = UserInfo.objects.get(user=user).is_controller
    except UserInfo.DoesNotExist:
        is_controller = False

    if not is_controller:

        is_controller = user.is_superuser

    return is_controller


def is_user_manager(user):
    try:
        is_manager = UserInfo.objects.get(user=user).is_manager
    except UserInfo.DoesNotExist:
        is_manager = False

    if not is_manager:

        is_manager = user.is_superuser

    return is_manager


def login(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect('/orders/view')

    form_auth = AuthenticationForm(None, request.POST or None)

    if form_auth.is_valid():
        auth.login(request, form_auth.get_user())
        return HttpResponseRedirect('/orders/view')

    context = {
        'form_auth': form_auth,
    }

    return render(request, 'login.html', context)


def logout(request):

    auth.logout(request)

    return HttpResponseRedirect('/')


def orders(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    is_controller = is_user_controller(request.user)
    is_manager = is_user_manager(request.user)

    if is_controller:

        order_list = Order.objects.all()

    else:
        organizations_id = OrganizationUser.objects.filter(user_id=request.user.id).values_list("organization_id",
                                                                                                flat=True)
        if is_manager:
            order_list = Order.objects.filter(org_responsible__in=set(organizations_id))
        else:
            order_list = Order.objects.filter(org_creator__in=set(organizations_id))

    context = {
        'order_list': order_list,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
        'is_controller': is_controller,
        'is_manager': is_manager,
    }

    return render(request, 'orders.html', context)


def order_add(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    is_controller = is_user_controller(request.user)
    is_manager = is_user_manager(request.user)

    min_date = datetime.datetime.today().replace(hour=9, minute=0, second=0, microsecond=0)

    # поданные в пятницу переносим на понедельник
    # остальные на следующий день
    if min_date.weekday() == 4:
        min_date += datetime.timedelta(days=3)
    else:
        min_date += datetime.timedelta(days=1)

    if request.method == 'POST':

        order_form = OrderForm(request.POST)

        if order_form.is_valid():

            # проверка даты заявки

            work_date = order_form.cleaned_data['work_date'].replace(second=0)

            if min_date > work_date:

                return HttpResponse('Дата меньше')

            elif min_date < work_date and ((work_date.hour > 14 and work_date.minute >= 0)
                                           or (work_date.hour == 14 and work_date.minute > 0)):

                return HttpResponse('Дата больше')

            order = Order()

            order.org_creator = order_form.cleaned_data['organization']
            order.user_creator = request.user
            order.org_responsible = order_form.cleaned_data['building'].service_organization
            order.building = order_form.cleaned_data['building']
            order.porch = order_form.cleaned_data['porch']
            order.order_reason = order_form.cleaned_data['order_reason']
            order.building_object_type = order_form.cleaned_data['building_object_type']
            order.work_date = work_date
            order.priority = OrderPriority.objects.get(is_default=True)
            order.order_status = OrderStatus.objects.get(is_default=True)

            order.save()

            return HttpResponseRedirect('/orders/view/')
        else:
            return HttpResponse(order_form.errors)

    user_organizations = get_user_organizations(request.user)

    initial_data = {
        'organization': Organization.objects.get(id=user_organizations[0].id),
        'work_date': min_date,
    }

    order_form = OrderForm(initial=initial_data)
    order_form.set_queryset(element='organization', queryset=user_organizations)

    context = {
        'order_form': order_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
        'is_controller': is_controller,
        'is_manager': is_manager,
    }

    return render(request, 'order.html', context)


def order_edit(request, order_id):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    is_superuser = request.user.is_superuser
    is_controller = is_user_controller(request.user)
    is_manager = is_user_manager(request.user)

    if not (request.user.is_superuser or is_controller or is_manager):
        return HttpResponseRedirect('/orders/view/')

    order = Order.objects.get(id=order_id)

    if request.method == 'POST':

        order_form = OrderForm(request.POST)

        if order_form.is_valid():

            order_status = order_form.cleaned_data['order_status']

            if (is_controller or is_manager) and order_status:
                order.order_status = order_form.cleaned_data['order_status']

            if is_controller:
                order.priority = order_form.cleaned_data['priority']
                order.comment = order_form.cleaned_data['comment']

            order.save()

            return HttpResponseRedirect('/orders/view/')

    initial_data = {
        'organization': order.org_creator,
        'order_status': order.order_status,
        'priority': order.priority,
    }

    order_form = OrderForm(instance=order, initial=initial_data)

    order_form.set_queryset(element='organization', queryset=get_user_organizations(order.user_creator))

    if is_superuser:
        statuses_qs = OrderStatus.objects.all()
    elif is_controller:
        statuses_qs = OrderStatus.objects.filter(controller_can_use=True)
    elif is_manager:
        statuses_qs = OrderStatus.objects.filter(manager_can_use=True)
    else:
        statuses_qs = OrderStatus.objects.none()

    order_form.set_queryset(element='order_status', queryset=statuses_qs)

    order_form.organization = order.org_creator

    context = {
        'order_id': order_id,
        'order_form': order_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': is_superuser,
        'is_controller': is_controller,
        'is_manager': is_manager,
    }

    return render(request, 'order_edit.html', context)


def order_cancel(request, order_id):

    order = Order.objects.get(id=order_id)

    if not order.order_status.user_can_cancel:
        return HttpResponse('Невозможно отменить заявку с данным статусом')

    order.is_active = not order.is_active
    order.save()

    return HttpResponseRedirect('/orders/view/')


def users(request):

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    if not request.user.is_superuser:
        return HttpResponseRedirect('/orders/view/')

    users_list = User.objects.all()

    context = {
        'users': users_list,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'users.html', context)


def user_add(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        user_form = UserForm(request.POST)

        if user_form.is_valid():

            try:
                new_user = User.objects.get(username=user_form.cleaned_data['username'])
            except User.DoesNotExist:
                new_user = None

            if new_user:
                return HttpResponse('Пользователь с таким логином уже существует')

            if user_form.cleaned_data['is_superuser']:

                new_user = User.objects.create_superuser(user_form.cleaned_data['username'],
                                                         user_form.cleaned_data['email'],
                                                         user_form.cleaned_data['password'])

            else:

                new_user = User.objects.create_user(user_form.cleaned_data['username'],
                                                    user_form.cleaned_data['email'],
                                                    user_form.cleaned_data['password'])

            user_info = UserInfo(user=new_user, is_controller=user_form.cleaned_data['is_controller'],
                                 is_manager=user_form.cleaned_data['is_manager'],
                                 telephone=user_form.cleaned_data['telephone'])

            user_info.save()

            org_user = OrganizationUser(user=new_user, organization=user_form.cleaned_data['organization'])

            org_user.save()

            return HttpResponseRedirect('/users/view/')

        else:

            return HttpResponse(user_form.errors)

    user_form = UserForm()

    context = {
        'user_form': user_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'user.html', context)


def user_del(request, user_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    User.objects.get(id=user_id).delete()

    return HttpResponseRedirect('/users/view/')


def buildings(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    buildings_list = Building.objects.all()

    context = {
        'buildings': buildings_list,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'buildings.html', context)


def building_del(request, building_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    Building.objects.get(id=building_id).delete()

    return HttpResponseRedirect('/buildings/view/')


def building_add(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        building_form = BuildingForm(request.POST)

        if building_form.is_valid():

            new_building = Building(street=building_form.cleaned_data['street'],
                                    house_num=building_form.cleaned_data['house_num'],
                                    housing=building_form.cleaned_data['housing'],
                                    letter=building_form.cleaned_data['letter'],
                                    service_organization=building_form.cleaned_data['service_organization'])

            new_building.save()

            return HttpResponseRedirect('/buildings/view/')

    building_form = BuildingForm()

    context = {
        'building_form': building_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'building.html', context)


def streets(request):

    street_list = Street.objects.all()

    context = {
        'streets': street_list,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'streets.html', context)


def street_add(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        street_form = StreetForm(request.POST)

        if street_form.is_valid():

            new_street = Street(name=street_form.cleaned_data['name'])

            new_street.save()

            return HttpResponseRedirect('/streets/view/')

    street_form = StreetForm()

    context = {
        'street_form': street_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'street.html', context)


def street_del(request, street_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    Street.objects.get(id=street_id).delete()

    return HttpResponseRedirect('/streets/view/')


def organizations(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    organizations_list = Organization.objects.all()

    context = {
        'organizations': organizations_list,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'organizations.html', context)


def organization_add(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        organization_form = OrganizationForm(request.POST)

        if organization_form.is_valid():

            Organization(name=organization_form.cleaned_data['name']).save()

            return HttpResponseRedirect('/organizations/view/')

    organization_form = OrganizationForm()

    context = {
        'organization_form': organization_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'organization.html', context)


def organization_del(request, organization_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    Organization.objects.get(id=organization_id).delete()

    return HttpResponseRedirect('/organizations/view/')


def statuses(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    status_list = OrderStatus.objects.all()

    context = {
        'statuses': status_list,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'statuses.html', context)


def status_add(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        status_form = StatusForm(request.POST)

        if status_form.is_valid():

            order_status = OrderStatus(name=status_form.cleaned_data['name'],
                                       user_can_cancel=status_form.cleaned_data['user_can_cancel'],
                                       manager_can_use=status_form.cleaned_data['manager_can_use'],
                                       controller_can_use=status_form.cleaned_data['controller_can_use'],
                                       is_default=status_form.cleaned_data['is_default'],)

            order_status.save()

            return HttpResponseRedirect('/statuses/view')

    status_form = StatusForm()

    context = {
        'status_form': status_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'status_add.html', context)


def status_edit(request, status_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    order_status = OrderStatus.objects.get(id=status_id)

    if request.method == 'POST':

        status_form = StatusForm(request.POST)

        if status_form.is_valid():

            order_status.name = status_form.cleaned_data['name']
            order_status.user_can_cancel = status_form.cleaned_data['user_can_cancel']
            order_status.is_default = status_form.cleaned_data['is_default']
            order_status.manager_can_use = status_form.cleaned_data['manager_can_use']
            order_status.controller_can_use = status_form.cleaned_data['controller_can_use']

            order_status.save()

            return HttpResponseRedirect('/statuses/view')

    status_form = StatusForm(instance=order_status)

    context = {
        'status_id': status_id,
        'status_form': status_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'status_edit.html', context)


def status_del(request, status_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    OrderStatus.objects.get(id=status_id).delete()

    return HttpResponseRedirect('/statuses/view')


def priorities(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    priority_list = OrderPriority.objects.all()

    context = {
        'priorities': priority_list,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'order_priorities.html', context)


def priority_add(request):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        priority_form = OrderPriorityForm(request.POST)

        if priority_form.is_valid():

            new_order_priority = OrderPriority(name=priority_form.cleaned_data['name'],
                                               is_default=priority_form.cleaned_data['is_default'],)

            new_order_priority.save()

            return HttpResponseRedirect('/priorities/view/')

    priority_form = OrderPriorityForm()

    context = {
        'priority_form': priority_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'order_priority.html', context)


def priority_del(request, priority_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    OrderPriority.objects.get(id=priority_id).delete()

    return HttpResponseRedirect('/priorities/view')


def priority_edit(request, priority_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    order_priority = OrderPriority.objects.get(id=priority_id)

    if request.method == 'POST':

        priority_form = OrderPriorityForm(request.POST)

        if priority_form.is_valid():

            order_priority.name = priority_form.cleaned_data['name']
            order_priority.is_default = priority_form.cleaned_data['is_default']

            order_priority.save()

            return HttpResponseRedirect('/priorities/view/')

    priority_form = OrderPriorityForm(instance=order_priority)

    context = {
        'priority_id': priority_id,
        'priority_form': priority_form,
        'is_authenticated': request.user.is_authenticated(),
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'order_priority_edit.html', context)