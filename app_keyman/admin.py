from django.contrib import admin
from models import Organization, OrderPriority, Building, Performer, OrderStatus, Order, OrganizationUser, \
    BuildingObjectType, Street, UserInfo

# Register your models here.

admin.site.register(Organization)
admin.site.register(OrderPriority)
admin.site.register(Building)
admin.site.register(Performer)
admin.site.register(OrderStatus)
admin.site.register(Order)
admin.site.register(OrganizationUser)
admin.site.register(BuildingObjectType)
admin.site.register(Street)
admin.site.register(UserInfo)