# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, jsonify,render_template, request, redirect, url_for
import mysql.connector
from flask_cors import CORS
from flask import jsonify

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="appointment"
)
mycursor = db.cursor()
TEACHER_ID = ""
STUDENT_ID = ""


@app.route("/")
def root():
    return render_template('login.html', error='Invalid credentials')

@app.route("/tlogin")
def tlogin():
    return render_template('teacherlogin.html', error='Invalid credentials')

# Route for handling student login
@app.route('/login-student', methods=['POST'])
def login_student():
    username = request.form.get('username')
    password = request.form.get('password')
    # print(username,password)
    # type = request.form.get('student')
    query = f"SELECT * FROM students WHERE semail='{username}' AND spasword='{password}';"
    res = mycursor.execute(query)
    data = mycursor.fetchall()
    #print(data[0][0])
    try:
        if int(data[0][0])>0:
        # Redirect to the student dashboard upon successful login
            return redirect(url_for('dashboard_student'))
    except Exception as e:
        flash('Invalid credentials', 'error')
        return render_template('login.html', show_alert = True)


# Route for handling teacher login   
@app.route('/login-teacher', methods=['POST'])
def login_teacher():
    username = request.form.get('username')
    password = request.form.get('password')
    # print(username,password)
    
    # type = request.form.get('student')
    query = f"SELECT * FROM teachers WHERE temail='{username}' AND tpassword='{password}';"
    res = mycursor.execute(query)
    data = mycursor.fetchall()
    # print(data)
    
    try:
        if int(data[0][0])>0:
            id = str(data[0][0])
            # print(f'dashboard_teacher/{id}')
        # Redirect to the student dashboard upon successful login
            return redirect(url_for('dashboard_teacher',id=id))
    except Exception as e:
        flash('Invalid credentials', 'error')
        return render_template('teacherlogin.html', show_alert = True)
    
# Route for rendering the student dashboard
@app.route('/dashboard_student')
def dashboard_student():
    # Fetch available teachers from the database
    query = "SELECT teacher_id, tname FROM teachers;"
    mycursor.execute(query)
    available_teachers = mycursor.fetchall()
    
    # Fetch student name from the database
    student_id = request.form.get('sid')
    query_student_name = f"SELECT sname FROM students WHERE sid='{student_id}';"
    mycursor.execute(query_student_name)
    student_name = mycursor.fetchone()

    # Fetch teacher slots for the selected teacher
    selected_teacher_id = request.args.get('teacher_id')
    if selected_teacher_id:
        query_teacher_slots = f"SELECT free_time FROM free_slot JOIN teacher_free_slot ON free_slot.free_id = teacher_free_slot.free_id WHERE teacher_free_slot.teacher_id='{selected_teacher_id}';"
        mycursor.execute(query_teacher_slots)
        teacher_slots = mycursor.fetchall()
    else:
        teacher_slots = []  # If no teacher is selected, initialize an empty list
    
    # Pass the fetched data to the template
    return render_template('dashboard_student.html', student_name=student_name, available_teachers=available_teachers, teacher_slots=teacher_slots)


# Route for fetching free time slots for a specific teacher
@app.route('/get-teacher-free-slots/<teacher_id>')
def get_teacher_free_slots(teacher_id):
    # Query to fetch free time slots for the specified teacher
    query = f"SELECT free_time FROM free_slot JOIN teacher_free_slot ON free_slot.free_id = teacher_free_slot.free_id WHERE teacher_free_slot.teacher_id='{teacher_id}';"
    mycursor.execute(query)
    free_slots = mycursor.fetchall()

    # Extract the free time slots from the query result
    free_time_slots = [slot[0] for slot in free_slots]

    # Return the free time slots as a JSON response
    return jsonify({'teacher_id': teacher_id, 'free_time_slots': free_time_slots})




# Route for fetching teacher slots
@app.route('/get-teacher-slots/<teacher_id>')
def get_teacher_slots(teacher_id):
    query = f"SELECT free_date, free_time FROM free_slot JOIN teacher_free_slot ON free_slot.free_id = teacher_free_slot.free_id WHERE teacher_free_slot.teacher_id='{teacher_id}';"
    mycursor.execute(query)
    slots_data = mycursor.fetchall()
    
    # Fetch teacher's free slots
    query_teacher_slots = f"SELECT * FROM free_slot WHERE free_id IN (SELECT free_id FROM teacher_free_slot WHERE teacher_id='{teacher_id}');"
    mycursor.execute(query_teacher_slots)
    teacher_slots = mycursor.fetchall()

    # Fetch the teacher name
    query_teacher_name = f"SELECT teacher_name FROM teachers WHERE teacher_id='{teacher_id}';"
    mycursor.execute(query_teacher_name)
    teacher_name = mycursor.fetchone()[0]
    
    # Create HTML for teacher slots
    slots_html = ""
    for slot in teacher_slots:
        slots_html += f"<li>Date: {slot[1]}, Time: {slot[2]}</li>"

    # Prepare data to send to the client
    slots = [{'date': slot[0], 'time': slot[1]} for slot in slots_data]
    response_data = {'teacherName': teacher_name, 'slots': slots}

    return jsonify({'teacherName': teacher_name, 'slotsHTML': slots_html})

# Route for rendering the teacher dashboard
@app.route('/dashboard_teacher/<id>')
def dashboard_teacher(id):
    # print(id)
    global TEACHER_ID
    TEACHER_ID = id
    
    query = f"SELECT free_id FROM teacher_free_slot WHERE teacher_id='{id}';"
    res = mycursor.execute(query)
    fids = mycursor.fetchall()
    teacher_free_slots = []
    for fid in fids:
        inner_query = f"SELECT * FROM free_slot WHERE free_id='{fid[0]}';"
        res = mycursor.execute(inner_query)
        data = mycursor.fetchall()
        teacher_free_slots.append(data)
        # print(fid[0])
    # print(teacher_free_slots)
    for x in teacher_free_slots:
        print(x)
        
    # Fetch appointment requests for the teacher from the database
    query = f"SELECT * FROM appointment WHERE teacher_id='{id}';"
    mycursor.execute(query)
    appointment_requests = mycursor.fetchall()
        
         # Fetch teacher's free slots from the database
    query = f"SELECT * FROM teacher_free_slot WHERE teacher_id='{id}';"
    mycursor.execute(query)
    teacher_free_slots = mycursor.fetchall()
    
    return render_template('dashboard_teacher.html',teacher_free_slots=teacher_free_slots, appointment_requests=appointment_requests)





@app.route('/manage-slots',methods=['POST'])
def manage_slots():
    # print(TEACHER_ID)
    slotDate = request.form.get('slotDate')
    slotTime = request.form.get('slotTime')
    query = f"INSERT INTO free_slot(free_date,free_time) VALUES(%s,%s)"
    val = (slotDate,slotTime)
    res = mycursor.execute(query,val)
    fid = mycursor.lastrowid
    innerQuery = f"INSERT INTO teacher_free_slot(teacher_id,free_id) VALUES(%s,%s)"
    # print(slotDate,slotTime)
    innerval = (TEACHER_ID,fid)
    resinner = mycursor.execute(innerQuery,innerval)
    db.commit()
    return redirect(url_for('dashboard_teacher',id=TEACHER_ID))

# Fetch appointment requests status from the database
@app.route('/appointment-requests-status')
def appointment_requests_status():
    # Query to fetch appointment requests status
    query = "SELECT teacher_name, status FROM appointment_requests;"
    mycursor.execute(query)
    appointment_requests_status = mycursor.fetchall()
    
    # Pass the fetched data to the template
    return render_template('appointment_requests_status.html', appointment_requests_status=appointment_requests_status)


@app.route('/appointment-success')
def appointment_success():
    return render_template('appointment_success.html')

@app.route('/teachlogout')
def teachlogout():
    return render_template('dashboard_teacher.html')

@app.route('/slogout')
def studentlogout():
    return render_template('dashboard_student.html')


if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)
