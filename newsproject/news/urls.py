from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.NewsListView.as_view(), name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='news/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    
    # Password reset URLs
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='news/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='news/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='news/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='news/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # News post URLs
    path('post/new/', views.NewsCreateView.as_view(), name='news_create'),
    path('post/<int:pk>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('post/<int:pk>/update/', views.NewsUpdateView.as_view(), name='news_update'),
    path('post/<int:pk>/delete/', views.NewsDeleteView.as_view(), name='news_delete'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),

    # Chat URLs
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chats/start/<str:username>/', views.start_chat, name='start_chat'),
    path('chats/<int:chat_id>/send/', views.send_message, name='send_message'),
    path('chats/unread/', views.get_unread_count, name='get_unread_count'),
] 