from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path("organize-auctions/", views.organize_auction, name="organize_auction"),
    path("auctions/", views.auctions, name="auctions"),
    path("join-auction/<int:auction_id>/", views.join_auction, name="join_auction"),
    path("start-auction/<int:auction_id>/", views.start_auction, name="start_auction"),
    path('start-bid/<int:auction_id>/', views.start_bid, name='start_bid'),
    path('mybid/', views.mybid, name='mybid'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path("payment/<int:team_id>/<int:amount>/", views.payment_page, name="payment_page"),
    path("complete-payment/<int:team_id>/<int:amount>/", views.complete_payment, name="complete_payment"),
    path("save-auction-results/", views.save_auction_results, name="save_auction_results"),

    

]

