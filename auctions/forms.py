# auctions/forms.py
from django import forms
from .models import Auction

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['name', 'location', 'type', 'tournament_date', 'per_team_budget', 'description']
