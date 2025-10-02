from django.contrib import admin
from .models import Company, Candidate, JobOffer, Application

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'created_at']
    search_fields = ['name', 'location']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'location']

@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'category', 'publication_date', 'deadline', 'is_active']
    list_filter = ['category', 'is_active', 'publication_date']
    search_fields = ['title', 'company__name']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job_offer', 'application_date', 'status']
    list_filter = ['status', 'application_date']
    search_fields = ['candidate__user__first_name', 'job_offer__title']