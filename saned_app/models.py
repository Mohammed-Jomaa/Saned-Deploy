from django.db import models
from django.db import models

# Create your models here.
class User(models.Model):
    first_name=models.CharField(max_length=255)
    last_name=models.CharField(max_length=255)
    email=models.CharField(max_length=45)
    role=models.CharField(max_length=45)
    region=models.CharField(max_length=45)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class NGOProfile(models.Model):
    organization_name=models.CharField(max_length=45)
    license_document=models.TextField()
    approved=models.BooleanField(default=False)
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="ngo-profiles")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class AidRequest(models.Model):
    type=models.CharField(max_length=45)
    description=models.TextField()
    amount_requested=models.IntegerField()
    document=models.TextField()
    status=models.CharField(max_length=45)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    beneficiary=models.ForeignKey(User,on_delete=models.CASCADE,related_name="aid_request")

class Campaign(models.Model):
    title=models.CharField(max_length=45)
    description=models.TextField()
    goal_amount=models.IntegerField()
    deadline=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    ngo=models.ForeignKey(NGOProfile,on_delete=models.CASCADE,related_name="campaigns")

class Donation(models.Model):
    amount=models.IntegerField()
    anonymous=models.BooleanField(default=False)
    message=models.TextField(blank=True,null=True)
    donation_method=models.CharField(max_length=45)
    created_at=models.DateTimeField(auto_now_add=True)
    donor=models.ForeignKey(User,on_delete=models.CASCADE,related_name="donations")
    request=models.ForeignKey(AidRequest,on_delete=models.CASCADE,related_name="donations",null=True,blank=True)

class CampaignDonation(models.Model):
    donor=models.ForeignKey(User,on_delete=models.CASCADE,related_name="campaign_donations")
    campaign=models.ForeignKey(Campaign,on_delete=models.CASCADE,related_name="campaign_donations")
    created_at=models.DateTimeField(auto_now_add=True)

    




    
# Create your models here.
