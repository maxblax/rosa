"""Champs de formulaire partages, tolerants aux saisies clavier "naturelles".

Reutilises par toutes les apps pour eviter les widgets HTML natifs qui
rejettent silencieusement la saisie (input type=date, input type=number).
"""
from django import forms


def normalize_decimal_string(value):
    """Nettoie une saisie utilisateur en nombre decimal.

    Tolere espaces (y compris insecables), separateurs milliers virgule/point,
    et virgule decimale. Renvoie la valeur d'origine si non-str.
    """
    if value is None:
        return value
    if not isinstance(value, str):
        return value
    s = value.strip()
    if not s:
        return s
    s = s.replace('\u00a0', '').replace('\u202f', '').replace(' ', '')
    if ',' in s and '.' in s:
        if s.rfind('.') > s.rfind(','):
            s = s.replace(',', '')
        else:
            s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    return s


class TolerantDecimalField(forms.DecimalField):
    """DecimalField qui tolere les espaces et la virgule comme separateur."""

    def to_python(self, value):
        return super().to_python(normalize_decimal_string(value))


TOLERANT_DATE_FORMATS = (
    '%d/%m/%Y',  # 17/03/2008
    '%d-%m-%Y',  # 17-03-2008
    '%d.%m.%Y',  # 17.03.2008
    '%d/%m/%y',  # 17/03/08
    '%Y-%m-%d',  # ISO, format natif input type=date
)


class TolerantDateField(forms.DateField):
    """DateField rendu en <input type=text> avec parsing tolerant.

    Le widget natif type=date impose AAAA-MM-JJ et bloque les anciennes dates
    dans certains navigateurs. Cette variante accepte JJ/MM/AAAA et plusieurs
    separateurs cote serveur.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('input_formats', TOLERANT_DATE_FORMATS)
        kwargs.setdefault(
            'widget',
            forms.TextInput(attrs={
                'inputmode': 'numeric',
                'placeholder': 'JJ/MM/AAAA',
                'data-tolerant-date': 'true',
                'autocomplete': 'off',
            }),
        )
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if hasattr(value, 'strftime'):
            return value.strftime('%d/%m/%Y')
        return super().prepare_value(value)
