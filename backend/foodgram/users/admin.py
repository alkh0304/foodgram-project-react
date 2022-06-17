from django.contrib import admin

from .models import CustomUser, Subscription


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'first_name', 'last_name', 'email',
                    'date_joined', 'subscribers_count')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    ordering = ('pk',)
    empty_value_display = '--empty--'

    def subscribers_count(self, obj):
        return obj.subscriber.all().count()


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
