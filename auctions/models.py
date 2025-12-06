from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Auction(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    tournament_date = models.DateField()
    per_team_budget = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)

class Team(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="team_user",   # unique backward relation
        null=True,
        blank=True
    )
    auction = models.ForeignKey(
        'Auction',
        on_delete=models.CASCADE,
        related_name="teams"
    )
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_teams",  # another unique backward relation
        null=True,
        blank=True
    )
    logo = models.ImageField(upload_to="team_logos/", null=True, blank=True)

    def __str__(self):
        return self.name



class Player(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sold = models.BooleanField(default=False)
    photo = models.ImageField(upload_to="players_images/", null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_players")
   





    def __str__(self):
        return self.name
    
class Bid(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_winner = models.BooleanField(default=False)
    auction_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.team.name} - {self.player.name}"

