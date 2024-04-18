from pprint import pprint

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()


# @receiver(post_save, sender=SocialAccount)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         user=instance.user
#         Profile.objects.create(user=user)


# @receiver(post_save, sender=SocialAccount)
# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()
