from django.contrib import admin

from .models import Service, ServiceSession, ServiceRegistration, ServiceBooking, FinancialAidRequest


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'category', 'is_active', 'order']
    list_filter = ['kind', 'category', 'is_active']


@admin.register(ServiceSession)
class ServiceSessionAdmin(admin.ModelAdmin):
    list_display = ['service', 'date', 'capacity', 'is_closed']
    list_filter = ['service', 'is_closed']


class ServiceBookingInline(admin.TabularInline):
    model = ServiceBooking
    extra = 0


@admin.register(ServiceRegistration)
class ServiceRegistrationAdmin(admin.ModelAdmin):
    list_display = ['beneficiary', 'service', 'status', 'created_at', 'created_by']
    list_filter = ['service', 'status']
    inlines = [ServiceBookingInline]


@admin.register(FinancialAidRequest)
class FinancialAidRequestAdmin(admin.ModelAdmin):
    list_display = ['beneficiary', 'amount', 'nature', 'status', 'created_at', 'requested_by', 'decided_by']
    list_filter = ['status', 'nature']
