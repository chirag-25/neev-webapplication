from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)

# Configure the database
db = yaml.load(open('db.yaml'), Loader=yaml.Loader)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


@app.route("/")
def home():
    return render_template("home.html")
    # return render_template("admin/volunteers.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if (request.method == 'POST'):
        employee_form = request.form
        print(employee_form)
    return render_template("admin/login.html")


@app.route("/admin")
def admin():
    return render_template("admin/dashboard.html")


@app.route("/admin/funding", methods=['POST', 'GET'])
def funding():
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM Funding")
    if result_value > 0:
        userDetails = cur.fetchall()

    profileDetails = []
    for user in userDetails:
        user_profile = {
            'email': user[0], 'amount': user[1], 'benefactor': user[2], 'date': user[3]}
        sponsors_table_query = f"SELECT * FROM Sponsors WHERE email_id = \'{user[0]}\'"
        events_table_query = f"SELECT * FROM Projects"
        # print("before query")

        calculate_sponsors = cur.execute(sponsors_table_query)
        calculate_sponsors = cur.fetchall()

        calculate_events = cur.execute(events_table_query)
        calculate_events = cur.fetchall()

        # print(len(calculate_sponsors))
        if len(calculate_sponsors) > 0:
            user_profile['projects'] = calculate_sponsors
        else:
            # user_profile['email_id'] = 'NA'
            # user_profile['event_name'] = 'NA'
            # user_profile['start_date'] = 'NA'
            user_profile['projects'] = ()

        if (len(calculate_events) > 0):
            user_profile['events'] = calculate_events
        else:
            user_profile['events'] = ()

        # print(len(calculate_events))
        # print(user_profile['events'])
        profileDetails.append(user_profile)
    if (request.method == 'POST'):
        if request.form['signal'] == 'search':
            # pass
            benefactor = request.form['benefactor']
            email = request.form['email']
            amount = request.form['max_amount']
            # date = request.form['funding_date']
            year = request.form['year']
            funding_to = request.form['project_name']
            min_amount = request.form['min_amount']
            max_amount = request.form['max_amount']

            where_query = f" SELECT * FROM Funding"
            flag = False

            if benefactor != '':
                if flag == False:
                    where_query += f" WHERE funder_name = \'{benefactor}\' "
                else:
                    where_query += f"funder_name = \"{benefactor}\""
                flag = True
            if email != '':
                if flag == False:
                    where_query += f" WHERE email_id = \'{email}\' "
                else:
                    where_query += f" AND email_id = \"{email}\""
                flag = True
            if min_amount != '' and max_amount != '':
                if flag == False:
                    where_query += f" WHERE amount BETWEEN \'{min_amount}\' AND \'{max_amount}\'"
                else:
                    where_query += f" AND amount BETWEEN \'{min_amount}\' AND \'{max_amount}\'"
                flag = True

            if funding_to != '':
                if flag == False:
                    where_query += f" WHERE email_id IN (SELECT email_id FROM Sponsors WHERE event_name = \'{funding_to}\')"
                else:
                    where_query += f" AND email_id IN (SELECT email_id FROM Sponsors WHERE event_name = \'{funding_to}\')"
                flag = True

            if year != '':
                if flag == False:
                    where_query += f" WHERE YEAR(date) = {year}"
                else:
                    where_query += f" AND YEAR(date) = {year}"
                flag = True

            exec_query = cur.execute(where_query)
            search_results = cur.fetchall()
            # print(search_results)

            updated_profile_details = []
            for user in profileDetails:
                for result in search_results:
                    # print("email", result[0])
                    if user['email'] == result[0]:
                        updated_profile_details.append(user)
            profileDetails = updated_profile_details

            return render_template('admin/funding.html', userDetails=userDetails, profileDetails=profileDetails)
        elif request.form['signal'] == 'add':
            # print(request.form)
            print("addDetails filled!")

            benefactor = request.form['name']
            amount = request.form['amount_add']
            email = request.form['email']
            date = request.form['funding_date']

            funding_to = request.form['project']

            add_query = f"INSERT INTO Funding (email_id, amount, funder_name, date) "
            add_query = add_query + \
                f"VALUES (\"{email}\", \"{amount}\", \'{benefactor}\', \"{date}\")"
            exec_query = cur.execute(add_query)
            mysql.connection.commit()

            # add_project_query = f"INSERT INTO Sponsors (email_id, event_name, start_date)"
            # add_project_query = add_project_query + f"VALUES (\"{email}\", \"{funding_to}\", \"{date}\" )"
            # add_project_query = add_project_query + f" WHERE email_id = \"{email}\" "

            add_project_query = f"INSERT INTO Sponsors (email_id, event_name, start_date) "
            # assumption is taken here that beneficiary can only participate in current year's project
            add_project_query = add_project_query + \
                f"VALUES (\"{email}\", \"{funding_to}\", (SELECT start_date FROM Projects WHERE event_name = \"{funding_to}\" AND YEAR(start_date) = YEAR(\'{date}\')))"
            exec_add_project_query = cur.execute(add_project_query)
            mysql.connection.commit()

            return redirect('/admin/funding')
        elif request.form['signal'] == 'edit':
            print("iN edit")
            benefactor = request.form['benefactor']
            amount = request.form['amount']
            email = request.form['email']
            date = request.form['funding_date']

            edit_query = f"UPDATE Funding "
            edit_query = edit_query + \
                f"SET funder_name = \'{benefactor}\', amount = \'{amount}\', email_id = \'{email}\', date = \'{date}\' "
            edit_query = edit_query + f"WHERE email_id = \'{email}\'"

            exec_query = cur.execute(edit_query)
            mysql.connection.commit()
            return redirect('/admin/funding')
        elif request.form['signal'] == 'delete':
            email = request.form['email']
            delete_query = f"DELETE FROM Funding WHERE email_id = \'{email}\' "
            exec_query = cur.execute(delete_query)
            mysql.connection.commit()
            return redirect('/admin/funding')
        # print(profileDetails)
    return render_template('admin/funding.html', userDetails=userDetails, profileDetails=profileDetails, calculate_events=calculate_events, calculate_sponsors=calculate_sponsors)


@app.route("/admin/villageprofile", methods=['POST', 'GET'])
def village_profile():
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM VillageProfile")

    if result_value > 0:
        userDetails = cur.fetchall()

    # print(userDetails)
    # Generate the user profile details
    profile_details = []
    for user in userDetails:
        # VillageProfile(pincode, name, no_of_beneficiaries, no_of_primary_health_center, no_of_primary_school, transport,
        #                infrastructure, major_occupation, technical_literacy, year)
        user_profile = {'pincode': user[0], 'name': user[1], 'no_of_beneficiaries': user[2], 'no_of_primary_health_center': user[3],
                        'no_of_primary_school': user[4], 'transport': user[5], 'infrastructure': user[6], 'major_occupation': user[7], 'technical_literacy': user[8], 'year': user[9]}

        extract_beneficiaries_list_query = f"SELECT name,aadhar_id FROM Beneficiary WHERE aadhar_id IN (SELECT aadhar_id FROM belongs WHERE pincode = \'{user[0]}\')"

        extract_beneficiaries_list_query = cur.execute(
            extract_beneficiaries_list_query)
        extract_beneficiaries_list = cur.fetchall()

        calculate_occupation = f"SELECT * FROM VillageProfile"
        calculate_occupation = cur.fetchall()

        if len(extract_beneficiaries_list) > 0:
            user_profile['beneficiaries'] = extract_beneficiaries_list
        else:
            user_profile['beneficiaries'] = ()

        if len(calculate_occupation) > 0:
            user_profile['occupation'] = calculate_occupation
        else:
            user_profile['occupation'] = "NA"

        profile_details.append(user_profile)

    # print(profile_details)

    if (request.method == 'POST'):
        if (request.form['signal'] == 'search'):
            print("this is search query")
            name = request.form['name']
            pinCode = request.form['pinCode']
            occupation = request.form['occupation']
            technical_literacy = request.form['technical_literacy']

            print(name)

            where_query = f" SELECT * FROM VillageProfile"
            flag = False

            if name != '':
                if flag == False:
                    where_query += f" WHERE name = \'{name}\' "
                else:
                    where_query += f"name = \"{name}\""
                flag = True
            if pinCode != '':
                if flag == False:
                    where_query += f" WHERE pincode = \'{pinCode}\' "
                else:
                    where_query += f" AND pincode = \"{pinCode}\""
                flag = True
            if occupation != '':
                if flag == False:
                    where_query += f" WHERE major_occupation = \'{occupation}\' "
                else:
                    where_query += f" AND major_occupation = \"{occupation}\""
                flag = True

            if technical_literacy != '':
                if flag == False:
                    where_query += f" WHERE technical_literacy = \'{technical_literacy}\' "
                else:
                    where_query += f" AND technical_literacy = \"{technical_literacy}\""
                flag = True

            exec_query = cur.execute(where_query)
            print("Search query executed")
            search_results = cur.fetchall()

            # print(search_results)

            updated_profile_details = []
            for user in profile_details:
                for result in search_results:
                    if user['name'] == result[1]:
                        updated_profile_details.append(user)
            profile_details = updated_profile_details
            # print(profileDetails)
        elif (request.form['signal'] == 'editUser'):
            print("this is edit query")
        elif (request.form['signal'] == 'addUser'):
            print("add new data")
        print(calculate_occupation)
    return render_template('admin/village_profile.html', profile_details=profile_details)


@app.route("/admin/volunteers")
def volunteers():
    return render_template("admin/volunteers.html")


@app.route("/admin/projects", methods=['POST', 'GET'])
def projects():
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM Projects")

    if result_value > 0:
        projectDetails = cur.fetchall()

    project_details = []
    for project in projectDetails:
        project_profile = {'event_name': project[0], 'start_date': project[1], 'types': project[2], 'budget': project[3],
                           'no_of_participants': project[4], 'duration': project[5], 'collection': project[6], 'total_expense': project[7]}

        even_name = project_profile['event_name']
        start_date = project_profile['start_date']

        extract_venue_id_query = f"SELECT venue_id FROM HeldAt WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\'"
        extract_beneficiaries_enrolled_query = f"SELECT name,aadhar_id FROM Beneficiary WHERE aadhar_id IN (SELECT aadhar_id FROM participants WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\')"
        extract_volunteers_enrolled_query = f"SELECT name,email_id FROM Volunteers WHERE email_id IN (SELECT email_id FROM volunteering WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\')"
        extract_donors_enrolled_query = f"SELECT funder_name,email_id FROM Funding WHERE email_id IN (SELECT email_id FROM Sponsors WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\')"
        extract_trainers_query = f"SELECT name,email_id FROM Trainers WHERE email_id IN (SELECT email_id FROM trains WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\')"
        extract_employee_query = f"SELECT name,employee_id FROM Teams WHERE employee_id IN (SELECT employee_id FROM Organize WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\')"
        extract_goods_query = f"SELECT item_name,quantity,amount FROM Goods WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\'"
        extract_expense_query = f"SELECT amount,description FROM ProjectExpense WHERE event_name = \'{even_name}\' AND start_date = \'{start_date}\'"

        extract_venue_id_query = cur.execute(extract_venue_id_query)
        extract_venue_id_query = cur.fetchall()
        if len(extract_venue_id_query) > 0:
            project_profile['venue_id'] = extract_venue_id_query[0][0]
        else:
            project_profile['venue_id'] = 'NA'

        extract_beneficiaries_enrolled_query = cur.execute(
            extract_beneficiaries_enrolled_query)
        extract_beneficiaries_enrolled_query = cur.fetchall()
        if len(extract_beneficiaries_enrolled_query) > 0:
            project_profile['beneficiaries'] = extract_beneficiaries_enrolled_query
        else:
            project_profile['beneficiaries'] = ()

        extract_volunteers_enrolled_query = cur.execute(
            extract_volunteers_enrolled_query)
        extract_volunteers_enrolled_query = cur.fetchall()
        if len(extract_volunteers_enrolled_query) > 0:
            project_profile['volunteers'] = extract_volunteers_enrolled_query
        else:
            project_profile['volunteers'] = ()

        extract_donors_enrolled_query = cur.execute(
            extract_donors_enrolled_query)
        extract_donors_enrolled_query = cur.fetchall()
        if len(extract_donors_enrolled_query) > 0:
            project_profile['donors'] = extract_donors_enrolled_query
        else:
            project_profile['donors'] = ()

        extract_trainers_query = cur.execute(extract_trainers_query)
        extract_trainers_query = cur.fetchall()
        if len(extract_trainers_query) > 0:
            project_profile['trainers'] = extract_trainers_query
        else:
            project_profile['trainers'] = ()

        extract_employee_query = cur.execute(extract_employee_query)
        extract_employee_query = cur.fetchall()
        if len(extract_employee_query) > 0:
            project_profile['employees'] = extract_employee_query
        else:
            project_profile['employees'] = ()

        extract_goods_query = cur.execute(extract_goods_query)
        extract_goods_query = cur.fetchall()
        if len(extract_goods_query) > 0:
            project_profile['goods'] = extract_goods_query
        else:
            project_profile['goods'] = ()

        extract_expense_query = cur.execute(extract_expense_query)
        extract_expense_query = cur.fetchall()
        if len(extract_expense_query) > 0:
            project_profile['expenses'] = extract_expense_query
        else:
            project_profile['expenses'] = ()

        project_details.append(project_profile)

    if (request.method == 'POST'):
        if (request.form['signal'] == 'search'):
            event_name = request.form['event_name']
            year = request.form['year']
            type_event = request.form['type_event']
            min_budget = request.form['min_budget']
            max_budget = request.form['max_budget']
            
            where_query = f" SELECT * FROM Projects"
            flag = False

            if event_name != '':
                if flag == False:
                    where_query += f" WHERE event_name = \'{event_name}\' "
                else:
                    where_query += f"event_name = \"{event_name}\""
                flag = True
                
            if year != '':
                if flag == False:
                    where_query += f" WHERE YEAR(start_date) = {year}"
                else:
                    where_query += f" AND YEAR(start_date) = {year}"
                flag = True
            if type_event != '':
                if flag == False:
                    where_query += f" WHERE types = \'{type_event}\' "
                else:
                    where_query += f" AND types = \"{type_event}\""
                flag = True
                
            if min_budget != '' and max_budget != '':
                if flag == False:
                    where_query += f" WHERE budget BETWEEN \'{min_budget}\' AND \'{max_budget}\'"
                else:
                    where_query += f" AND budget BETWEEN \'{min_budget}\' AND \'{max_budget}\'"
                flag = True
                            
            exec_query = cur.execute(where_query)
            print("Search query executed")
            search_results = cur.fetchall()

            # print(search_results)

            updated_profile_details = []
            for user in project_details:
                for result in search_results:
                    if user['event_name'] == result[0]:
                        updated_profile_details.append(user)
            project_details = updated_profile_details
            
            print("this is search query")
        elif (request.form['signal'] == 'editUser'):
            print("this is edit query")
        elif (request.form['signal'] == 'addUser'):
            print("add new data")
    return render_template('admin/projects.html', project_details=project_details)


@app.route("/admin/user", methods=['POST', 'GET'])
def user():
    if (request.method == 'POST'):
        if (request.form['signal'] == 'search'):
            
            print("this is search query")
        elif (request.form['signal'] == 'editUser'):
            print("this is edit query")
        elif (request.form['signal'] == 'addUser'):
            print("add new data")
    return render_template('admin/user.html')


if __name__ == '__main__':
    app.run(debug=True)
