# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django import forms

# Create your models here.
from django.forms.widgets import Textarea


class Street(models.Model):
    name = models.CharField(max_length=256)

    def __unicode__(self):
        return self.name


class BuildingObjectType(models.Model):
    name = models.CharField(max_length=256)

    def __unicode__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField(max_length=256)

    def __unicode__(self):
        return self.name


class OrderPriority(models.Model):
    name = models.CharField(max_length=256)
    is_default = models.BooleanField()

    def __unicode__(self):
        return self.name


class Building(models.Model):
    service_organization = models.ForeignKey(Organization)
    street = models.ForeignKey(Street)
    house_num = models.DecimalField(max_digits=3, decimal_places=0)
    housing = models.DecimalField(max_digits=3, decimal_places=0, blank=True, null=True)
    letter = models.CharField(max_length=256, blank=True, null=True)

    def __unicode__(self):

        result = self.street.name + u' д. ' + str(self.house_num)

        if self.housing:
            result += u' корп. ' + str(self.housing)

        if self.letter:
            result += u' литер ' + self.letter

        return result


class Performer(models.Model):
    name = models.CharField(max_length=256)

    def __unicode__(self):
        return self.name


class OrderStatus(models.Model):

    name = models.CharField(max_length=256)
    user_can_cancel = models.BooleanField()
    manager_can_use = models.BooleanField()
    controller_can_use = models.BooleanField()
    is_default = models.BooleanField()

    def __unicode__(self):
        return self.name


class Order(models.Model):
    org_creator = models.ForeignKey(Organization, related_name='org_creator')
    user_creator = models.ForeignKey(User)
    org_responsible = models.ForeignKey(Organization, related_name='org_responsible')
    performer = models.ForeignKey(Performer, blank=True, null=True)
    order_status = models.ForeignKey(OrderStatus)
    order_reason = models.CharField(max_length=1024)
    building = models.ForeignKey(Building)
    porch = models.DecimalField(max_digits=3, decimal_places=0)
    building_object_type = models.ForeignKey(BuildingObjectType)
    work_date = models.DateTimeField()
    priority = models.ForeignKey(OrderPriority)
    comment = models.CharField(max_length=1024, blank=True, default='')
    is_active = models.BooleanField(default=True)


class UserProfile(models.Model):

    user = models.OneToOneField(User, primary_key=True)
    organization = models.ForeignKey(Organization)
    is_controller = models.BooleanField()
    is_manager = models.BooleanField()
    telephone = models.CharField(max_length=10)

    def __unicode__(self):
        return self.user.username


class OrderForm(forms.ModelForm):

    organization = forms.ModelChoiceField(Organization.objects.all(), label='Организация')
    priority = forms.ModelChoiceField(OrderPriority.objects.all(), label='Приоритет', required=False)
    order_status = forms.ModelChoiceField(OrderStatus.objects.all(), label='Статус', required=False)

    def set_queryset(self, element, queryset):
        self.fields[element].queryset = queryset

    class Meta:

        model = Order
        fields = ['building', 'porch', 'building_object_type', 'work_date', 'order_reason', 'comment']

        labels = {
            'porch': 'Подъезд',
            'building_object_type': 'Помещение',
            'work_date': 'Дата проведения работ',
            'order_reason': 'Причина',
            'building': 'Дом',
            'priority': 'Приоритет',
            'order_status': 'Статус',
            'comment': 'Комментарий',
            }

        localized_fields = (
            'work_date',
        )

        widgets = {
            'order_reason': Textarea(attrs={'cols': 30, 'rows': 10}),
            'comment': Textarea(attrs={'cols': 30, 'rows': 10}),
            }


class UserForm(forms.Form):

    organization = forms.ModelChoiceField(queryset=Organization.objects.all(), label='Организация')
    username = forms.CharField(label='Имя пользователя', max_length=256)
    password = forms.CharField(label='Пароль', max_length=256)
    first_name = forms.CharField(label='Имя', max_length=30)
    last_name = forms.CharField(label='Фамилия', max_length=30)
    telephone = forms.CharField(max_length=10, label='Телефон')
    email = forms.EmailField(label='Эл. почта', required=False)
    is_superuser = forms.BooleanField(label='Администратор', required=False)
    is_controller = forms.BooleanField(label='Контролирующий орган', required=False)
    is_manager = forms.BooleanField(label='Управляющая компания', required=False)


class BuildingForm(forms.ModelForm):

    class Meta:

        model = Building

        fields = ['street', 'house_num', 'housing', 'letter', 'service_organization']

        labels = {
            'street': 'Улица',
            'house_num': 'Номер дома',
            'housing': 'Корпус',
            'letter': 'Литер',
            'service_organization': 'Обслуживающая организация',
        }


class StreetForm(forms.ModelForm):

    class Meta:

        model = Street

        fields = ['name']

        labels = {
            'name': 'Улица'
        }


class OrganizationForm(forms.ModelForm):

    class Meta:
        model = Organization

        fields = ['name']

        labels = {
            'name': 'Организация',
        }


class StatusForm(forms.ModelForm):

    class Meta:

        model = OrderStatus

        fields = ['name', 'user_can_cancel', 'manager_can_use', 'controller_can_use', 'is_default']

        localized_fields = (
            'is_default',
        )

        labels = {
            'name': 'Статус',
            'user_can_cancel': 'Возможно отменить',
            'is_default': 'По умолчанию',
            'manager_can_use': 'Может использовать управляющая компания',
            'controller_can_use': 'Может использовать контролирующий орган',
        }


class OrderPriorityForm(forms.ModelForm):

    class Meta:

        model = OrderPriority

        fields = ['name', 'is_default']

        labels = {
            'name': 'Приоритет',
            'is_default': 'По умолчанию',
        }