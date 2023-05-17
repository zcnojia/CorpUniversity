from django.core.serializers import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
import json
import urllib.parse
import jwt
import datetime
from django.db import connection
from collections import namedtuple
import random

import mysql.connector
from django.conf import settings
from django.shortcuts import redirect


def sessional_dashboard(request, param1):
    decoded_token = jwt.decode(param1, 'Technical-Inquiry-Project-KEY', algorithms=['HS256'])
    user_id = decoded_token.get("user_id")

    query = "SELECT * FROM unit AS u JOIN `permanent staff` AS ps ON u.permanent_staff_id = ps.Id JOIN qualification AS q ON u.qualification_id = q.Id JOIN person AS p ON ps.Person_Idl = p.Id"
    result = fetch(query)
    return render(request, 'pdashboard.html', {'data': result})


def permanent_dashboard(request, param1):

    query = "select * from unit;"
    allUnits = fetch(query)
    asb = param1
    decoded_token = get_user_id_from_token(param1)
    decoded_token = jwt.decode(param1, 'Technical-Inquiry-Project-KEY', algorithms=['HS256'])
    user_id = decoded_token.get("user_id")

    query = "SELECT ps.Id " \
            "FROM `permanent staff` AS ps " \
            "WHERE ps.Person_Idl = (SELECT Id FROM person WHERE EmailAddress = '{}')".format(user_id)

    Id = select(query)
    Id = Id[0][0]

    result = [item for item in allUnits if item.permanent_staff_id == Id]

    query = "Select Id, Name from qualification"
    qualification = fetch(query)

    data = {
        'qualifications' : qualification,
        'courses': allUnits,
        'myCourses': result,
        'token': param1,
        'username': user_id
    }



    return render(request, 'pdashboard.html', {'data': data})

def add_course(request):
    if request.method == 'POST' and request.is_ajax():
        course_name = request.POST.get('courseName')
        course_code = request.POST.get('courseCode')
        username = request.POST.get('username')
        qualification = request.POST.get('qualification')

        # Perform the necessary operations to add the course
        # Use the provided course_name, course_code, and username variables
        query = "SELECT ps.Id " \
                "FROM `permanent staff` AS ps " \
                "WHERE ps.Person_Idl = (SELECT Id FROM person WHERE EmailAddress = '{}')".format(username)

        Id = select(query)
        Id = Id[0][0]

        query = "INSERT INTO unit (Name, code, permanent_staff_id, qualification_id) VALUES ('{}', '{}', {}, {})".format(
            course_name, course_code, Id, qualification)
        execute_query(query)
        # Assuming the course is successfully added, return a success response
        response = {
            'message': 'Course added successfully!'
        }
        return JsonResponse(response)

    # If the request method is not POST or it's not an AJAX request, return an error response
    response = {
        'error': 'Invalid request'
    }
    return JsonResponse(response, status=400)

# Create your views here.
def login_view(request):
    return render(request, "login.html", {})

def landing_page(request):
    return render(request, "index.html", {})

def sessional_login(request):
    return render(request, "sessionalLogin.html", {})

def validate_slogin(request):
    if request.method == 'POST':
        # Retrieve form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        query = "SELECT username, password FROM sessional_login WHERE username = '{}' AND password = '{}'".format(
            username, password)
        result = select(query)

        if len(result) > 0:
            token = createToken(username, password, "sessional staff")
            return redirect('sessional_dashboard', param1=token)
        else:
            return redirect('sessional_login')






def sessional_registrationForm(request):


    query = "select Id, Name from qualification;"
    data = fetch(query)
    return render(request, 'sessional_registration.html', {'data': data})


def submit_form(request):
    if request.method == 'POST':
        # Retrieve form data
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        phone = request.POST.get('contact')
        email = request.POST.get('email')
        age = request.POST.get('age')
        password = request.POST.get('password')
        gender = request.POST.get('gender')
        qualifications = request.POST.getlist('qualification')

        Id = random.randint(11, 9999)
        query = "INSERT INTO person (Id, `First Name`, `Last Name`, `Phone Number`, `EmailAddress`, `gender`, `age`) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}');"
        formatted_query = query.format(Id, fname, lname, phone, email, gender, age)
        query = formatted_query
        Personid = execute_query(query)

        query = "INSERT INTO `sessional staff` (`Person_Id`) VALUES ('" + str(Id) + "');"
        sessionalId = insert_person_details(query)
        #sessionalId = insert_person_details("SELECT LAST_INSERT_ID();")

        query = "insert into `sessional qualification` (sessionalStaff_Id, qualification_Id) VALUES ('{}', '{}');"
        formatted_query = query.format(sessionalId, qualifications[0])
        insert_person_details(formatted_query)

        query = "INSERT INTO sessional_login (username, password, status, sessional_staff_Id) VALUES ('{}', '{}', '{}', {});".format(email, password, '1', sessionalId)
        execute_query(query)

        return redirect('sessional_login')


def about_view(request):
    redirect_url = '/my/new/page'
    return render(request, "about.html", {})


def permanent_login(request):
    return render(request, "permanentLogin.html", {})

def validate_plogin(request):
    if request.method == 'POST':
        # Retrieve form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        query = "SELECT username, password FROM permanent_login WHERE username = '{}' AND password = '{}'".format(username, password)
        result = select(query)

        if len(result) > 0:
            token = createToken(username, password, "permanent staff")
            return redirect('permanent_dashboard', param1=token)
        else:
            return render(request, 'permanentLogin.html')

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



def createToken(email, password, status):
    # Define the payload
    payload = {
        'user_id': email,
        'username': password,
        'group': status,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expiration time
    }

    # Define the secret key (keep it secure)
    secret_key = 'Technical-Inquiry-Project-KEY'

    # Create the JWT token
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def get_user_id_from_token(token):
    try:
        # Decode the JWT token
        decoded_token = jwt.decode(token, algorithms=["HS256"])

        # Retrieve the user_id from the decoded payload


        return decoded_token
    except jwt.exceptions.DecodeError:
        # Handle any decoding errors
        return None


def select(query):
    # Access database information from settings
    database_user = settings.DATABASES['default']['USER']
    database_password = settings.DATABASES['default']['PASSWORD']
    database_host = settings.DATABASES['default']['HOST']
    database_port = settings.DATABASES['default']['PORT']
    database_name = settings.DATABASES['default']['NAME']

    # Construct the connection string
    connection_string = f"mysql+mysqlconnector://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"

    # Establish the database connection
    conn = mysql.connector.connect(
        host=database_host,
        user=database_user,
        password=database_password,
        port=database_port,
        database=database_name
    )

    # Create a cursor to execute SQL queries
    cursor = conn.cursor()

    # Retrieve data from the view
    cursor.execute(query)
    result = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return result


def fetch(query):
    # Access database information from settings
    database_user = settings.DATABASES['default']['USER']
    database_password = settings.DATABASES['default']['PASSWORD']
    database_host = settings.DATABASES['default']['HOST']
    database_port = settings.DATABASES['default']['PORT']
    database_name = settings.DATABASES['default']['NAME']

    # Construct the connection string
    connection_string = f"mysql+mysqlconnector://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"

    # Establish the database connection
    conn = mysql.connector.connect(
        host=database_host,
        user=database_user,
        password=database_password,
        port=database_port,
        database=database_name
    )

    # Create a cursor to execute SQL queries
    cursor = conn.cursor()

    # Retrieve data from the view
    cursor.execute(query)

    # Retrieve the results and fetch column names
    columns = [column[0] for column in cursor.description]
    ResultRow = namedtuple('ResultRow', columns)

    # Fetch all rows and map to named tuples
    rows = cursor.fetchall()
    results = [ResultRow(*row) for row in rows]
    return results

def insert_person_details(query):
    # ... Previous code to retrieve values for fname, lname, phone, email, gender, and age ...
    # Access database information from settings
    database_user = settings.DATABASES['default']['USER']
    database_password = settings.DATABASES['default']['PASSWORD']
    database_host = settings.DATABASES['default']['HOST']
    database_port = settings.DATABASES['default']['PORT']
    database_name = settings.DATABASES['default']['NAME']

    # Construct the connection string
    connection_string = f"mysql+mysqlconnector://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"

    # Establish the database connection
    conn = mysql.connector.connect(
        host=database_host,
        user=database_user,
        password=database_password,
        port=database_port,
        database=database_name
    )

    # Create a cursor to execute SQL queries
    cursor = conn.cursor()

    with connection.cursor() as cursor:
        cursor.execute(query)
        inserted_id = cursor.lastrowid

    return inserted_id;


def execute_query(query):
    try:
        # ... Previous code to retrieve values for fname, lname, phone, email, gender, and age ...
        # Access database information from settings
        database_user = settings.DATABASES['default']['USER']
        database_password = settings.DATABASES['default']['PASSWORD']
        database_host = settings.DATABASES['default']['HOST']
        database_port = settings.DATABASES['default']['PORT']
        database_name = settings.DATABASES['default']['NAME']

        # Construct the connection string
        connection_string = f"mysql+mysqlconnector://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"

        # Establish the database connection
        conn = mysql.connector.connect(
            host=database_host,
            user=database_user,
            password=database_password,
            port=database_port,
            database=database_name
        )

        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        print("Query executed successfully!")
    except mysql.connector.Error as error:
        print("Error executing query:", error)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




