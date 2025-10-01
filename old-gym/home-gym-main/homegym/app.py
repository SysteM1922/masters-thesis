from datetime import date, timedelta, datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from views import mgvideos, mgamificacao, mgamigos, mgtreinos
from models import *
import secrets
import os


app = Flask(__name__)
#app.config.from_object('config.py')
CORS(app, cors_allowed_origins='*')

app.secret_key = secrets.token_hex(32) #chave para a sessão

with app.app_context():
    init_db()
    clear_db()
    add_exercises()
    add_measurements()
    add_user()
    add_badge_types()
    add_exercise_plan()
    add_training_plan()
    add_levels()
    
    #add_user_badges()
    #add_test_fintrain()


@app.route('/templates/<path:filename>')
def serve_html(filename):
    return send_from_directory(os.path.join(app.root_path, 'templates'), filename)
    
#funções de login/logout/registo ------------------------------------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.get_json().get('userId')
        session['UserID'] = user_id
        session.permanent = True
        #app.permanent_session_lifetime = timedelta(minutes=20)   #tempo da sessão ativa
        return '', 200
    else:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT Username, UserImage FROM Users")
        users = [{"username": row[0], "image_path": row[1]} for row in c.fetchall()]

        conn.close()

        return render_template('login.html', users=users)
    
@app.route('/logout', methods=['GET', 'POST'])
def logout():

    if 'UserID' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE Users SET status= 'Offline' WHERE UserID = ?", (session['UserID'],))
    conn.commit()
    conn.close()

    session.pop('UserID', None)

    return redirect(url_for('login'))


#paginas base ------------------------------------------------------------------------------------------------------
@app.route("/teste", methods=['GET', 'POST'])
def teste():
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    
    return render_template('teste.html')



@app.route("/" , methods=['GET', 'POST'])
def menu():
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    name = get_user_data(session['UserID'])[3]
    image_path = get_user_data(session['UserID'])[5]

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE Users SET status= 'Offline' WHERE UserID = ?", (session['UserID'],))
    conn.commit()
    conn.close()
    
    return render_template('index.html', name = name , image_path = image_path)

@app.route("/meusplanos" , methods=['GET', 'POST'])
def pagina_planos():
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    name = get_user_data(session['UserID'])[3]
    image_path = get_user_data(session['UserID'])[5]
    
    return render_template('MenuPlanos.html', name = name, image_path = image_path)

@app.route("/meuperfil" , methods=['GET', 'POST'])
def pagina_perfil():
    if 'UserID' not in session:
        return redirect(url_for('login'))
    userID = session['UserID']
    user_info = get_user_data(userID)
    name = user_info[3]
    time = datetime.now().strftime('%H:%M')  # Formata a hora para mostrar apenas horas e minutos
    date_today = date.today().strftime('%d/%m/%Y')  
    image_path = user_info[5]    
    mgamificacao.badges(userID)

    return render_template('Perfil.html',time = time, date_today = date_today, image_path = image_path, name = name)

@app.route("/novasessao" , methods=['GET', 'POST'])
def pagina_novasessao():
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    name = get_user_data(session['UserID'])[3]
    image_path = get_user_data(session['UserID'])[5]

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE Users SET status= 'Online' WHERE UserID = ?", (session['UserID'],))
    conn.commit()
    conn.close()
    
    return render_template('NovaSessao.html', name = name, image_path = image_path)

@app.route("/novasessao/<lobbyname>" , methods=['GET', 'POST'])
def pagina_mostrarsessao(lobbyname):
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    db_id = get_user_data(session['UserID'])[0]
    if db_id == 1:
        planId = 7
    else:
        planId = 14
    
    return render_template('Sessao.html', planId = planId)


@app.route("/meusplanos/plano<selectedPlan>" , methods=['GET', 'POST'])
def pagina_mostrarplano(selectedPlan):
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    json_data = planosOrder()
    response, status_code = json_data
    if status_code == 200:
        json_data = response.json
        #print(json_data)
    else:
        print(f"Error: Status Code {status_code}")
    
    id_real = json_data[selectedPlan]

    username = get_username(session['UserID'])
    
    return render_template('PlanoTreino.html', id_real = id_real, username = username)

#fim paginas base




#funções para a API	------------------------------------------------------------------------------------------------------
@app.route("/planos" , methods=['GET', 'POST'])
def show_all_trainingPlans_from_user():                       #devolve todos os planos de treino do user
    #verificar se o user está na sessão
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    userID = session['UserID']
    training_plans_data = {}
    order = {}
    training_plans_ID = mgtreinos.getUserTrainingPlans(userID)

    if training_plans_ID is None:
        return jsonify({'Error': 'No training plans!'}), 404
    
    count = 1
    for id in training_plans_ID:
        if count > 6: #max 6 planos p/user
            break
        id = id[0]
        order[id] = count                                   #{id: order}
        training_plan = mgtreinos.getTrainingPlanData(id)
        training_plans_data[id] = training_plan             #{id: [name, description, type, duration, image]}
        count += 1
    
    combined = [training_plans_data, order]
    return jsonify(combined),200



    
@app.route("/planosOrder" , methods=['GET', 'POST'])
def planosOrder():

    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    userID = session['UserID']
    order = {}
    training_plans_ID = mgtreinos.getUserTrainingPlans(userID)

    if training_plans_ID is None:
        return jsonify({'Error': 'No training plans!'}), 404
    
    count = 1
    for id in training_plans_ID:
        if count > 6: #max 6 planos
            break
        id = id[0]
        order[count] = id                                   #{id: order}
        count += 1
    return jsonify(order),200




@app.route("/planotreino/<trainingPlanID>", methods=['GET', 'POST'])     #devolve info do plano de treino consoante o id
def show_trainingPlan(trainingPlanID):
   
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    training_plan_data = mgtreinos.getTrainingPlanData(trainingPlanID)
    if training_plan_data is None:
        return jsonify({'Error': 'Training plan not found'}), 404
    
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("SELECT ExercisePlanID FROM TrainingPlan WHERE TrainingPlanID = ?", (trainingPlanID,))
    exercisePlanId = cursor.fetchone()
    cursor.close()
    db.close()

    exercise_data = mgtreinos.get_exercise_data(exercisePlanId[0])
    
    return jsonify([training_plan_data, exercise_data]), 200  


@app.route('/FinishPlan', methods=['POST'])
def handle_post():
    data = request.get_json()
    elapsedTime = round(data['elapsedTime'] / 1000)
    planNumber = data['planNumber']

    json_data = planosOrder()
    response, status_code = json_data
    if status_code == 200:
        json_data = response.json
    else:
        print(f"Error: Status Code {status_code}")

    planID = int(json_data[str(planNumber)])
    userID = session['UserID']
    finishDate = date.today()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO FinishTraining (FinishTime, FinishDate, TrainingPlanID, UserID) VALUES (?, ?, ?, ?)", (elapsedTime, finishDate, planID, userID))
    conn.commit()
    conn.close()

    mgamificacao.give_plan_xp(userID, planID) #give xp depending on the plan
    #mgamificacao.check_level(userID)

    return jsonify({'message': 'Success!'}), 200

@app.route('/FinishSharedPlan', methods=['POST'])
def handle_post_shared():
    data = request.get_json()
    elapsedTime = round(data['elapsedTime'] / 1000)
    planNumber = data['planNumber']

    planID = planNumber
    userID = session['UserID']
    finishDate = date.today()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO FinishTraining (FinishTime, FinishDate, TrainingPlanID, UserID) VALUES (?, ?, ?, ?)", (elapsedTime, finishDate, planID, userID))
    conn.commit()
    conn.close()

    mgamificacao.give_plan_xp(userID, planID) #give xp depending on the plan
    #mgamificacao.check_level(userID)

    return jsonify({'message': 'Success!'}), 200


@app.route('/awardedBadges', methods=['GET', 'POST'])
def awardedBadges():
    userID = session['UserID']
    badge_awarded = mgamificacao.badges(userID)

    badge_info = []

    if badge_awarded != []:
        for badge_id in badge_awarded:
            badge_info.append({badge_id : mgamificacao.getbadges_data(badge_id)})
            mgamificacao.give_badge_xp(userID, badge_id)
            
        #mgamificacao.check_level(userID)

    return jsonify(badge_info), 200


@app.route('/userBadges', methods=['GET', 'POST'])
def userBadges():
    userID = session['UserID']
    badge_id = mgamificacao.getbadges_type(userID)
    badge_data_list = [mgamificacao.getbadges_data(id[0]) for id in badge_id]
    return jsonify(badge_data_list), 200

@app.route('/allBadges', methods=['GET', 'POST'])
def allBadges():
    badge_data = mgamificacao.getallbadges()
    return jsonify(badge_data), 200


@app.route('/streak', methods=['GET', 'POST'])
def getstreak():
    userID = session['UserID']
    streak = mgamificacao.streak(userID)
    return jsonify(streak), 200

@app.route('/info', methods=['GET', 'POST'])
def getinfo():
    userID = session['UserID']
    info = get_user_data(userID)

    
    full_name = info[3] + " " + info[4]
    
    measurements = get_measurements(userID)

    register_date = info[8]
    register_date = datetime.strptime( register_date, "%Y-%m-%d")
    register_date = register_date.strftime("%d-%m-%Y")
    
    birthday_user = info[7]
    birthday_data = datetime.strptime( birthday_user, "%Y-%m-%d")
    birthday = birthday_data.strftime("%d-%m-%Y")# Formata a data no estilo europeu
    age = get_age(birthday_data)

    
    return jsonify({
        'register_date': register_date,
        'measurements': measurements,
        'full_name': full_name,
        'birthday': birthday,
        'age': age
    }), 200




@app.route('/progress', methods=['GET', 'POST'])
def getprogress():
    userID = session['UserID']
    plans = mgamificacao.get_plans_done(userID)
    exs = mgamificacao.get_exs_done(userID)
    avg_time = round(mgamificacao.get_avg_time(userID))
    total_time = mgamificacao.get_total_time(userID)
    return jsonify({
        'plans_done': plans,
        'exs_done': exs,
        'avg_time': avg_time,
        'total_time': total_time
    })

@app.route('/getlevel', methods=['GET', 'POST'])
def getlevel():
    userID = session['UserID']
    leveledUp = mgamificacao.check_level(userID)
    level = mgamificacao.get_level(userID)
    return jsonify({
            'level': level,
            'leveledUp': leveledUp,
        }), 200

@app.route('/getplanxp/<planid>', methods=['GET', 'POST'])
def getplanxp(planid):
    xp = mgamificacao.get_plan_xp(planid)
    return jsonify(xp), 200

@app.route('/getlevelprogress', methods=['GET', 'POST'])
def getlevelprogress():
    userID = session['UserID']
    progress = mgamificacao.get_level_progress(userID)
    return jsonify({
        'user_xp': progress[0],
        'current_level': progress[1],
        'next_level': progress[2]
    }), 200

@app.route('/getOnlineFriends', methods=['GET', 'POST'])
def getOnlineFriends():
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    userID = session['UserID']
    online_friends = mgamigos.get_online_friends(userID)
    #print(online_friends)
    if online_friends == []:
        return [], 200
    
    return jsonify(online_friends), 200

#----http requests para o serverApp utilizar------------------------------------------------
@app.route('/getOnlineFriends/<ID>', methods=['GET', 'POST'])
def getOnlineFriendsID(ID):
    online_friends_json = {}
    online_friends = mgamigos.get_online_friends(ID)
    #print(online_friends)
    if online_friends == []:  
        return {}, 200
    
    for friend in online_friends:
        online_friends_json[friend[0]] = friend[1]
        #print(online_friends_json)

    return online_friends_json, 200
        
        

@app.route('/getUserId', methods=['GET', 'POST'])
def getUserId():
    return jsonify(session['UserID']), 200

@app.route('/getUsername/<id>', methods=['GET', 'POST'])
def getUsername(id):
    username = get_username(id)
    
    if username is None:
        return [], 404
    
    return jsonify(username), 200
#----------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(host = '0.0.0.0')
    
    