from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Beneficiary, FinancialSnapshot, Child, Interaction
from .forms import BeneficiaryForm, FinancialSnapshotForm, ChildForm, ChildFormSet, InteractionForm
from volunteers.permissions import CanModifyBeneficiariesMixin


class BeneficiaryListView(CanModifyBeneficiariesMixin, ListView):
    """Vue liste des bénéficiaires avec recherche"""
    model = Beneficiary
    template_name = 'beneficiaries/list.html'
    context_object_name = 'beneficiaries'
    paginate_by = 20

    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        return queryset.select_related().prefetch_related('financial_snapshots')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class BeneficiaryCreateView(CanModifyBeneficiariesMixin, CreateView):
    """Vue de création d'un nouveau bénéficiaire avec snapshot financier initial"""
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'beneficiaries/create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['financial_form'] = FinancialSnapshotForm(self.request.POST)
        else:
            context['financial_form'] = FinancialSnapshotForm()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        financial_form = context['financial_form']
        
        with transaction.atomic():
            if financial_form.is_valid():
                # Sauvegarder le bénéficiaire
                self.object = form.save()
                
                # Sauvegarder le snapshot financier
                financial_snapshot = financial_form.save(commit=False)
                financial_snapshot.beneficiary = self.object
                financial_snapshot.save()
                
                messages.success(
                    self.request, 
                    f'Bénéficiaire {self.object.full_name} créé avec succès.'
                )
                return redirect(self.get_success_url())
            else:
                return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('beneficiaries:detail', kwargs={'pk': self.object.pk})


class BeneficiaryDetailView(CanModifyBeneficiariesMixin, DetailView):
    """Vue détail d'un bénéficiaire avec historique financier"""
    model = Beneficiary
    template_name = 'beneficiaries/detail.html'
    context_object_name = 'beneficiary'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['financial_snapshots'] = self.object.financial_snapshots.all()[:10]  # Derniers 10
        context['latest_snapshot'] = self.object.latest_financial_snapshot
        context['children'] = self.object.children.all()
        context['interactions'] = self.object.interactions.select_related('user').all()[:10]  # Dernières 10
        return context


class BeneficiaryUpdateView(CanModifyBeneficiariesMixin, UpdateView):
    """Vue d'édition d'un bénéficiaire"""
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'beneficiaries/edit.html'
    context_object_name = 'beneficiary'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['children_formset'] = ChildFormSet(self.request.POST, prefix='children')
        else:
            # Créer un formset avec les enfants existants
            children_data = []
            for child in self.object.children.all():
                children_data.append({
                    'first_name': child.first_name,
                    'last_name': child.last_name,
                    'birth_date': child.birth_date,
                    'observations': child.observations
                })
            context['children_formset'] = ChildFormSet(initial=children_data, prefix='children')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        children_formset = context['children_formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if children_formset.is_valid():
                # Supprimer les enfants existants
                self.object.children.all().delete()
                
                # Créer les nouveaux enfants
                for child_form in children_formset:
                    if child_form.cleaned_data and not child_form.cleaned_data.get('DELETE', False):
                        child = child_form.save(commit=False)
                        child.beneficiary = self.object
                        child.save()
                
                messages.success(self.request, 'Bénéficiaire modifié avec succès.')
                return redirect(self.object.get_absolute_url())
        
        return self.form_invalid(form)


@login_required
def financial_snapshot_create_view(request, pk):
    """Vue pour créer/modifier une photo instantanée financière mensuelle pour un bénéficiaire existant"""
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    
    # Obtenir le mois courant
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Chercher un snapshot existant pour le mois courant
    current_month_snapshot = beneficiary.financial_snapshots.filter(
        date__gte=current_month_start,
        date__month=now.month,
        date__year=now.year
    ).first()
    
    if request.method == 'POST':
        if current_month_snapshot:
            # Modifier le snapshot existant du mois courant
            form = FinancialSnapshotForm(request.POST, instance=current_month_snapshot)
            action_message = 'Photo instantanée financière mise à jour avec succès.'
        else:
            # Créer un nouveau snapshot
            form = FinancialSnapshotForm(request.POST)
            action_message = 'Photo instantanée financière créée avec succès.'
            
        if form.is_valid():
            snapshot = form.save(commit=False)
            snapshot.beneficiary = beneficiary
            
            # Si c'est une modification, mettre à jour la date
            if current_month_snapshot:
                snapshot.date = timezone.now()
            
            snapshot.save()
            
            messages.success(request, action_message)
            return redirect('beneficiaries:detail', pk=beneficiary.pk)
    else:
        if current_month_snapshot:
            # Utiliser le snapshot du mois courant pour modification
            form = FinancialSnapshotForm(instance=current_month_snapshot)
            form.is_update = True
        else:
            # Pré-remplir avec les données du dernier snapshot si disponible
            latest_snapshot = beneficiary.latest_financial_snapshot
            if latest_snapshot:
                # Créer un nouveau snapshot basé sur le dernier, mais avec des valeurs null pour les champs à 0
                form = FinancialSnapshotForm(instance=latest_snapshot)
                # Nettoyer les valeurs 0 pour les afficher comme null
                for field_name, field in form.fields.items():
                    if hasattr(latest_snapshot, field_name):
                        value = getattr(latest_snapshot, field_name)
                        if value == 0 or value == 0.00:
                            form.initial[field_name] = None
            else:
                form = FinancialSnapshotForm()
            form.is_update = False
    
    # Retourner la page complète
    context = {
        'form': form,
        'beneficiary': beneficiary,
        'is_update': getattr(form, 'is_update', False),
        'current_month_snapshot': current_month_snapshot
    }
    return render(request, 'beneficiaries/financial_snapshot_create.html', context)


@login_required
def beneficiary_search_autocomplete(request):
    """Vue pour l'autocomplétion de recherche de bénéficiaires (pour HTMX)"""
    query = request.GET.get('q', '')
    beneficiaries = []
    
    if query and len(query) >= 2:
        beneficiaries = Beneficiary.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:10]
    
    if request.headers.get('HX-Request'):
        context = {'beneficiaries': beneficiaries, 'query': query}
        return render(request, 'beneficiaries/partials/search_results.html', context)
    
    # Fallback JSON pour autres usages
    results = [
        {
            'id': b.pk,
            'name': b.full_name,
            'email': b.email,
            'url': reverse('beneficiaries:detail', kwargs={'pk': b.pk})
        }
        for b in beneficiaries
    ]
    return JsonResponse({'results': results})


class InteractionCreateView(CanModifyBeneficiariesMixin, CreateView):
    """Vue pour créer une nouvelle interaction avec un bénéficiaire"""
    model = Interaction
    form_class = InteractionForm
    template_name = 'beneficiaries/interaction_create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.beneficiary = get_object_or_404(Beneficiary, pk=kwargs['beneficiary_pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['beneficiary'] = self.beneficiary
        
        # Ajouter le formulaire de snapshot financier pré-rempli avec les dernières données
        if self.request.POST:
            context['financial_form'] = FinancialSnapshotForm(self.request.POST)
        else:
            # Pré-remplir avec les données du dernier snapshot si disponible
            latest_snapshot = self.beneficiary.latest_financial_snapshot
            if latest_snapshot:
                context['financial_form'] = FinancialSnapshotForm(instance=latest_snapshot)
                # Nettoyer les valeurs 0 pour les afficher comme vides
                for field_name, field in context['financial_form'].fields.items():
                    if hasattr(latest_snapshot, field_name):
                        value = getattr(latest_snapshot, field_name)
                        if value == 0 or value == 0.00:
                            context['financial_form'].initial[field_name] = None
            else:
                context['financial_form'] = FinancialSnapshotForm()
        
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            # Sauvegarder l'interaction
            self.object = form.save(commit=False)
            self.object.beneficiary = self.beneficiary
            # Assigner l'utilisateur seulement s'il est connecté
            if self.request.user.is_authenticated:
                self.object.user = self.request.user
            self.object.save()
            
            # Si un snapshot financier est renseigné, le sauvegarder
            # On ne bloque jamais l'interaction, même si les données financières ont des problèmes
            if self._has_financial_data_from_request():
                try:
                    # Créer le snapshot manuellement avec les données POST
                    financial_snapshot = FinancialSnapshot(beneficiary=self.beneficiary)
                    
                    # Parcourir tous les champs du modèle FinancialSnapshot
                    for field in FinancialSnapshot._meta.fields:
                        if field.name not in ['id', 'beneficiary', 'date']:
                            value = self.request.POST.get(field.name, '')
                            if value == '' or value is None:
                                setattr(financial_snapshot, field.name, 0)
                            else:
                                try:
                                    setattr(financial_snapshot, field.name, float(value))
                                except (ValueError, TypeError):
                                    setattr(financial_snapshot, field.name, 0)
                    
                    financial_snapshot.save()
                    
                    # Associer le snapshot à l'interaction
                    self.object.financial_snapshot = financial_snapshot
                    self.object.save()
                except Exception as e:
                    # Si la création du snapshot échoue, on continue quand même
                    print(f"Erreur lors de la création du snapshot: {e}")
            
            messages.success(
                self.request, 
                f'Interaction "{self.object.title}" créée avec succès.'
            )
            
            return redirect(self.get_success_url())
    
    def _has_financial_data_from_request(self):
        """Vérifie si la requête contient des données financières"""
        # Parcourir tous les champs du modèle FinancialSnapshot
        for field in FinancialSnapshot._meta.fields:
            if field.name not in ['id', 'beneficiary', 'date']:
                value = self.request.POST.get(field.name, '')
                if value and value.strip() and value != '0':
                    return True
        return False
    
    def _has_financial_data(self, financial_form):
        """Vérifie si le formulaire financier contient des données (méthode legacy)"""
        return self._has_financial_data_from_request()
    
    def get_success_url(self):
        return reverse('beneficiaries:detail', kwargs={'pk': self.beneficiary.pk})


class InteractionDetailView(CanModifyBeneficiariesMixin, DetailView):
    """Vue détail d'une interaction"""
    model = Interaction
    template_name = 'beneficiaries/interaction_detail.html'
    context_object_name = 'interaction'
    
    def get_object(self):
        return get_object_or_404(
            Interaction, 
            pk=self.kwargs['pk'], 
            beneficiary__pk=self.kwargs['beneficiary_pk']
        )


class InteractionUpdateView(CanModifyBeneficiariesMixin, UpdateView):
    """Vue pour modifier une interaction"""
    model = Interaction
    form_class = InteractionForm
    template_name = 'beneficiaries/interaction_edit.html'
    context_object_name = 'interaction'
    
    def get_object(self):
        return get_object_or_404(
            Interaction, 
            pk=self.kwargs['pk'], 
            beneficiary__pk=self.kwargs['beneficiary_pk']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['beneficiary'] = self.object.beneficiary
        return context
    
    def get_success_url(self):
        messages.success(self.request, 'Interaction modifiée avec succès.')
        return reverse('beneficiaries:interaction_detail', kwargs={
            'beneficiary_pk': self.object.beneficiary.pk,
            'pk': self.object.pk
        })
