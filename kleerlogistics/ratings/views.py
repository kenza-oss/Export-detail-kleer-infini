from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404

from .models import Rating
from .serializers import RatingSerializer, RatingCreateSerializer, UserRatingSummarySerializer
from users.models import User

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_rating(request):
    """Créer une nouvelle évaluation."""
    serializer = RatingCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Ajouter l'utilisateur connecté comme évaluateur
        serializer.save(rater=request.user)
        return Response({
            'success': True,
            'message': 'Évaluation créée avec succès',
            'rating': RatingSerializer(serializer.instance).data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_ratings(request, user_id):
    """Obtenir les évaluations d'un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    ratings = Rating.objects.filter(rated_user=user)
    
    serializer = RatingSerializer(ratings, many=True)
    return Response({
        'success': True,
        'ratings': serializer.data,
        'total_ratings': ratings.count()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_rating_summary(request, user_id):
    """Obtenir le résumé des évaluations d'un utilisateur."""
    user = get_object_or_404(User, id=user_id)
    ratings = Rating.objects.filter(rated_user=user)
    
    if not ratings.exists():
        return Response({
            'success': True,
            'rating_summary': {
                'average_rating': 0.0,
                'total_ratings': 0,
                'rating_distribution': {}
            }
        })
    
    # Calculer la moyenne
    average_rating = ratings.aggregate(avg=Avg('rating'))['avg']
    
    # Calculer la distribution des notes
    rating_distribution = {}
    for i in range(1, 6):
        count = ratings.filter(rating=i).count()
        rating_distribution[str(i)] = count
    
    data = {
        'average_rating': round(average_rating, 2),
        'total_ratings': ratings.count(),
        'rating_distribution': rating_distribution
    }
    
    serializer = UserRatingSummarySerializer(data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_shipment_ratings(request, shipment_id):
    """Obtenir les évaluations d'une expédition."""
    ratings = Rating.objects.filter(shipment_id=shipment_id)
    
    serializer = RatingSerializer(ratings, many=True)
    return Response({
        'success': True,
        'ratings': serializer.data,
        'total_ratings': ratings.count()
    })

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_rating(request, rating_id):
    """Modifier ou supprimer une évaluation."""
    rating = get_object_or_404(Rating, id=rating_id, rater=request.user)
    
    if request.method == 'PUT':
        serializer = RatingSerializer(rating, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Évaluation mise à jour avec succès',
                'rating': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        rating.delete()
        return Response({
            'success': True,
            'message': 'Évaluation supprimée avec succès'
        })

class RatingListView(generics.ListAPIView):
    """Vue pour lister les évaluations avec filtres."""
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Rating.objects.all()
        
        # Filtres
        rated_user = self.request.query_params.get('rated_user')
        rater = self.request.query_params.get('rater')
        shipment = self.request.query_params.get('shipment')
        min_rating = self.request.query_params.get('min_rating')
        max_rating = self.request.query_params.get('max_rating')
        
        if rated_user:
            queryset = queryset.filter(rated_user_id=rated_user)
        if rater:
            queryset = queryset.filter(rater_id=rater)
        if shipment:
            queryset = queryset.filter(shipment_id=shipment)
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        if max_rating:
            queryset = queryset.filter(rating__lte=max_rating)
        
        return queryset 