from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save  
from django.dispatch import receiver  

class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, blank=True)
    high_score = models.IntegerField(default=0)
    # Add new fields for game state
    current_game_state = models.JSONField(null=True, blank=True)  # Store the current board state
    current_solution = models.JSONField(null=True, blank=True)    # Store the solution
    current_score = models.IntegerField(default=0)               
    current_time = models.IntegerField(default=0)                
    difficulty_level = models.CharField(max_length=20, default='beginner')
    grid_size = models.IntegerField(default=9)  # Size of the in-progress saved game (9 or 16)
    is_game_in_progress = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)  # Add this field


class HighScore(models.Model):
    user_info = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='high_scores')
    grid_size = models.IntegerField()
    best_score = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_info', 'grid_size')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
        UserInfo.objects.create(user=instance, username=instance.username)  

# Signal to save UserInfo when User is saved  
@receiver(post_save, sender=User)  
def save_user_profile(sender, instance, **kwargs):  
    try:  
        instance.userinfo.save()  
    except UserInfo.DoesNotExist:  
        UserInfo.objects.create(user=instance, username=instance.username)  
