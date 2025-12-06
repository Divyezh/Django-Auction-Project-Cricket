from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import Auction, Team, Player, Bid
import json
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse




def home(request):
    return render(request, 'home.html')


# Show all auctions
def auctions(request):
    auctions = Auction.objects.all().order_by('-tournament_date')  # latest first
    return render(request, 'auctions.html', {"auctions": auctions})



def mybid(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # 1. Find auctions the user participated in
    user_teams = Team.objects.filter(owner=request.user)
    participated_auctions = set(t.auction for t in user_teams)
    
    auction_groups = []
    
    for auction in participated_auctions:
        # 2. Get ALL teams for this auction
        all_teams = Team.objects.filter(auction=auction)
        
        teams_data = []
        for team in all_teams:
            # Calculate stats for each team
            # Note: We need to check if players are sold to this team.
            # The 'won_players' related_name on Player model (from models.py) is useful here if it exists,
            # but let's check how we track sales. 
            # In save_auction_results, we set player.team = team.
            
            won_players = Player.objects.filter(team=team, sold=True)
            total_spent = int(sum(p.price for p in won_players))
            remaining_budget = auction.per_team_budget - total_spent
            
            teams_data.append({
                'team': team,
                'players_won': won_players,
                'total_spent': total_spent,
                'remaining_budget': remaining_budget,
                'is_user_team': team.owner == request.user
            })

        # Sort teams by total spent (descending) or any other metric
        teams_data.sort(key=lambda x: x['total_spent'], reverse=True)

        auction_groups.append({
            'auction': auction,
            'teams_data': teams_data
        })

    return render(request, "mybid.html", {
        "auction_groups": auction_groups
    })








# Register
def register_view(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                return render(request, 'register.html', {'error': 'Username already taken'})
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                return redirect('login')
        else:
            return render(request, 'register.html', {'error': 'Passwords do not match'})
    return render(request, 'register.html')


# Login
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')


# Logout
def logout_view(request):
    logout(request)
    return redirect('login')


# Create Auction (with raw POST)




@login_required
def organize_auction(request):
    if request.method == "POST":
        auction = Auction.objects.create(
            name=request.POST.get("name"),
            location=request.POST.get("location"),
            type=request.POST.get("type"),
            tournament_date=request.POST.get("tournament_date"),
            per_team_budget=request.POST.get("team_budget"),
            password=request.POST.get("auction_password"),
        )

        # Save Teams
        teams = request.POST.getlist("teams[]")
        team_logos = request.FILES.getlist("team_logos[]")
        for i, team_name in enumerate(teams):
            if team_name.strip():
                logo = team_logos[i] if i < len(team_logos) else None
                Team.objects.create(auction=auction, name=team_name, logo=logo, owner=request.user)

        # Save Players
        players = request.POST.getlist("players[]")
        player_images = request.FILES.getlist("player_images[]")
        for i, player_name in enumerate(players):
            if player_name.strip():
                photo = player_images[i] if i < len(player_images) else None
                Player.objects.create(auction=auction, name=player_name, photo=photo)

        return redirect("auctions")

    return render(request, "organize_auction.html")




# Join Auction
def join_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    
    if request.method == "POST":
        entered_password = request.POST.get('password', '').strip()
        
        # Verify password
        if auction.password and entered_password == auction.password:
            # Password correct - redirect to start_bid
            return redirect('start_bid', auction_id=auction_id)
        else:
            # Password incorrect
            messages.error(request, 'Incorrect password. Please try again.')
            return redirect('auctions')
    
    return render(request, "join_auction.html", {"auction": auction})


# Start Auction
def start_auction(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    return render(request, "start_auction.html", {"auction": auction})


# Start Bid
def start_bid(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    teams = auction.teams.all()  # or however you fetch teams
    players_qs = auction.players.order_by('id')  # whatever order you want
    players_list = []
    for p in players_qs:
        players_list.append({
            'id': p.id,
            'name': p.name,
            'photo_url': p.photo.url if p.photo else None,
            'base_price': str(p.price) if p.price else "200000"
        })
    context = {
        'auction': auction,
        'teams': teams,
        'players': players_qs,
        'players_json': json.dumps(players_list),
    }
    return render(request, 'start_bid.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Player, Team

def payment_page(request, team_id, amount):
    team = get_object_or_404(Team, id=team_id)
    
    context = {
        "team": team,
        "amount": amount
    }
    return render(request, "payment.html", context)

def complete_payment(request, team_id, amount):
    """
    Marks payment as complete for a team.
    """
    team = get_object_or_404(Team, id=team_id)

    # Here you would integrate with a payment gateway.
    # For now, we just show the success page.

    messages.success(request, f"Payment of ₹{amount} by {team.name} completed successfully!")
    return render(request, "payment_complete.html", {
        "team": team,
        "amount": amount,
    })

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def save_auction_results(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            results = data.get('results', [])
            
            for item in results:
                team_id = item.get('team_id')
                player_id = item.get('player_id')
                amount = item.get('amount')
                
                team = Team.objects.get(id=team_id)
                player = Player.objects.get(id=player_id)
                
                # Update Player
                player.sold = True
                player.price = amount
                player.team = team
                player.save()
                
                # Create/Update Bid
                bid, created = Bid.objects.get_or_create(
                    team=team, 
                    player=player,
                    defaults={'amount': amount, 'is_winner': True}
                )
                if not created:
                    bid.amount = amount
                    bid.is_winner = True
                    bid.save()
                    
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'invalid method'}, status=400)
