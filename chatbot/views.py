from django.shortcuts import render

from users.decorators import view_mode_allowed
from users.remember import get_display_user

from .forms import ChatForm
from .models import ChatMessage
from .rules import hybrid_response


@view_mode_allowed
def chatbot_home(request):
    """Awareness chatbot.

    Remembered (view-mode) visitors may read their past conversation, but the
    decorator rejects POST, so no new message can be stored without a session.
    """
    display_user = get_display_user(request)
    form = ChatForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        message = form.cleaned_data['message']
        response = hybrid_response(message)
        ChatMessage.objects.create(user=request.user, message=message, response=response)
        form = ChatForm()

    conversations = ChatMessage.objects.filter(user=display_user).order_by('-created_at')[:10]
    return render(
        request,
        'chatbot/home.html',
        {
            'form': form,
            'conversations': reversed(conversations),
        },
    )
