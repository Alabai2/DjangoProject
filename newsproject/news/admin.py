from django.contrib import admin
from .models import UserProfile, NewsPost, Comment

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio']
    search_fields = ['user__username', 'bio']

@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'author']
    search_fields = ['title', 'content', 'author__username']
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username', 'post__title']
