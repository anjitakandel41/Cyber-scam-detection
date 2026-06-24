from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import ChatForm
from .models import ChatMessage
from .rules import hybrid_response


@login_required
def chatbot_home(request):
    form = ChatForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        message = form.cleaned_data['message']
        response = hybrid_response(message)
        ChatMessage.objects.create(user=request.user, message=message, response=response)
        form = ChatForm()

    conversations = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(
        request,
        'chatbot/home.html',
        {
            'form': form,
            'conversations': reversed(conversations),
        },
    )
