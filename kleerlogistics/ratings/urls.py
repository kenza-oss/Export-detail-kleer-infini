from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    # Créer une évaluation
    path('create/', views.create_rating, name='create_rating'),
    
    # Obtenir les évaluations d'un utilisateur
    path('user/<int:user_id>/', views.get_user_ratings, name='user_ratings'),
    
    # Obtenir le résumé des évaluations d'un utilisateur
    path('user/<int:user_id>/summary/', views.get_user_rating_summary, name='user_rating_summary'),
    
    # Obtenir les évaluations d'une expédition
    path('shipment/<int:shipment_id>/', views.get_shipment_ratings, name='shipment_ratings'),
    
    # Modifier ou supprimer une évaluation
    path('<int:rating_id>/', views.update_rating, name='update_rating'),
    
    # Lister les évaluations avec filtres
    path('list/', views.RatingListView.as_view(), name='rating_list'),
] 