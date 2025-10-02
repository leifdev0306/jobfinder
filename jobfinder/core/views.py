from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout 
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Company, Candidate, JobOffer, Application
from .forms import *

def home(request):
    recent_offers = JobOffer.objects.filter(
        is_active=True, 
        deadline__gte=timezone.now().date()
    ).order_by('-publication_date')[:5]
    
    offers_by_category = JobOffer.objects.filter(
        is_active=True,
        deadline__gte=timezone.now().date()
    ).values('category').annotate(count=Count('id'))
    
    context = {
        'recent_offers': recent_offers,
        'offers_by_category': offers_by_category,
    }
    return render(request, 'core/index.html', context)

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        user_type = request.POST.get('user_type', 'candidate')
        
        if user_form.is_valid():
            user = user_form.save()
            
            if user_type == 'company':
                company_data = {
                    'name': request.POST.get('company_name', ''),
                    'description': request.POST.get('company_description', ''),
                    'location': request.POST.get('company_location', ''),
                    'phone': request.POST.get('company_phone', ''),
                    'website': request.POST.get('company_website', ''),
                }
                
                company_form = CompanyRegisterForm(company_data)
                if company_form.is_valid():
                    company = company_form.save(commit=False)
                    company.user = user
                    company.save()
                    messages.success(request, 'Empresa registrada exitosamente!')
                    
                    username = user_form.cleaned_data.get('username')
                    password = user_form.cleaned_data.get('password1')
                    user = authenticate(username=username, password=password)
                    if user is not None:
                        login(request, user)
                    return redirect('home')
                else:
                    user.delete()
                    messages.error(request, 'Error en los datos de la empresa. Por favor, corrige los errores.')
            else:
                candidate_data = {
                    'phone': request.POST.get('candidate_phone', ''),
                    'location': request.POST.get('candidate_location', ''),
                    'skills': request.POST.get('candidate_skills', ''),
                    'experience': request.POST.get('candidate_experience', ''),
                }
                
                candidate_form = CandidateRegisterForm(candidate_data)
                if candidate_form.is_valid():
                    candidate = candidate_form.save(commit=False)
                    candidate.user = user
                    candidate.save()
                    messages.success(request, 'Candidato registrado exitosamente!')
                    
                    username = user_form.cleaned_data.get('username')
                    password = user_form.cleaned_data.get('password1')
                    user = authenticate(username=username, password=password)
                    if user is not None:
                        login(request, user)
                    return redirect('home')
                else:
                    user.delete()
                    messages.error(request, 'Error en los datos del candidato. Por favor, corrige los errores.')
        else:
            messages.error(request, 'Error en el formulario de usuario. Por favor, corrige los errores.')
    
    else:
        user_form = UserRegisterForm()
    
    return render(request, 'core/register.html', {'user_form': user_form})
    
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso!')
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'core/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente!')
    return redirect('home')

@login_required
def job_offers(request):
    offers = JobOffer.objects.filter(
        is_active=True, 
        deadline__gte=timezone.now().date()
    ).order_by('-publication_date')
    
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    if category:
        offers = offers.filter(category=category)
    if search:
        offers = offers.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(company__name__icontains=search)
        )
    
    context = {'offers': offers}
    return render(request, 'core/offer_list.html', context)

@login_required
def job_offer_detail(request, pk):
    offer = get_object_or_404(JobOffer, pk=pk)
    has_applied = False
    
    if hasattr(request.user, 'candidate'):
        has_applied = Application.objects.filter(
            candidate=request.user.candidate, 
            job_offer=offer
        ).exists()
    
    context = {
        'offer': offer,
        'has_applied': has_applied,
    }
    return render(request, 'core/offer_detail.html', context)

@login_required
def create_job_offer(request):
    try:
        company = request.user.company
    except Company.DoesNotExist:
        messages.error(request, 'Solo las empresas pueden publicar ofertas. Tu usuario no tiene un perfil de empresa.')
        return redirect('home')
    
    if request.method == 'POST':
        form = JobOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.company = company
            offer.save()
            messages.success(request, '🎉 Oferta publicada exitosamente!')
            return redirect('company_dashboard')
        else:
            messages.error(request, '❌ Por favor, corrige los errores en el formulario.')
    else:
        form = JobOfferForm()
    
    return render(request, 'core/offer_form.html', {'form': form, 'editing': False})

@login_required
def edit_job_offer(request, pk):
    try:
        company = request.user.company
    except Company.DoesNotExist:
        messages.error(request, 'Solo las empresas pueden editar ofertas.')
        return redirect('home')
    
    offer = get_object_or_404(JobOffer, pk=pk, company=company)
    
    if request.method == 'POST':
        form = JobOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, '🎉 Oferta actualizada exitosamente!')
            return redirect('company_dashboard')
        else:
            messages.error(request, '❌ Por favor, corrige los errores en el formulario.')
    else:
        form = JobOfferForm(instance=offer)
    
    context = {
        'form': form,
        'offer': offer,
        'editing': True
    }
    return render(request, 'core/offer_form.html', context)

@login_required
def delete_job_offer(request, pk):
    try:
        company = request.user.company
    except Company.DoesNotExist:
        messages.error(request, 'Solo las empresas pueden eliminar ofertas.')
        return redirect('home')
    
    offer = get_object_or_404(JobOffer, pk=pk, company=company)
    
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Oferta eliminada exitosamente!')
        return redirect('company_dashboard')
    
    context = {'offer': offer}
    return render(request, 'core/offer_confirm_delete.html', context)

@login_required
def apply_to_offer(request, pk):
    if not hasattr(request.user, 'candidate'):
        messages.error(request, 'Solo los candidatos pueden postularse a ofertas.')
        return redirect('home')
    
    offer = get_object_or_404(JobOffer, pk=pk)
    
    if Application.objects.filter(candidate=request.user.candidate, job_offer=offer).exists():
        messages.error(request, 'Ya te has postulado a esta oferta.')
        return redirect('job_offer_detail', pk=pk)
    
    if offer.is_expired:
        messages.error(request, 'Esta oferta ha expirada.')
        return redirect('job_offer_detail', pk=pk)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            try:
                application = form.save(commit=False)
                application.candidate = request.user.candidate
                application.job_offer = offer
                
                try:
                    application.full_clean()
                    application.save()
                    messages.success(request, 'Postulación enviada exitosamente!')
                    return redirect('my_applications')
                except ValidationError as e:
                    for field, errors in e.error_dict.items():
                        for error in errors:
                            messages.error(request, f'{field}: {error}')
            except Exception as e:
                messages.error(request, f'Error al guardar la aplicación: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ApplicationForm()
    
    context = {'form': form, 'offer': offer}
    return render(request, 'core/apply.html', context)

@login_required
def cancel_application(request, pk):
    if not hasattr(request.user, 'candidate'):
        messages.error(request, 'Solo los candidatos pueden cancelar postulaciones.')
        return redirect('home')
    
    application = get_object_or_404(Application, pk=pk, candidate=request.user.candidate)
    
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Postulación cancelada exitosamente!')
        return redirect('my_applications')
    
    context = {'application': application}
    return render(request, 'core/application_confirm_cancel.html', context)

@login_required
def my_applications(request):
    if not hasattr(request.user, 'candidate'):
        messages.error(request, 'Acceso restringido a candidatos.')
        return redirect('home')
    
    applications = Application.objects.filter(candidate=request.user.candidate)
    context = {'applications': applications}
    return render(request, 'core/my_applications.html', context)

@login_required
def company_dashboard(request):
    if not hasattr(request.user, 'company'):
        messages.error(request, 'Acceso restringido a empresas.')
        return redirect('home')
    
    company = request.user.company
    offers = JobOffer.objects.filter(company=company).annotate(
        application_count=Count('application')
    )
    applications = Application.objects.filter(job_offer__company=company)
    
    # Calcular estadísticas en la vista
    total_offers = offers.count()
    total_applications = applications.count()
    active_offers = offers.filter(is_active=True, deadline__gte=timezone.now().date()).count()
    
    context = {
        'offers': offers,
        'applications': applications,
        'total_offers': total_offers,
        'total_applications': total_applications,
        'active_offers': active_offers,
    }
    return render(request, 'core/company_dashboard.html', context)

@login_required
def application_list(request, offer_pk):
    if not hasattr(request.user, 'company'):
        messages.error(request, 'Acceso restringido a empresas.')
        return redirect('home')
    
    offer = get_object_or_404(JobOffer, pk=offer_pk, company=request.user.company)
    applications = Application.objects.filter(job_offer=offer).select_related(
        'candidate', 'candidate__user', 'job_offer'
    )
    
    context = {
        'offer': offer,
        'applications': applications,
    }
    return render(request, 'core/application_list.html', context)

@login_required
def update_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk)
    
    if request.user != application.job_offer.company.user:
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado actualizado exitosamente!')
            return redirect('application_list', offer_pk=application.job_offer.pk)
    else:
        form = ApplicationStatusForm(instance=application)
    
    context = {'form': form, 'application': application}
    return render(request, 'core/update_application_status.html', context)

@login_required
def offers_by_category(request):
    offers_count = JobOffer.objects.filter(
        is_active=True,
        deadline__gte=timezone.now().date()
    ).values('category').annotate(count=Count('id'))
    
    context = {'offers_count': offers_count}
    return render(request, 'core/offers_by_category.html', context)

@login_required
def recent_offers(request):
    recent_offers = JobOffer.objects.filter(
        is_active=True,
        deadline__gte=timezone.now().date()
    ).order_by('-publication_date')[:10]
    
    context = {'recent_offers': recent_offers}
    return render(request, 'core/recent_offers.html', context)

@login_required
def offers_expiring_soon(request):
    next_week = timezone.now().date() + timedelta(days=7)
    expiring_offers = JobOffer.objects.filter(
        is_active=True,
        deadline__gte=timezone.now().date(),
        deadline__lte=next_week
    ).order_by('deadline')
    
    context = {'expiring_offers': expiring_offers}
    return render(request, 'core/offers_expiring_soon.html', context)