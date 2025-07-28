from rest_framework import serializers
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    """Serializer pour les évaluations."""
    
    rater_name = serializers.SerializerMethodField()
    rated_user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Rating
        fields = [
            'id', 'rater', 'rater_name', 'rated_user', 'rated_user_name',
            'shipment', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'rater_name', 'rated_user_name']
    
    def get_rater_name(self, obj):
        """Obtenir le nom de l'évaluateur."""
        return f"{obj.rater.first_name} {obj.rater.last_name}"
    
    def get_rated_user_name(self, obj):
        """Obtenir le nom de l'utilisateur évalué."""
        return f"{obj.rated_user.first_name} {obj.rated_user.last_name}"
    
    def validate(self, attrs):
        """Valider les données d'évaluation."""
        # Empêcher qu'un utilisateur s'évalue lui-même
        if attrs['rater'] == attrs['rated_user']:
            raise serializers.ValidationError("Vous ne pouvez pas vous évaluer vous-même.")
        
        # Vérifier qu'une évaluation n'existe pas déjà pour cette expédition
        if Rating.objects.filter(
            rater=attrs['rater'],
            rated_user=attrs['rated_user'],
            shipment=attrs['shipment']
        ).exists():
            raise serializers.ValidationError("Vous avez déjà évalué cet utilisateur pour cette expédition.")
        
        return attrs

class RatingCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une évaluation."""
    
    class Meta:
        model = Rating
        fields = ['rated_user', 'shipment', 'rating', 'comment']
    
    def validate_rating(self, value):
        """Valider la note."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note doit être comprise entre 1 et 5.")
        return value

class UserRatingSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des évaluations d'un utilisateur."""
    
    average_rating = serializers.FloatField()
    total_ratings = serializers.IntegerField()
    rating_distribution = serializers.DictField()
    
    def to_representation(self, instance):
        """Formater les données pour l'API."""
        return {
            'success': True,
            'rating_summary': {
                'average_rating': instance['average_rating'],
                'total_ratings': instance['total_ratings'],
                'rating_distribution': instance['rating_distribution']
            }
        } 