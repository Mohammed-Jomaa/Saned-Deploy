from django.contrib import admin
from .models import NGOProfile

# Register your models here.


@admin.register(NGOProfile)
class NGOProfileAdmin(admin.ModelAdmin):
    exclude = ('user',)  # Hide user field from the form
    list_display = ('organization_name', 'user', 'approved')
    list_filter = ('approved',)
    search_fields = ('organization_name', 'user__username')
    readonly_fields = ('license_document',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user  # Set user to current logged-in admin
        super().save_model(request, obj, form, change)