from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User

class Rating(models.Model):
    """Modèle pour les évaluations entre utilisateurs."""
    
    rater = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='ratings_given',
        verbose_name='Évaluateur'
    )
    rated_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='ratings_received',
        verbose_name='Utilisateur évalué'
    )
    shipment = models.ForeignKey(
        'shipments.Shipment',
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Expédition'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Note'
    )
    comment = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Commentaire'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['rater', 'rated_user', 'shipment']
        verbose_name = 'Évaluation'
        verbose_name_plural = 'Évaluations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Évaluation de {self.rated_user} par {self.rater} - {self.rating}/5"

    def save(self, *args, **kwargs):
        """Sauvegarder et mettre à jour la note moyenne de l'utilisateur évalué."""
        super().save(*args, **kwargs)
        self.update_user_rating()

    def update_user_rating(self):
        """Mettre à jour la note moyenne de l'utilisateur évalué."""
        ratings = Rating.objects.filter(rated_user=self.rated_user)
        if ratings.exists():
            avg_rating = ratings.aggregate(avg=models.Avg('rating'))['avg']
            self.rated_user.rating = round(avg_rating, 2)
            self.rated_user.save() 