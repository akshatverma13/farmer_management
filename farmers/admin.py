from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import UserProfile, Block, Farmer, MonthlyReport
import csv
from datetime import datetime
from django import forms
from django.urls import path
from django.shortcuts import get_object_or_404
import os

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = 'user'  # Specify the ForeignKey to use (the primary relationship)

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

class FarmerDateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('name', 'surveyor', 'block', 'created_at')
    list_filter = ('created_at', 'surveyor', 'block')
    search_fields = ('name',)

    actions = ['download_farmers_csv']

    def download_farmers_csv(self, request, queryset):
        if 'apply' in request.POST:
            form = FarmerDateRangeForm(request.POST)
            if form.is_valid():
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']

                farmers = Farmer.objects.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date
                )

                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="farmers_{start_date}_to_{end_date}.csv"'

                writer = csv.writer(response)
                writer.writerow(['Name', 'Aadhar ID', 'Surveyor', 'Block', 'Farm Area', 'Created At'])

                for farmer in farmers:
                    writer.writerow([
                        farmer.name,
                        farmer.aadhar_id,
                        farmer.surveyor.username if farmer.surveyor else 'N/A',
                        farmer.block.name if farmer.block else 'N/A',
                        farmer.farm_area,
                        farmer.created_at
                    ])

                return response
        else:
            form = FarmerDateRangeForm()

        from django.template.response import TemplateResponse
        return TemplateResponse(
            request,
            'farmers/farmer_date_range_form.html',
            {'form': form, 'title': 'Download Farmers CSV by Date Range'}
        )

    download_farmers_csv.short_description = "Download CSV of farmers by date range"

@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ('report_name', 'created_at', 'download_link')
    list_filter = ('year', 'month')
    search_fields = ('year', 'month')

    def report_name(self, obj):
        return f"Report {obj.year}-{obj.month:02d}"
    report_name.short_description = "Report"

    def download_link(self, obj):
        if obj.file_path:
            return f'<a href="/admin/download-monthly-report/{obj.id}/">Download CSV</a>'
        return "No file available"
    download_link.allow_tags = True
    download_link.short_description = "Download"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('download-monthly-report/<int:report_id>/', self.download_monthly_report, name='download-monthly-report'),
        ]
        return custom_urls + urls

    def download_monthly_report(self, request, report_id):
        report = get_object_or_404(MonthlyReport, id=report_id)
        if not os.path.exists(report.file_path):
            return HttpResponse("File not found", status=404)

        with open(report.file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="monthly_report_{report.year}-{report.month:02d}.csv"'
            return response

# Unregister and re-register User with the custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Block)