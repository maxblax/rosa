from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.contrib.auth.forms import AuthenticationForm
from django import forms


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion personnalisé avec style Tailwind"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personnaliser les champs
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Nom d\'utilisateur'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Mot de passe'
        })

        # Labels français
        self.fields['username'].label = 'Nom d\'utilisateur'
        self.fields['password'].label = 'Mot de passe'


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_view(request):
    """Vue de connexion personnalisée"""

    if request.user.is_authenticated:
        return redirect('beneficiaries:list')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue, {user.get_full_name() or user.username} !')

                # Redirection vers next ou URL par défaut
                next_url = request.GET.get('next', 'beneficiaries:list')
                if next_url.startswith('/'):
                    return redirect(next_url)
                else:
                    return redirect(next_url)
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = CustomAuthenticationForm()

    context = {
        'form': form,
        'next': request.GET.get('next', ''),
    }
    return render(request, 'auth/login.html', context)


def logout_view(request):
    """Vue de déconnexion"""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'Au revoir, {username} ! Vous êtes maintenant déconnecté.')

    return redirect('auth:login')