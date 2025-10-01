from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q

from .models import Product
from .forms import ProductForm, AdjustQuantityForm


class ProductListView(ListView):
    """Liste tous les produits en stock."""
    model = Product
    template_name = 'stock/list.html'
    context_object_name = 'products'
    paginate_by = 50

    def get_queryset(self):
        queryset = Product.objects.all()
        search_query = self.request.GET.get('search', '')
        category_filter = self.request.GET.get('category', '')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if category_filter:
            queryset = queryset.filter(category=category_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['categories'] = Product.CATEGORY_CHOICES

        # Stats rapides
        all_products = Product.objects.all()
        context['total_products'] = all_products.count()
        context['low_stock_count'] = sum(1 for p in all_products if p.is_low_stock)

        return context


class ProductCreateView(CreateView):
    """Creer un nouveau produit."""
    model = Product
    form_class = ProductForm
    template_name = 'stock/create.html'
    success_url = reverse_lazy('stock:list')

    def form_valid(self, form):
        messages.success(self.request, f'Produit "{form.instance.name}" cr�� avec succ�s.')
        return super().form_valid(form)


class ProductUpdateView(UpdateView):
    """editer un produit existant."""
    model = Product
    form_class = ProductForm
    template_name = 'stock/edit.html'
    success_url = reverse_lazy('stock:list')

    def form_valid(self, form):
        messages.success(self.request, f'Produit "{form.instance.name}" modifie avec succes.')
        return super().form_valid(form)


class ProductDeleteView(DeleteView):
    """Supprimer un produit."""
    model = Product
    template_name = 'stock/delete.html'
    success_url = reverse_lazy('stock:list')

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        messages.success(request, f'Produit "{product.name}" supprime avec succes.')
        return super().delete(request, *args, **kwargs)


def adjust_quantity_view(request, pk):
    """Vue pour ajuster rapidement la quantit� d'un produit (+/-)."""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = AdjustQuantityForm(request.POST)
        if form.is_valid():
            adjustment = form.cleaned_data['adjustment']
            note = form.cleaned_data.get('note', '')

            # Appliquer l'ajustement
            product.quantity += adjustment

            # Emp�cher les quantit�s n�gatives
            if product.quantity < 0:
                messages.error(request, 'La quantite ne peut pas etre negative.')
                product.quantity = 0

            product.save()

            # Message de confirmation
            action = "ajoute" if adjustment > 0 else "retire"
            msg = f'{abs(adjustment)} {product.unit} {action} au stock de "{product.name}".'
            if note:
                msg += f' Note: {note}'
            messages.success(request, msg)

            return redirect('stock:list')
    else:
        form = AdjustQuantityForm()

    context = {
        'product': product,
        'form': form,
    }
    return render(request, 'stock/adjust.html', context)
