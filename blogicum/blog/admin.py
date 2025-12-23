from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Category, Location, Post, Comment

User = get_user_model()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('is_published',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('name',)
    list_editable = ('is_published',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'location', 'pub_date', 'is_published', 'created_at')
    list_filter = ('is_published', 'category', 'pub_date', 'author')
    search_fields = ('title', 'text', 'author__username')
    list_editable = ('is_published',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'pub_date'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'post', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('text', 'author__username', 'post__title')
    readonly_fields = ('created_at',)


# Отменяем регистрацию User, если она уже есть
if admin.site.is_registered(User):
    admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    pass
