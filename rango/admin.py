from django.contrib import admin
from rango.models import Category, Page, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'id']
    propopulated_fields = {'slug': ('name',)}


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'url']
    list_filter = ('category', )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'website']
