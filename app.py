from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db_connection, init_db
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'replace_this_with_a_secure_secret'

database_initialized = False

@app.before_request
def setup_database():
    global database_initialized
    if not database_initialized:
        init_db()
        database_initialized = True


def parse_int(value):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    totals = {
        'total_candidates': 0,
        'total_applications': 0,
        'total_interviews': 0,
        'total_employees': 0,
        'total_training': 0,
    }
    error = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT COUNT(*) AS total FROM candidates')
        totals['total_candidates'] = cursor.fetchone()['total'] or 0
        cursor.execute('SELECT COUNT(*) AS total FROM applications')
        totals['total_applications'] = cursor.fetchone()['total'] or 0
        cursor.execute('SELECT COUNT(*) AS total FROM interviews')
        totals['total_interviews'] = cursor.fetchone()['total'] or 0
        cursor.execute('SELECT COUNT(*) AS total FROM employees')
        totals['total_employees'] = cursor.fetchone()['total'] or 0
        cursor.execute('SELECT COUNT(*) AS total FROM employee_training')
        totals['total_training'] = cursor.fetchone()['total'] or 0
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('dashboard.html', totals=totals, error=error)

@app.route('/candidates')
def candidates():
    candidates = []
    error = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT Candidate_ID AS id, Full_Name AS full_name, Email AS email, Phone_Number AS phone FROM candidates ORDER BY Full_Name')
        candidates = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('candidates.html', candidates=candidates, candidate=None, error=error)

@app.route('/candidates/add', methods=['POST'])
def add_candidate():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO candidates (Full_Name, Email, Phone_Number) VALUES (%s, %s, %s)',
            (full_name, email, phone)
        )
        conn.commit()
        flash('Candidate added successfully.')
    except Error as err:
        flash(f'Error adding candidate: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('candidates'))

@app.route('/candidates/edit/<int:candidate_id>', methods=['GET', 'POST'])
def edit_candidate(candidate_id):
    conn = None
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE candidates SET Full_Name = %s, Email = %s, Phone_Number = %s WHERE Candidate_ID = %s',
                (full_name, email, phone, candidate_id)
            )
            conn.commit()
            flash('Candidate updated successfully.')
            return redirect(url_for('candidates'))
        except Error as err:
            flash(f'Error updating candidate: {err}')
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
    candidate = None
    candidates = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT Candidate_ID AS id, Full_Name AS full_name, Email AS email, Phone_Number AS phone FROM candidates WHERE Candidate_ID = %s', (candidate_id,))
        candidate = cursor.fetchone()
        if candidate is None:
            flash('Candidate not found.')
            return redirect(url_for('candidates'))
        cursor.execute('SELECT Candidate_ID AS id, Full_Name AS full_name, Email AS email, Phone_Number AS phone FROM candidates ORDER BY Full_Name')
        candidates = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('candidates.html', candidates=candidates, candidate=candidate, error=error)

@app.route('/candidates/delete/<int:candidate_id>')
def delete_candidate(candidate_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM candidates WHERE Candidate_ID = %s', (candidate_id,))
        conn.commit()
        flash('Candidate deleted successfully.')
    except Error as err:
        flash(f'Error deleting candidate: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('candidates'))

@app.route('/applications')
def applications():
    applications = []
    candidates = []
    job_postings = []
    error = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT a.Application_ID AS id, a.Candidate_ID AS candidate_id, a.Job_ID AS job_posting_id, a.Application_Date AS application_date, a.Final_Status AS status, '
            'COALESCE(c.Full_Name, "Not Available") AS candidate_name, '
            'COALESCE(jp.Job_Title, "Not Available") AS job_title '
            'FROM applications a '
            'LEFT JOIN candidates c ON a.Candidate_ID = c.Candidate_ID '
            'LEFT JOIN job_postings jp ON a.Job_ID = jp.Job_ID '
            'ORDER BY a.Application_ID DESC'
        )
        applications = cursor.fetchall()
        cursor.execute('SELECT Candidate_ID AS id, Full_Name FROM candidates ORDER BY Full_Name')
        candidates = cursor.fetchall()
        cursor.execute('SELECT Job_ID AS id, Job_Title AS title FROM job_postings ORDER BY title')
        job_postings = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('applications.html', applications=applications, candidates=candidates, job_postings=job_postings, application=None, error=error)

@app.route('/applications/add', methods=['POST'])
def add_application():
    candidate_id = parse_int(request.form.get('candidate_id'))
    job_posting_id = parse_int(request.form.get('job_posting_id'))
    application_date = request.form.get('application_date', '').strip() or None
    status = request.form.get('status', '').strip()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO applications (Candidate_ID, Job_ID, Application_Date, Final_Status) VALUES (%s, %s, %s, %s)',
            (candidate_id, job_posting_id, application_date, status)
        )
        conn.commit()
        flash('Application added successfully.')
    except Error as err:
        flash(f'Error adding application: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('applications'))

@app.route('/applications/edit/<int:application_id>', methods=['GET', 'POST'])
def edit_application(application_id):
    conn = None
    if request.method == 'POST':
        candidate_id = parse_int(request.form.get('candidate_id'))
        job_posting_id = parse_int(request.form.get('job_posting_id'))
        application_date = request.form.get('application_date', '').strip() or None
        status = request.form.get('status', '').strip()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE applications SET Candidate_ID = %s, Job_ID = %s, Application_Date = %s, Final_Status = %s WHERE Application_ID = %s',
                (candidate_id, job_posting_id, application_date, status, application_id)
            )
            conn.commit()
            flash('Application updated successfully.')
            return redirect(url_for('applications'))
        except Error as err:
            flash(f'Error updating application: {err}')
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
    application = None
    applications = []
    candidates = []
    job_postings = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT Application_ID AS id, Candidate_ID AS candidate_id, Job_ID AS job_posting_id, Application_Date AS application_date, Final_Status AS status FROM applications WHERE Application_ID = %s', (application_id,))
        application = cursor.fetchone()
        if application is None:
            flash('Application not found.')
            return redirect(url_for('applications'))
        cursor.execute(
            'SELECT a.Application_ID AS id, a.Candidate_ID AS candidate_id, a.Job_ID AS job_posting_id, a.Application_Date AS application_date, a.Final_Status AS status, '
            'COALESCE(c.Full_Name, "Not Available") AS candidate_name, '
            'COALESCE(jp.Job_Title, "Not Available") AS job_title '
            'FROM applications a '
            'LEFT JOIN candidates c ON a.Candidate_ID = c.Candidate_ID '
            'LEFT JOIN job_postings jp ON a.Job_ID = jp.Job_ID '
            'ORDER BY a.Application_ID DESC'
        )
        applications = cursor.fetchall()
        cursor.execute('SELECT Candidate_ID AS id, Full_Name FROM candidates ORDER BY Full_Name')
        candidates = cursor.fetchall()
        cursor.execute('SELECT Job_ID AS id, Job_Title AS title FROM job_postings ORDER BY title')
        job_postings = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('applications.html', applications=applications, candidates=candidates, job_postings=job_postings, application=application, error=error)

@app.route('/applications/delete/<int:application_id>')
def delete_application(application_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM applications WHERE Application_ID = %s', (application_id,))
        conn.commit()
        flash('Application deleted successfully.')
    except Error as err:
        flash(f'Error deleting application: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('applications'))

@app.route('/interviews')
def interviews():
    interviews = []
    applications = []
    error = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT i.Interview_ID AS id, i.Application_ID AS application_id, i.Interview_Date AS interview_date, '
            'i.Interviewer AS interviewer, i.Status AS interview_status, '
            'COALESCE(c.Full_Name, "Not Available") AS candidate_name, '
            'COALESCE(jp.Job_Title, "Not Available") AS job_title '
            'FROM interviews i '
            'LEFT JOIN applications a ON i.Application_ID = a.Application_ID '
            'LEFT JOIN candidates c ON a.Candidate_ID = c.Candidate_ID '
            'LEFT JOIN job_postings jp ON a.Job_ID = jp.Job_ID '
            'ORDER BY i.Interview_ID DESC'
        )
        interviews = cursor.fetchall()
        cursor.execute(
            'SELECT a.Application_ID AS id, COALESCE(c.Full_Name, "Not Available") AS candidate_name, '
            'COALESCE(jp.Job_Title, "Not Available") AS job_title '
            'FROM applications a '
            'LEFT JOIN candidates c ON a.Candidate_ID = c.Candidate_ID '
            'LEFT JOIN job_postings jp ON a.Job_ID = jp.Job_ID '
            'ORDER BY a.Application_ID DESC'
        )
        applications = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('interviews.html', interviews=interviews, applications=applications, interview=None, error=error)

@app.route('/interviews/add', methods=['POST'])
def add_interview():
    application_id = parse_int(request.form.get('application_id'))
    interview_date = request.form.get('interview_date', '').strip() or None
    interviewer = request.form.get('interviewer', '').strip()
    interview_status = request.form.get('interview_status', '').strip()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO interviews (Application_ID, Interview_Date, Interviewer, Status) VALUES (%s, %s, %s, %s)',
            (application_id, interview_date, interviewer, interview_status)
        )
        conn.commit()
        flash('Interview added successfully.')
    except Error as err:
        flash(f'Error adding interview: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('interviews'))

@app.route('/interviews/edit/<int:interview_id>', methods=['GET', 'POST'])
def edit_interview(interview_id):
    conn = None
    if request.method == 'POST':
        application_id = parse_int(request.form.get('application_id'))
        interview_date = request.form.get('interview_date', '').strip() or None
        interviewer = request.form.get('interviewer', '').strip()
        interview_status = request.form.get('interview_status', '').strip()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE interviews SET Application_ID = %s, Interview_Date = %s, Interviewer = %s, Status = %s WHERE Interview_ID = %s',
                (application_id, interview_date, interviewer, interview_status, interview_id)
            )
            conn.commit()
            flash('Interview updated successfully.')
            return redirect(url_for('interviews'))
        except Error as err:
            flash(f'Error updating interview: {err}')
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
    interview = None
    interviews = []
    applications = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT Interview_ID AS id, Application_ID AS application_id, Interview_Date AS interview_date, Interviewer AS interviewer, Status AS interview_status FROM interviews WHERE Interview_ID = %s', (interview_id,))
        interview = cursor.fetchone()
        if interview is None:
            flash('Interview not found.')
            return redirect(url_for('interviews'))
        cursor.execute(
            'SELECT i.Interview_ID AS id, i.Application_ID AS application_id, i.Interview_Date AS interview_date, '
            'i.Interviewer AS interviewer, i.Status AS interview_status, '
            'COALESCE(c.Full_Name, "Not Available") AS candidate_name, '
            'COALESCE(jp.Job_Title, "Not Available") AS job_title '
            'FROM interviews i '
            'LEFT JOIN applications a ON i.Application_ID = a.Application_ID '
            'LEFT JOIN candidates c ON a.Candidate_ID = c.Candidate_ID '
            'LEFT JOIN job_postings jp ON a.Job_ID = jp.Job_ID '
            'ORDER BY i.Interview_ID DESC'
        )
        interviews = cursor.fetchall()
        cursor.execute(
            'SELECT a.Application_ID AS id, COALESCE(c.Full_Name, "Not Available") AS candidate_name, '
            'COALESCE(jp.Job_Title, "Not Available") AS job_title '
            'FROM applications a '
            'LEFT JOIN candidates c ON a.Candidate_ID = c.Candidate_ID '
            'LEFT JOIN job_postings jp ON a.Job_ID = jp.Job_ID '
            'ORDER BY a.Application_ID DESC'
        )
        applications = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('interviews.html', interviews=interviews, applications=applications, interview=interview, error=error)

@app.route('/interviews/delete/<int:interview_id>')
def delete_interview(interview_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM interviews WHERE Interview_ID = %s', (interview_id,))
        conn.commit()
        flash('Interview deleted successfully.')
    except Error as err:
        flash(f'Error deleting interview: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('interviews'))

@app.route('/employees')
def employees():
    employees = []
    departments = []
    error = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT e.Employee_ID AS id, e.Full_Name AS full_name, e.Email AS email, e.Hiring_Date AS hire_date, e.Department_ID AS department_id, '
            'COALESCE(d.Department_Name, "") AS department_name '
            'FROM employees e '
            'LEFT JOIN departments d ON e.Department_ID = d.Department_ID '
            'ORDER BY e.Employee_ID DESC'
        )
        employees = cursor.fetchall()
        cursor.execute('SELECT Department_ID AS id, Department_Name AS name FROM departments ORDER BY name')
        departments = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('employees.html', employees=employees, departments=departments, employee=None, error=error)

@app.route('/employees/add', methods=['POST'])
def add_employee():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    department_id = parse_int(request.form.get('department_id'))
    hire_date = request.form.get('hire_date', '').strip() or None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO employees (Full_Name, Email, Department_ID, Hiring_Date) VALUES (%s, %s, %s, %s)',
            (full_name, email, department_id, hire_date)
        )
        conn.commit()
        flash('Employee added successfully.')
    except Error as err:
        flash(f'Error adding employee: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('employees'))

@app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    conn = None
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        department_id = parse_int(request.form.get('department_id'))
        hire_date = request.form.get('hire_date', '').strip() or None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE employees SET Full_Name = %s, Email = %s, Department_ID = %s, Hiring_Date = %s WHERE Employee_ID = %s',
                (full_name, email, department_id, hire_date, employee_id)
            )
            conn.commit()
            flash('Employee updated successfully.')
            return redirect(url_for('employees'))
        except Error as err:
            flash(f'Error updating employee: {err}')
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
    employee = None
    employees = []
    departments = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT Employee_ID AS id, Full_Name AS full_name, Email AS email, Department_ID AS department_id, Hiring_Date AS hire_date FROM employees WHERE Employee_ID = %s', (employee_id,))
        employee = cursor.fetchone()
        if employee is None:
            flash('Employee not found.')
            return redirect(url_for('employees'))
        cursor.execute('SELECT e.Employee_ID AS id, e.Full_Name AS full_name, e.Email AS email, e.Hiring_Date AS hire_date, e.Department_ID AS department_id, '
                       'COALESCE(d.Department_Name, "") AS department_name '
                       'FROM employees e '
                       'LEFT JOIN departments d ON e.Department_ID = d.Department_ID '
                       'ORDER BY e.Employee_ID DESC')
        employees = cursor.fetchall()
        cursor.execute('SELECT Department_ID AS id, Department_Name AS name FROM departments ORDER BY name')
        departments = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('employees.html', employees=employees, departments=departments, employee=employee, error=error)

@app.route('/employees/delete/<int:employee_id>')
def delete_employee(employee_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM employees WHERE Employee_ID = %s', (employee_id,))
        conn.commit()
        flash('Employee deleted successfully.')
    except Error as err:
        flash(f'Error deleting employee: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('employees'))

@app.route('/training')
def training():
    records = []
    employees = []
    programs = []
    error = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT et.ET_ID AS id, et.Employee_ID AS employee_id, et.Program_ID AS training_program_id, et.Training_Start_Date AS completion_date, et.Completion_Status AS status, '
            'COALESCE(e.Full_Name, "Not Available") AS employee_name, '
            'COALESCE(tp.Program_Name, "Not Available") AS program_name '
            'FROM employee_training et '
            'LEFT JOIN employees e ON et.Employee_ID = e.Employee_ID '
            'LEFT JOIN training_programs tp ON et.Program_ID = tp.Program_ID '
            'ORDER BY et.ET_ID DESC'
        )
        records = cursor.fetchall()
        cursor.execute('SELECT Employee_ID AS id, Full_Name AS name FROM employees ORDER BY Full_Name')
        employees = cursor.fetchall()
        cursor.execute('SELECT Program_ID AS id, Program_Name AS name FROM training_programs ORDER BY name')
        programs = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('training.html', records=records, employees=employees, programs=programs, record=None, error=error)

@app.route('/training/add', methods=['POST'])
def add_training():
    employee_id = parse_int(request.form.get('employee_id'))
    training_program_id = parse_int(request.form.get('training_program_id'))
    completion_date = request.form.get('completion_date', '').strip() or None
    status = request.form.get('status', '').strip()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO employee_training (Employee_ID, Program_ID, Training_Start_Date, Completion_Status) VALUES (%s, %s, %s, %s)',
            (employee_id, training_program_id, completion_date, status)
        )
        conn.commit()
        flash('Training record added successfully.')
    except Error as err:
        flash(f'Error adding training record: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('training'))

@app.route('/training/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_training(record_id):
    conn = None
    if request.method == 'POST':
        employee_id = parse_int(request.form.get('employee_id'))
        training_program_id = parse_int(request.form.get('training_program_id'))
        completion_date = request.form.get('completion_date', '').strip() or None
        status = request.form.get('status', '').strip()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE employee_training SET Employee_ID = %s, Program_ID = %s, Training_Start_Date = %s, Completion_Status = %s WHERE ET_ID = %s',
                (employee_id, training_program_id, completion_date, status, record_id)
            )
            conn.commit()
            flash('Training record updated successfully.')
            return redirect(url_for('training'))
        except Error as err:
            flash(f'Error updating training record: {err}')
        finally:
            if conn is not None and conn.is_connected():
                conn.close()
    record = None
    records = []
    employees = []
    programs = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT ET_ID AS id, Employee_ID AS employee_id, Program_ID AS training_program_id, Training_Start_Date AS completion_date, Completion_Status AS status FROM employee_training WHERE ET_ID = %s', (record_id,))
        record = cursor.fetchone()
        if record is None:
            flash('Training record not found.')
            return redirect(url_for('training'))
        cursor.execute(
            'SELECT et.ET_ID AS id, et.Employee_ID AS employee_id, et.Program_ID AS training_program_id, et.Training_Start_Date AS completion_date, et.Completion_Status AS status, '
            'COALESCE(e.Full_Name, "Not Available") AS employee_name, '
            'COALESCE(tp.Program_Name, "Not Available") AS program_name '
            'FROM employee_training et '
            'LEFT JOIN employees e ON et.Employee_ID = e.Employee_ID '
            'LEFT JOIN training_programs tp ON et.Program_ID = tp.Program_ID '
            'ORDER BY et.ET_ID DESC'
        )
        records = cursor.fetchall()
        cursor.execute('SELECT Employee_ID AS id, Full_Name AS name FROM employees ORDER BY Full_Name')
        employees = cursor.fetchall()
        cursor.execute('SELECT Program_ID AS id, Program_Name AS name FROM training_programs ORDER BY name')
        programs = cursor.fetchall()
    except Error as err:
        error = str(err)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return render_template('training.html', records=records, employees=employees, programs=programs, record=record, error=error)

@app.route('/training/delete/<int:record_id>')
def delete_training(record_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM employee_training WHERE ET_ID = %s', (record_id,))
        conn.commit()
        flash('Training record deleted successfully.')
    except Error as err:
        flash(f'Error deleting training record: {err}')
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
    return redirect(url_for('training'))

if __name__ == '__main__':
    app.run(debug=True)
