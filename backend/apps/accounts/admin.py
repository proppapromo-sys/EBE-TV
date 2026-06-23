from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "display_name", "is_creator", "is_staff", "created_at")
    list_filter = ("is_creator", "is_staff")
    list_editable = ("is_creator",)
    search_fields = ("email", "display_name")
