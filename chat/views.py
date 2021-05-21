from django.shortcuts import render, redirect
from django.contrib import messages

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .forms import ChatForm
from .models import Chat

@login_required(login_url='login')
def index(request):
    return redirect('chat')


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            name = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {name}')
            return redirect('login')
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'register.html', context)


def loginUser(request):
    if request.method == "POST":
        name = request.POST['username']
        password = request.POST.get('password')
        user = authenticate(request, username=name, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome {name}')
            return redirect('chat')
        else:
            messages.warning(request, 'Username or password is incorrect!')
    return render(request, 'login.html')


# Anonymous is a user already created and anonymous login logs any user through this account
def anonymousLogin(request):
    user = authenticate(request, username="Anonymous", password="testing321")
    if user is not None:
        login(request, user)
        messages.success(request, f'Welcome Anonymous user')
    return redirect('chat')

    
@login_required(login_url='login')
def logoutUser(request):
    messages.success(request, f'{request.user} logged out')
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def chat(request):
    if request.method == "POST":
        form = ChatForm(request.POST)
        form.instance.user = request.user
        if form.is_valid:
            form.save()
            return redirect('chat')
    else:
        chats = Chat.objects.all()
        context = {'chats': chats}
        return render(request, 'chat.html', context)


@login_required(login_url='login')
def history(request):
    chats = Chat.objects.all().filter(user=request.user)
    context = {'chats': chats}
    return render(request, 'history.html', context)