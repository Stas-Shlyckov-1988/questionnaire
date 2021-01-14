"""
Definition of views.
"""

import json
from django.http import HttpResponse
from django.core import serializers
from django.db import connection
from os import path
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView, DetailView
from app.models import Choice, Poll


class PollListView(ListView):
    """Renders the home page, with a list of all polls."""
    model = Poll

    def get_context_data(self, **kwargs):
        context = super(PollListView, self).get_context_data(**kwargs)
        context['title'] = 'Опросить'
        context['year'] = datetime.now().year
        return context

class PollDetailView(DetailView):
    """Renders the poll details page."""
    model = Poll

    def get_context_data(self, **kwargs):
        context = super(PollDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Опрос'
        context['btn'] = 'Опросить'
        context['year'] = datetime.now().year
        return context

class PollResultsView(DetailView):
    """Renders the results page."""
    model = Poll

    def get_context_data(self, **kwargs):
        context = super(PollResultsView, self).get_context_data(**kwargs)
        context['title'] = 'Результат'
        context['btn'] = 'Повторить'
        context['year'] = datetime.now().year
        return context

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Контакты',
            'message':'Ваши контакты.',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'О нас',
            'message':'Ваше приложение с описанием страницы.',
            'year':datetime.now().year,
        }
    )

def questions(request, poll_id = None):
    assert isinstance(request, HttpRequest)

    if poll_id is None:
        poll = Choice.objects.all().select_related('poll')
        poll = serializers.serialize('json', poll)
    else:
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM app_poll WHERE id = %s", [poll_id])
            for row in cursor.fetchall():
                poll = {"id": row[0], "text": row[1], "publication": row[2].isoformat(timespec='microseconds')}

        choice = []
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM app_choice WHERE poll_id = %s", [poll_id])
            for row in cursor.fetchall():
                choice.append({"id": row[0], "text": row[1], "voite": row[2]})

        poll = json.dumps([poll, choice])

    return HttpResponse(poll, content_type='json')

def vote(request, poll_id):
    """Handles voting. Validates input and updates the repository."""
    poll = get_object_or_404(Poll, pk=poll_id)
    try:
        selected_choice = poll.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'app/details.html', {
            'title': 'Poll',
            'year': datetime.now().year,
            'poll': poll,
            'error_message': "Please make a selection.",
    })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return HttpResponseRedirect(reverse('app:results', args=(poll.id,)))

@login_required
def seed(request):
    """Seeds the database with sample polls."""
    samples_path = path.join(path.dirname(__file__), 'samples.json')
    with open(samples_path, 'r') as samples_file:
        samples_polls = json.load(samples_file)

    for sample_poll in samples_polls:
        poll = Poll()
        poll.text = sample_poll['text']
        poll.pub_date = timezone.now()
        poll.save()

        for sample_choice in sample_poll['choices']:
            choice = Choice()
            choice.poll = poll
            choice.text = sample_choice
            choice.votes = 0
            choice.save()

    return HttpResponseRedirect(reverse('app:home'))
