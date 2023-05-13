from django.core.serializers import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
import json
import urllib.parse
import jwt
import datetime



# Create your views here.
def login_view(request):
    return render(request, "login.html", {})

def landing_page(request):

    return render(request, "index.html", {})

def sessional_login(request):
    redirect_url = '/my/new/page'
    return render(request, "sessionalLogin.html", {})

def validate_slogin(request):
    if request.method == 'POST':
        # Retrieve form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        data = []
        if username == 'abc' and password == 'abc':
            token = createToken()
            return render(request, 'sessional_dashboard.html', {'data': token})
        else:
            return render(request, "sessionalLogin.html", {})

def sessional_dashboard(request):
    data = []
    return render(request, 'sessional_dashboard.html', {'data' : data})


def sessional_registrationForm(request):

    data = [
        {'degree': 'Bachelors in Computer Science', 'code': '1'},
        {'degree': 'Masters in Computer Science', 'code': '2'}
    ]

    return render(request, 'sessional_registration.html', {'data': data})


def submit_form(request):
    if request.method == 'POST':
        # Retrieve form data
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        qualifications = request.POST.getlist('qualification')

        # You can redirect to a success page or render another template as needed
    return render(request, 'submit_success.html')


def about_view(request):
    redirect_url = '/my/new/page'
    return render(request, "about.html", {})


def permanent_login(request):
    print(request.headers)
    return render(request, "permanentLogin.html", {})


@require_POST
def entityRedirection(request):

    # Decode the request body to a string
    body_unicode = request.body.decode('utf-8')
    # Parse the data string into a dictionary
    data = urllib.parse.parse_qs(body_unicode)
    json_string = data['data'][0]
    json_data = json.loads(json_string)
    id = json_data["id"]

    #redirect the request to the sessional or permanent login page
    if(id == 'sessional'):
        redirect_url = "/sessional_login"
    else:
        redirect_url = "/permanent_login"

    return JsonResponse({'redirect': redirect_url})



def createToken():
    # Define the payload
    payload = {
        'user_id': '3',
        'username': 'hello',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expiration time
    }

    # Define the secret key (keep it secure)
    secret_key = 'your_secret_key'

    # Create the JWT token
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token
