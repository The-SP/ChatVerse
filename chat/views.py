from django.shortcuts import render, redirect
from django.contrib import messages

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .models import Chat, Room

@login_required(login_url='login')
def home(request):
    rooms = Room.objects.all()
    if request.method == "POST":
        room_name = request.POST.get('name')
        room, created = Room.objects.get_or_create(name=room_name)
        if created:
            room.host = request.user
            room.save()
        return redirect('room', room.id)
    return render(request, 'home.html', {'rooms':rooms})


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
            return redirect('home')
        else:
            messages.warning(request, 'Username or password is incorrect!')
    return render(request, 'login.html')


# Anonymous is a user already created and anonymous login logs any user through this account
def anonymousLogin(request):
    user = authenticate(request, username="Anonymous", password="testing321")
    if user is not None:
        login(request, user)
        messages.success(request, f'Welcome Anonymous user')
    return redirect('home')

    
@login_required(login_url='login')
def logoutUser(request):
    messages.success(request, f'{request.user} logged out')
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def history(request):
    chats = Chat.objects.all().filter(user=request.user).order_by('-date')
    context = {'chats': chats}
    return render(request, 'history.html', context)


def room(request, pk):
    if request.method == "POST":
        message = request.POST.get('message')
        Chat.objects.create(
            user=request.user,
            room_id=pk,
            message=message
        )
        return redirect('room', pk)
    else:
        chats = Chat.objects.all().filter(room_id=pk)
        context = {'chats': chats, 'room':Room.objects.get(id=pk)}
        return render(request, 'room.html', context)


@login_required(login_url='login')
def delete(request, pk):
    message = Chat.objects.get(id=pk)
    message.delete()
    return redirect(request.META.get('HTTP_REFERER'))