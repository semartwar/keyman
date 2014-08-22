# -*- coding: utf-8 -*-

import datetime
from django.contrib import auth
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from models import Order, Organization, OrderPriority, OrderStatus, OrderForm, UserForm, \
    UserProfile, Building, BuildingForm, Street, StreetForm, OrganizationForm, StatusForm, OrderPriorityForm

# Create your views here.


def login(request):

    request_user = request.user

    if request_user.is_authenticated():

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

    request_user = request.user
    user_profile = request_user.userprofile

    # только аутентифицированные юзвери
    if not request_user.is_authenticated():
        return HttpResponseRedirect('/')

    # для контролирующих органов/админов доступны все
    # заявки
    if user_profile.is_controller or user_profile.is_superuser:

        order_list = Order.objects.all()

    elif user_profile.is_manager:

        # для манагеров (уп. компаний) только те, которые обслуживает
        # их организация
        order_list = Order.objects.filter(org_responsible=request_user.organization)

    else:

        # для простых смертных только их заявки
        order_list = Order.objects.filter(org_creator=request_user.organization)

    context = {
        'order_list': order_list,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'orders.html', context)


def order_add(request):

    request_user = request.user
    user_profile = request_user.userprofile

    # только аутентифицированные юзвери
    if not (request_user.is_authenticated() and (request_user.is_superuser or user_profile.is_controller)) :
        return HttpResponseRedirect('/')

    # этот день 09:00:00
    min_date = datetime.datetime.today().replace(hour=9, minute=0, second=0, microsecond=0)

    # поданные в пятницу переносим на понедельник
    # остальные на следующий день ибо нехуй
    if min_date.weekday() == 4:
        min_date += datetime.timedelta(days=3)
    else:
        min_date += datetime.timedelta(days=1)

    if request.method == 'POST':

        order_form = OrderForm(request.POST)

        if order_form.is_valid():

            # проверка даты заявки. минимальная дата 9 утра следующего дня,
            # максимальная 14 часов

            # на всякий случай обнуляем секунды
            work_date = order_form.cleaned_data['work_date'].replace(second=0)

            if min_date > work_date:

                return HttpResponse('надо выводить в форме заявки ошибку')

            elif min_date < work_date and ((work_date.hour > 14 and work_date.minute >= 0)
                                           or (work_date.hour == 14 and work_date.minute > 0)):

                return HttpResponse('надо выводить в форме заявки ошибку')

            # все хорошо, создаем заявку

            order = Order()

            order.org_creator = order_form.cleaned_data['organization']
            order.user_creator = request_user
            order.org_responsible = order_form.cleaned_data['building'].service_organization
            order.building = order_form.cleaned_data['building']
            order.porch = order_form.cleaned_data['porch']
            order.order_reason = order_form.cleaned_data['order_reason']
            order.building_object_type = order_form.cleaned_data['building_object_type']
            order.work_date = work_date
            order.priority = OrderPriority.objects.get(is_default=True)
            order.order_status = OrderStatus.objects.get(is_default=True)

            order.save()

            # возвращаемся к списку заявок

            return HttpResponseRedirect('/orders/view/')
        else:
            return HttpResponse('надо выводить в форме заявки ошибку')

    initial_data = {
        'organization': user_profile.organization,
        'work_date': min_date,
    }

    # для админов и контролирующих органов доступны все
    # организации
    if request_user.is_superuser or user_profile.is_controller:
        organization_qs = Organization.objects.all()
    else:
        organization_qs = Organization.objects.filter(id=request_user.organization.id)

    order_form = OrderForm(initial=initial_data)
    order_form.set_queryset(element='organization', queryset=organization_qs)

    context = {
        'action': 'add',
        'order_form': order_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'order.html', context)


def order_edit(request, order_id):

    request_user = request.user
    user_profile = request_user.userprofile

    if not request_user.is_authenticated():
        return HttpResponseRedirect('/')

    # редактирование доступно для всех кроме смертных
    if not (request_user.is_superuser or user_profile.is_controller or user_profile.is_manager):
        return HttpResponseRedirect('/orders/view/')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponseRedirect('http://www.google.com/')

    if request.method == 'POST':

        order_form = OrderForm(request.POST)

        if order_form.is_valid():

            order_status = order_form.cleaned_data['order_status']

            # манагеры и контролирующие органы могут менять
            # статус заявок
            if (user_profile.is_controller or user_profile.is_manager) and order_status:
                order.order_status = order_form.cleaned_data['order_status']

            # контролирующие органы могут дополнительно менять
            # приоритет заявки и комментарий к ней
            if user_profile.is_controller:
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

    if request_user.is_superuser or user_profile.is_controller:
        organization_qs = Organization.objects.all()
    else:
        organization_qs = Organization.objects.filter(id=order.org_creator.id)

    order_form.set_queryset(element='organization', queryset=organization_qs)

    if user_profile.is_superuser:
        statuses_qs = OrderStatus.objects.all()
    elif user_profile.is_controller:
        statuses_qs = OrderStatus.objects.filter(controller_can_use=True)
    elif user_profile.is_manager:
        statuses_qs = OrderStatus.objects.filter(manager_can_use=True)
    else:
        statuses_qs = OrderStatus.objects.none()

    order_form.set_queryset(element='order_status', queryset=statuses_qs)

    order_form.organization = order.org_creator

    context = {
        'action': 'edit',
        'order_id': order_id,
        'order_form': order_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'order_edit.html', context)


def order_cancel(request, order_id):

    request_user = request.user

    # только аутентифицированные юзвери
    if not request_user.is_authenticated():
        return HttpResponseRedirect('/')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponseRedirect('http://www.google.com')

    if not order.order_status.user_can_cancel:
        return HttpResponse('Невозможно отменить заявку с данным статусом')

    order.is_active = not order.is_active
    order.save()

    return HttpResponseRedirect('/orders/view/')


def users(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not request_user.is_authenticated():
        return HttpResponseRedirect('/')

    if not request_user.is_superuser:
        return HttpResponseRedirect('/orders/view/')

    users_list = User.objects.all()

    context = {
        'users': users_list,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'users.html', context)


def user_add(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
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

            new_user.first_name = user_form.cleaned_data['first_name']
            new_user.last_name = user_form.cleaned_data['last_name']

            new_user.save()

            # запишем данные профиля
            user_profile = UserProfile(user=new_user,
                                       organization=user_form.cleaned_data['organization'],
                                       is_controller=user_form.cleaned_data['is_controller'],
                                       is_manager=user_form.cleaned_data['is_manager'],
                                       telephone=user_form.cleaned_data['telephone'])

            user_profile.save()

            return HttpResponseRedirect('/users/view/')

        else:

            return HttpResponse('Вывести ошибки на форму')

    user_form = UserForm()

    context = {
        'action': 'add',
        'user_form': user_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'user.html', context)


def user_del(request, user_id):

    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect('/')

    try:
        User.objects.get(id=user_id).delete()
    except User.DoesNotExist:
        return HttpResponseRedirect('http://www.google.com')

    return HttpResponseRedirect('/users/view/')


def buildings(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    buildings_list = Building.objects.all()

    context = {
        'buildings': buildings_list,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'buildings.html', context)


def building_del(request, building_id):

    request_user = request.user

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    Building.objects.get(id=building_id).delete()

    return HttpResponseRedirect('/buildings/view/')


def building_add(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
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
        'action': 'add',
        'building_form': building_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'building.html', context)


def streets(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    street_list = Street.objects.all()

    context = {
        'streets': street_list,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'streets.html', context)


def street_add(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        street_form = StreetForm(request.POST)

        if street_form.is_valid():

            new_street = Street(name=street_form.cleaned_data['name'])

            new_street.save()

            return HttpResponseRedirect('/streets/view/')

    street_form = StreetForm()

    context = {
        'action': 'add',
        'street_form': street_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'street.html', context)


def street_del(request, street_id):

    request_user = request.user

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    try:
        Street.objects.get(id=street_id).delete()
    except Street.DoesNotExist:
        return HttpResponseRedirect('http://www.google.com/')

    return HttpResponseRedirect('/streets/view/')


def organizations(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    organizations_list = Organization.objects.all()

    context = {
        'organizations': organizations_list,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'organizations.html', context)


def organization_add(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        organization_form = OrganizationForm(request.POST)

        if organization_form.is_valid():

            Organization(name=organization_form.cleaned_data['name']).save()

            return HttpResponseRedirect('/organizations/view/')

    organization_form = OrganizationForm()

    context = {
        'action': 'add',
        'organization_form': organization_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'organization.html', context)


def organization_del(request, organization_id):

    request_user = request.user

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    try:
        Organization.objects.get(id=organization_id).delete()
    except Organization.DoesNoExist:
        return HttpResponseRedirect('http://www.google.com/')

    return HttpResponseRedirect('/organizations/view/')


def statuses(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    status_list = OrderStatus.objects.all()

    context = {
        'statuses': status_list,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'statuses.html', context)


def status_add(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
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
        'action': reverse('statuses:add'),
        'title': 'Создание статуса',
        'status_form': status_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'status.html', context)


def status_edit(request, status_id):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    try:
        order_status = OrderStatus.objects.get(id=status_id)
    except OrderStatus.DoesNotExist:
        return HttpResponseRedirect('http://www.google.com/')

    if request.method == 'POST':

        status_form = StatusForm(request.POST)

        if status_form.is_valid():

            order_status.name = status_form.cleaned_data['name']
            order_status.user_can_cancel = status_form.cleaned_data['user_can_cancel']
            order_status.is_default = status_form.cleaned_data['is_default']
            order_status.manager_can_use = status_form.cleaned_data['manager_can_use']
            order_status.controller_can_use = status_form.cleaned_data['controller_can_use']

            print(status_form.cleaned_data['user_can_cancel'])

            order_status.save()

            return HttpResponseRedirect('/statuses/view')

    status_form = StatusForm(instance=order_status)

    context = {
        'action': reverse('statuses:edit', kwargs={'status_id': status_id}),
        'title': 'Редактирование статуса',
        'status_form': status_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'status.html', context)


def status_del(request, status_id):

    request_user = request.user

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    OrderStatus.objects.get(id=status_id).delete()

    return HttpResponseRedirect('/statuses/view')


def priorities(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    priority_list = OrderPriority.objects.all()

    context = {
        'priorities': priority_list,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'order_priorities.html', context)


def priority_add(request):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
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
        'action': 'add',
        'priority_form': priority_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'order_priority.html', context)


def priority_del(request, priority_id):

    request_user = request.user

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    try:
        OrderPriority.objects.get(id=priority_id).delete()
    except OrderPriority.DoesNotExist:
        return HttpResponseRedirect('http://www.google.com/')

    return HttpResponseRedirect('/priorities/view')


def priority_edit(request, priority_id):

    request_user = request.user
    user_profile = request_user.userprofile

    if not (request_user.is_authenticated() and request_user.is_superuser):
        return HttpResponseRedirect('/')

    try:
        order_priority = OrderPriority.objects.get(id=priority_id)
    except OrderPriority.DoesNotExist:
        return HttpResponseRedirect('http://www.google.com/')

    if request.method == 'POST':

        priority_form = OrderPriorityForm(request.POST)

        if priority_form.is_valid():

            order_priority.name = priority_form.cleaned_data['name']
            order_priority.is_default = priority_form.cleaned_data['is_default']

            order_priority.save()

            return HttpResponseRedirect('/priorities/view/')

    priority_form = OrderPriorityForm(instance=order_priority)

    context = {
        'action': 'edit',
        'priority_id': priority_id,
        'priority_form': priority_form,
        'request_user': request_user,
        'user_profile': user_profile,
    }

    return render(request, 'order_priority_edit.html', context)