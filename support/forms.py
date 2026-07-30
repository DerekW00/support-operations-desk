from django import forms
from support.provider import CATEGORIES


class ReviewForm(forms.Form):
    expected_revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    category = forms.ChoiceField(choices=[(c, c.title()) for c in CATEGORIES])
    reply = forms.CharField(
        label="Draft reply", max_length=4000, widget=forms.Textarea(attrs={"rows": 7})
    )


class ImportForm(forms.Form):
    tickets = forms.CharField(
        label="Synthetic ticket JSON", widget=forms.Textarea(attrs={"rows": 10}), max_length=262144
    )
