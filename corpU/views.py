
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


def mycourses(request, param1):

    decoded_token = jwt.decode(param1, 'Technical-Inquiry-Project-KEY', algorithms=['HS256'])
    user_id = decoded_token.get("user_id")

    query = "SELECT ps.Id " \
            "FROM `sessional staff` AS ps " \
            "WHERE ps.Person_Id = (SELECT Id FROM person WHERE EmailAddress = '{}')".format(user_id)

    Id = select(query)
    Id = Id[0][0]

    query = "SELECT sa.Id AS assign_Id, sa.day_Id AS day, sa.sessionalStaff_Id, sa.unit_Id, sa.start_date, sa.end_date, sa.status, u.Name AS unit_name, u.code, p.EmailAddress FROM `sessional_assign` sa JOIN unit u ON sa.unit_id = u.Id JOIN `sessional staff` ss ON sa.sessionalStaff_Id = ss.Id JOIN person p ON ss.Person_Id = p.Id JOIN day d ON sa.day_Id = d.Id WHERE sa.sessionalStaff_Id = {};".format(Id)
    data = fetch(query)

    days = {3: 'Monday', 4: 'Tuesday', 5: 'Wednesday', 6: 'Thursday', 7: 'Friday', 8: 'Saturday', 9: 'Sunday'}
    response = {
        "data" : data,
        "param1": param1
    }


    response['data'] = [
        {
            'Id': item.assign_Id,
            'day': item.day,
            'sessionalStaff_Id': item.sessionalStaff_Id,
            'unit_Id': item.unit_Id,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'status': item.status,
            'unit_name': item.unit_name,
            'code': item.code,
            'EmailAddress': item.EmailAddress,
        }
        for item in response['data']
    ]


    for item in response['data']:
        item['day'] = days[item['day']]



    return render(request, 'mycourses.html', {'response': response})


def sessional_dashboard(request, param1):

    decoded_token = jwt.decode(param1, 'Technical-Inquiry-Project-KEY', algorithms=['HS256'])
    user_id = decoded_token.get("user_id")

    query = "SELECT ps.Id " \
            "FROM `sessional staff` AS ps " \
            "WHERE ps.Person_Id = (SELECT Id FROM person WHERE EmailAddress = '{}')".format(user_id)

    Id = select(query)
    Id = Id[0][0]


    query = "SELECT * FROM `sessional qualification`"
    sessional_qualification = fetch(query)

    s_qualification_id_set = {row.qualification_Id for row in sessional_qualification if row.sessionalStaff_Id == Id}
    s_qualification_id = s_qualification_id_set.pop() if s_qualification_id_set else None

    query = "select * from day"
    days = fetch(query)


    query = "select * from unit"
    units = fetch(query)
    filtered_units = [row for row in units if row.qualification_id == s_qualification_id]

    data = {
        "units": units,
        "filtered_units": filtered_units,
        "sessional_Id": Id,
        "user_id": user_id,
        "param1": param1,
        "days": days
    }

    data['units'] = [
        {
            'Id': item.Id,
            'Name': item.Name,
            'code': item.code,
            'permanent_staff_id': item.permanent_staff_id,
            'qualification_id': item.qualification_id
        }
        for item in data['units']
    ]

    # Convert 'filtered_units' list
    data['filtered_units'] = [
        {
            'Id': item.Id,
            'Name': item.Name,
            'code': item.code,
            'permanent_staff_id': item.permanent_staff_id,
            'qualification_id': item.qualification_id
        }
        for item in data['filtered_units']
    ]

    data['days'] = [
        {
            'Id': item.Id,
            'Name': item.Name
        }
        for item in data['days']
    ]
    data_json = json.dumps(data)

    return render(request, 'sessional_dashboard.html', {'data': data_json})

def sessional_assignment(request):
    if request.method == 'POST' and request.is_ajax():
        unit_id = request.POST.get('unit_id');
        day_id = request.POST.get('day');
        id = request.POST.get('data');
        timings = request.POST.get('timings');

        timeParts = timings.split(' - ');
        start = timeParts[0];
        end = timeParts[1];

        days_dict = {
            "Monday": 3,
            "Tuesday": 4,
            "Wednesday": 5,
            "Thursday": 6,
            "Friday": 7,
            "Saturday": 8,
            "Sunday": 9
        }

        day_id = days_dict[day_id];


        print(days_dict)

        query = "INSERT INTO `sessional_assign` (day_id, SessionalStaff_Id, unit_id, start_date, end_date) VALUES ({}, {}, {}, '{}', '{}');".format(
             day_id, id, unit_id, start, end)

        execute_query(query)
        response = {
            'message': 'Course added successfully!'
        }
        return JsonResponse(response)


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
        'qualifications': qualification,
        'courses': allUnits,
        'myCourses': result,
        'token': param1,
        'username': user_id,
        'param1': param1
    }

    data['courses'] = [
        {
            'Name': item.Name,
            'code': item.code,
            'Id': item.Id,
            'permanent_staff_id':  item.permanent_staff_id,
            'qualification_id': item.qualification_id
        }
        for item in data['courses']
    ]

    data['qualifications'] = [
        {
            'Id': item.Id,
            'Name': item.Name,

        }
        for item in data['qualifications']
    ]
    return render(request, 'pdashboard.html', {'data': data})


def course_timetable(request, param1):

    query = "SELECT sa.Id as assign_Id, sa.day_Id as day, sa.sessionalStaff_Id, sa.unit_Id, sa.start_date, sa.end_date, sa.status, u.Name as unit_name, u.code, p.EmailAddress FROM `sessional_assign` sa JOIN unit u ON sa.unit_id = u.Id JOIN `sessional staff` ss ON sa.sessionalStaff_Id = ss.Id JOIN person p ON ss.Person_Id = p.Id; JOIN day d ON sa.day_Id = d.Id;"
    data = fetch(query)

    days = {3: 'Monday', 4: 'Tuesday', 5: 'Wednesday', 6: 'Thursday', 7: 'Friday', 8: 'Saturday', 9: 'Sunday'}
    response = {
        "data" : data,
        "param1": param1
    }


    response['data'] = [
        {
            'Id': item.assign_Id,
            'day': item.day,
            'sessionalStaff_Id': item.sessionalStaff_Id,
            'unit_Id': item.unit_Id,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'status': item.status,
            'unit_name': item.unit_name,
            'code': item.code,
            'EmailAddress': item.EmailAddress
        }
        for item in response['data']
    ]


    for item in response['data']:
        item['day'] = days[item['day']]

    old = response['data'].copy()

    dup = []
    new_data = []
    for item in response['data']:
        if item['unit_Id'] in dup:
            continue  # Skip adding this item to the new data
        else:
            dup.append(item['unit_Id'])
            new_data.append(item)

    response['data'] = new_data

    #
    # query = "SELECT * FROM `sessional_assign`"
    # reg = fetch(query)
    #
    # reg = [
    #     {
    #         'time_In': item['start_date'],
    #         'registration_Id': item['Id'],
    #         'sessional_Id': item['sessionalStaff_Id'],
    #         'day': item['day'],
    #         'unit_id': item['unit_Id']
    #     }
    #     for item in response
    # ]


    reg = response['data'];

    sessional_lists = {}
    day_lists = {}

    list = []
    for item in reg:
        sessional_id = item['day']
        if sessional_id not in sessional_lists:
            sessional_lists[sessional_id] = []
        sessional_lists[sessional_id].append(item)

    dict = {}
    final = {}
    # Accessing lists for each distinct sessional_Id
    for sessional_id, sessional_list in sessional_lists.items():
        dict[sessional_id] = (process_dicts(sessional_list))

    for key, value in dict.items():
        unique_ids = []
        for item in value:
            registration_id = item['unit_Id']
            if registration_id not in unique_ids:
                unique_ids.append(registration_id)
        final[key] = [item for item in value if item['unit_Id'] in unique_ids]

    #for key, list in dict.items():

    response['timetable'] = final;
    response['data'] = old

    asv = "asd";
    return render(request, "permanent-teacher.html", {'response': response})


def approve(request):
    if request.method == 'POST' and request.is_ajax():
        assignId = request.POST.get('data');

    query = "UPDATE sessional_assign SET status = 'Approved' WHERE Id = '{}';".format(assignId);
    execute_query(query)

    response = {
        'message': 'Course added successfully!'
    }

    return JsonResponse(response)


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



def process_dicts(dicts):
    time_in_list = []
    clash = []
    response = []

    for d in dicts:
        time_in = d.get('start_date', '')
        if ':' in time_in:
            time_in_hours = time_in.split(':')[0]
            if time_in_hours not in clash:
                clash.append(time_in_hours)
                response.append(d)

    return response
