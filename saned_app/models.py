from django.db import models

class User(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=100, unique=True)
    role = models.CharField(max_length=45, choices=[
        ('beneficiary', 'Beneficiary'),
        ('donor', 'Donor'),
        ('ngo', 'NGO'),
        ('admin', 'Admin')
    ])
    region = models.CharField(max_length=45)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.role}"

class NGOProfile(models.Model):
    organization_name = models.CharField(max_length=100)
    license_document = models.FileField(upload_to='documents/')
    approved = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ngo_profiles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AidRequest(models.Model):
    type = models.CharField(max_length=45)
    description = models.TextField()
    amount_requested = models.IntegerField()
    document = models.FileField(upload_to='documents/')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('delivered', 'Delivered'),
    ], default='pending')
    beneficiary = models.ForeignKey(User, on_delete=models.CASCADE, related_name="aid_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Campaign(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    goal_amount = models.IntegerField()
    deadline = models.DateField()
    ngo = models.ForeignKey(NGOProfile, on_delete=models.CASCADE, related_name="campaigns")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Donation(models.Model):
    amount = models.IntegerField()
    anonymous = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    donation_method = models.CharField(max_length=45)
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="donations")
    request = models.ForeignKey(AidRequest, on_delete=models.CASCADE, related_name="donations", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CampaignDonation(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="campaign_donations")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="campaign_donations")
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
