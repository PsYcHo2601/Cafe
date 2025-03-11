from django.http import HttpResponse
from django.shortcuts import render
from datetime import date
def hello(request):
    return render(request, 'index.html', {
        'data':{'current_date': date.today()}
    })

# Create your views here.
