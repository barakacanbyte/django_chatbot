from django.shortcuts import render, redirect
from django.http import JsonResponse
from openai import OpenAI
import os
from django.contrib import auth
from .models import Chat
from django.utils import timezone

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"

client = OpenAI(
    base_url= endpoint,
    api_key=token,
)

def ask_openai(message):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ],
        top_p=1.0,
        max_tokens=150,
        temperature=0.7,
    )

    answer = response.choices[0].message.content.strip()
    return answer


def chatbot(request):
    chats = Chat.objects.filter(user=request.user)
    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)

        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()

        return JsonResponse({'message':message, 'response': response})
    return render(request, 'chatbot.html', {'chats': chats})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Debug: Check if user exists in DB
        print("Users in DB:", auth.models.User.objects.filter(username=username).exists())
        
        user = auth.authenticate(request, username=username, password=password)
        print("Auth result:", user)  # Should show user object or None

        if user is not None:
            auth.login(request, user)  # Use renamed import to avoid conflict
            return redirect('chatbot')
        else:
            # More detailed error messages
            if not auth.models.User.objects.filter(username=username).exists():
                error_message = "Username does not exist"
            else:
                error_message = "Incorrect password"
            return render(request, 'login.html', {'error_message': error_message})
    
    return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')

        if password1 == password2:
            try:
                user = auth.models.User.objects.create_user(username=username, password=password1, email=email)
                user.save()
                print("User created:", user)  # Debug: Check if user is created
                auth.login(request, user)

                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
        else:
            error_message = "Passwords do not match."
            return render(request, 'register.html', {'error_message': error_message})
    else:
        return render(request, 'register.html')