from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=200)
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class JobOffer(models.Model):
    CATEGORY_CHOICES = [
        ('💻 Desarrollo de Software', '💻 Desarrollo de Software'),
        ('📊 Marketing Digital', '📊 Marketing Digital'),
        ('🎨 Diseño Gráfico', '🎨 Diseño Gráfico'),
        ('✍️ Redacción de Contenidos', '✍️ Redacción de Contenidos'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    location = models.CharField(max_length=200)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    requirements = models.TextField()
    publication_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-publication_date']

    def __str__(self):
        return self.title

    def clean(self):
        if self.deadline < timezone.now().date():
            raise ValidationError('La fecha límite no puede ser en el pasado.')

    @property
    def is_expired(self):
        return self.deadline < timezone.now().date()

class Application(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('revisada', 'Revisada'),
        ('contactado', 'Contactado'),
        ('rechazada', 'Rechazada'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE)
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    cover_letter = models.TextField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['candidate', 'job_offer']
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.candidate} - {self.job_offer}"

    def clean(self):
        if hasattr(self, 'job_offer') and self.job_offer:
            if self.job_offer.is_expired:
                raise ValidationError('No puedes postularte a una oferta expirada.')

    def save(self, *args, **kwargs):
        if self.job_offer_id:
            self.full_clean()
        super().save(*args, **kwargs)