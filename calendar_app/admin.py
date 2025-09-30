from django.contrib import admin
from django.utils.html import format_html
from .models import (
    VolunteerCalendar, AvailabilitySlot, AvailabilityException, Appointment
)

@admin.register(VolunteerCalendar)
class VolunteerCalendarAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer_name', 'volunteer_role', 'default_view',
        'work_hours', 'show_weekends', 'email_reminders', 'created_at'
    ]
    list_filter = [
        'default_view', 'show_weekends', 'email_reminders',
        'volunteer__role', 'created_at'
    ]
    search_fields = [
        'volunteer__user__first_name', 'volunteer__user__last_name',
        'volunteer__user__email'
    ]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Bénévole', {
            'fields': ('volunteer',)
        }),
        ('Préférences d\'affichage', {
            'fields': ('default_view', 'work_start_time', 'work_end_time', 'show_weekends')
        }),
        ('Notifications', {
            'fields': ('email_reminders', 'reminder_hours_before')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def volunteer_name(self, obj):
        return obj.volunteer.user.get_full_name()
    volunteer_name.short_description = 'Bénévole'

    def volunteer_role(self, obj):
        role_colors = {
            'ADMIN': '#10b981',
            'EMPLOYEE': '#3b82f6',
            'VOLUNTEER_INTERVIEW': '#f59e0b',
            'VOLUNTEER_GOVERNANCE': '#6b7280'
        }
        color = role_colors.get(obj.volunteer.role, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.volunteer.get_role_display()
        )
    volunteer_role.short_description = 'Rôle'

    def work_hours(self, obj):
        return f"{obj.work_start_time.strftime('%H:%M')} - {obj.work_end_time.strftime('%H:%M')}"
    work_hours.short_description = 'Horaires'


class AvailabilityExceptionInline(admin.TabularInline):
    model = AvailabilityException
    extra = 0
    fields = ['exception_date', 'exception_type', 'new_start_time', 'new_end_time', 'reason']


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer_name', 'schedule_display', 'slot_type',
        'duration', 'max_appointments', 'is_bookable', 'is_active'
    ]
    list_filter = [
        'slot_type', 'recurrence_type', 'weekday', 'is_bookable',
        'is_active', 'volunteer_calendar__volunteer__role'
    ]
    search_fields = [
        'volunteer_calendar__volunteer__user__first_name',
        'volunteer_calendar__volunteer__user__last_name',
        'title', 'notes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [AvailabilityExceptionInline]

    fieldsets = (
        ('Bénévole', {
            'fields': ('volunteer_calendar',)
        }),
        ('Créneau', {
            'fields': ('slot_type', 'title', 'notes')
        }),
        ('Récurrence', {
            'fields': ('recurrence_type', 'weekday', 'specific_date')
        }),
        ('Horaires', {
            'fields': ('start_time', 'end_time')
        }),
        ('Validité', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Réservation', {
            'fields': ('is_bookable', 'max_appointments')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def volunteer_name(self, obj):
        return obj.volunteer_calendar.volunteer.user.get_full_name()
    volunteer_name.short_description = 'Bénévole'

    def schedule_display(self, obj):
        if obj.recurrence_type == 'NONE':
            return f"{obj.specific_date} {obj.start_time}-{obj.end_time}"
        else:
            weekday_name = dict(obj.WEEKDAY_CHOICES)[obj.weekday] if obj.weekday is not None else 'N/A'
            recurrence = obj.get_recurrence_type_display()
            return f"{weekday_name} {obj.start_time}-{obj.end_time} ({recurrence})"
    schedule_display.short_description = 'Planification'

    def duration(self, obj):
        return f"{obj.duration_hours:.1f}h"
    duration.short_description = 'Durée'

    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AvailabilityException)
class AvailabilityExceptionAdmin(admin.ModelAdmin):
    list_display = [
        'availability_slot', 'exception_date', 'exception_type',
        'time_change', 'reason', 'created_at'
    ]
    list_filter = [
        'exception_type', 'exception_date', 'created_at'
    ]
    search_fields = [
        'availability_slot__volunteer_calendar__volunteer__user__first_name',
        'availability_slot__volunteer_calendar__volunteer__user__last_name',
        'reason'
    ]
    readonly_fields = ['created_at', 'created_by']

    fieldsets = (
        ('Exception', {
            'fields': ('availability_slot', 'exception_date', 'exception_type')
        }),
        ('Modifications', {
            'fields': ('new_start_time', 'new_end_time', 'new_date'),
            'description': 'Uniquement pour les types "Modifié" et "Déplacé"'
        }),
        ('Détails', {
            'fields': ('reason',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def time_change(self, obj):
        if obj.exception_type == 'CANCELLED':
            return format_html('<span style="color: #ef4444;">Annulé</span>')
        elif obj.exception_type == 'MODIFIED' and obj.new_start_time and obj.new_end_time:
            return f"{obj.new_start_time}-{obj.new_end_time}"
        elif obj.exception_type == 'MOVED' and obj.new_date:
            return f"→ {obj.new_date}"
        return '-'
    time_change.short_description = 'Modification'

    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'volunteer_name', 'beneficiary_name', 'appointment_datetime',
        'appointment_type', 'status', 'duration', 'location'
    ]
    list_filter = [
        'status', 'appointment_type', 'appointment_date', 'created_at'
    ]
    search_fields = [
        'beneficiary__first_name', 'beneficiary__last_name',
        'title', 'description', 'location'
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    date_hierarchy = 'appointment_date'

    fieldsets = (
        ('Participants', {
            'fields': ('volunteer_calendar', 'beneficiary')
        }),
        ('Rendez-vous', {
            'fields': ('appointment_date', 'start_time', 'end_time')
        }),
        ('Détails', {
            'fields': ('appointment_type', 'title', 'description', 'location')
        }),
        ('Statut', {
            'fields': ('status',)
        }),
        ('Notes', {
            'fields': ('preparation_notes', 'completion_notes'),
            'classes': ('collapse',)
        }),
        ('Liens', {
            'fields': ('availability_slot',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def volunteer_name(self, obj):
        if obj.volunteer_calendar:
            return obj.volunteer_calendar.volunteer.user.get_full_name()
        return "Sans bénévole assigné"
    volunteer_name.short_description = 'Bénévole'

    def beneficiary_name(self, obj):
        return f"{obj.beneficiary.first_name} {obj.beneficiary.last_name}"
    beneficiary_name.short_description = 'Bénéficiaire'

    def appointment_datetime(self, obj):
        return f"{obj.appointment_date.strftime('%d/%m/%Y')} {obj.start_time.strftime('%H:%M')}"
    appointment_datetime.short_description = 'Date et heure'

    def duration(self, obj):
        return f"{obj.duration_hours:.1f}h"
    duration.short_description = 'Durée'

    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        # Optimiser les requêtes avec select_related
        return super().get_queryset(request).select_related(
            'beneficiary',
            'availability_slot',
            'created_by'
        ).prefetch_related(
            'volunteer_calendar__volunteer__user'
        )