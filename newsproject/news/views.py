from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from .models import NewsPost, Comment, UserProfile, Chat, Message
from .forms import CustomUserCreationForm, NewsPostForm, CommentForm, UserProfileForm, UserUpdateForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'news/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

class NewsListView(ListView):
    model = NewsPost
    template_name = 'news/home.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_ordering(self):
        ordering = self.request.GET.get('sort', '-created_at')
        # Validate ordering to prevent injection
        allowed_fields = ['created_at', '-created_at', 'title', '-title', 
                         'author__username', '-author__username']
        if ordering not in allowed_fields:
            ordering = '-created_at'
        return ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        context['popular_authors'] = User.objects.annotate(
            post_count=Count('news_posts')
        ).order_by('-post_count')[:5]
        return context

class NewsDetailView(DetailView):
    model = NewsPost
    template_name = 'news/news_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        return context

class NewsCreateView(LoginRequiredMixin, CreateView):
    model = NewsPost
    form_class = NewsPostForm
    template_name = 'news/news_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class NewsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = NewsPost
    form_class = NewsPostForm
    template_name = 'news/news_form.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class NewsDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = NewsPost
    success_url = reverse_lazy('home')
    template_name = 'news/news_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

@login_required
def add_comment(request, pk):
    post = get_object_or_404(NewsPost, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
    return redirect('news_detail', pk=pk)

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = NewsPost.objects.filter(author=user).order_by('-created_at')
    post_count = posts.count()
    comment_count = Comment.objects.filter(author=user).count()
    
    context = {
        'profile_user': user,
        'user_posts': posts,
        'post_count': post_count,
        'comment_count': comment_count,
    }
    return render(request, 'news/user_profile.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.userprofile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_posts': NewsPost.objects.filter(author=request.user).order_by('-created_at'),
        'post_count': NewsPost.objects.filter(author=request.user).count(),
        'comment_count': Comment.objects.filter(author=request.user).count(),
    }
    return render(request, 'news/profile.html', context)

@login_required
def chat_list(request):
    # Get all chats for the current user with prefetched data
    chats = Chat.objects.filter(participants=request.user).prefetch_related(
        'participants',
        'participants__userprofile',
        'messages',
        'messages__sender'
    ).distinct()
    
    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id).select_related(
        'userprofile'
    ).order_by('username')
    
    context = {
        'chats': chats,
        'users': users,
    }
    return render(request, 'news/chat_list.html', context)

@login_required
def chat_detail(request, chat_id):
    # Get chat with prefetched data
    chat = get_object_or_404(
        Chat.objects.prefetch_related(
            'participants',
            'participants__userprofile',
            'messages',
            'messages__sender'
        ),
        id=chat_id
    )
    
    # Security check - ensure user is a participant
    if request.user not in chat.participants.all():
        messages.error(request, "You don't have permission to view this chat.")
        return redirect('chat_list')
    
    # Get the other participant
    other_user = chat.participants.exclude(id=request.user.id).first()
    
    # Mark unread messages from other user as read
    chat.messages.filter(sender=other_user, is_read=False).update(is_read=True)
    
    context = {
        'chat': chat,
        'messages': chat.messages.all().order_by('created_at'),
        'other_user': other_user,
    }
    return render(request, 'news/chat_detail.html', context)

@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # Check if chat already exists
    existing_chat = Chat.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if existing_chat:
        return redirect('chat_detail', chat_id=existing_chat.id)
    
    # Create new chat
    chat = Chat.objects.create()
    chat.participants.add(request.user, other_user)
    return redirect('chat_detail', chat_id=chat.id)

@login_required
def send_message(request, chat_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user not in chat.participants.all():
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        content = request.POST.get('content', '').strip()
        if content:
            message = Message.objects.create(
                chat=chat,
                sender=request.user,
                content=content
            )
            chat.save()  # Update the updated_at timestamp
            
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'created_at': message.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    'is_sender': True
                }
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_unread_count(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        unread_count = Message.objects.filter(
            chat__participants=request.user
        ).exclude(
            sender=request.user
        ).filter(
            is_read=False
        ).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'error': 'Invalid request'}, status=400)
