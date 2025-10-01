from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Partner
from .forms import PartnerForm


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux salariés et administrateurs"""

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        if hasattr(user, 'volunteer_profile'):
            return user.volunteer_profile.role in ['ADMIN', 'EMPLOYEE']
        return False

    def handle_no_permission(self):
        messages.error(
            self.request,
            "Vous n'avez pas les permissions nécessaires pour effectuer cette action."
        )
        return redirect('partners:list')


class PartnerListView(LoginRequiredMixin, ListView):
    """Vue liste des partenaires avec recherche et filtres"""
    model = Partner
    template_name = 'partners/list.html'
    context_object_name = 'partners'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        service_filter = self.request.GET.get('service', '')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(services__icontains=search_query)
            )

        if service_filter:
            queryset = queryset.filter(services__icontains=service_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['service_filter'] = self.request.GET.get('service', '')

        # Obtenir tous les services uniques pour le filtre
        all_services = set()
        for partner in Partner.objects.all():
            all_services.update(partner.get_services_list())
        context['all_services'] = sorted(all_services)

        return context


class PartnerCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Vue de création d'un nouveau partenaire"""
    model = Partner
    form_class = PartnerForm
    template_name = 'partners/create.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            f'Partenaire {self.object.name} créé avec succès.'
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('partners:list')


class PartnerUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Vue d'édition d'un partenaire"""
    model = Partner
    form_class = PartnerForm
    template_name = 'partners/edit.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            f'Partenaire {self.object.name} modifié avec succès.'
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('partners:list')


class PartnerDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """Vue de suppression d'un partenaire"""
    model = Partner
    success_url = reverse_lazy('partners:list')

    def delete(self, request, *args, **kwargs):
        partner = self.get_object()
        messages.success(
            request,
            f'Partenaire {partner.name} supprimé avec succès.'
        )
        return super().delete(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Supprimer directement sans page de confirmation
        return self.delete(request, *args, **kwargs)


@require_http_methods(["GET"])
def get_all_services(request):
    """API endpoint pour récupérer tous les services uniques"""
    all_services = set()
    for partner in Partner.objects.all():
        all_services.update(partner.get_services_list())

    # Convertir en liste et trier (insensible à la casse)
    services_list = sorted(list(all_services), key=str.lower)

    return JsonResponse({'services': services_list})
