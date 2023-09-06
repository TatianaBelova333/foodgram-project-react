from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin

from users.models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'added_recipes_count',
    )
    list_filter = ('email', 'username')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    readonly_fields = ('last_login', 'date_joined')
    fieldsets = (
        (None, {'fields': (
            'username',
            'role',
            'email',
            'first_name',
            'last_name',
            'password',
            "is_active",
            'last_login',
            'date_joined',
        )}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
