import sqlite3
from datetime import date
from flask import Flask


def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create tables
    with open('databases/database.sql', 'r') as f:
        sql = f.read()
        c.executescript(sql)

    conn.commit()
    conn.close()


def clear_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # List of all tables
    tables = ['sqlite_sequence', 'BadgeType', 'ExercisePlan', 'Exercises', 'FinishTraining',
              'Food', 'Friendship', 'Measurements', 'Nutrition', 'TrainingPlan', 'UserBadges', 'Users']

    # Delete all rows from all tables
    for table in tables:
        c.execute(f"DELETE FROM {table}")

    conn.commit()
    conn.close()


def add_user():
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # INSERT OR IGNORE a new row of data into the Users table
    c.execute("""
        INSERT OR IGNORE INTO Users (Username, Password, Name, Surname, UserImage,Email, BirthDate, RegistrationDate, Role, UserXP, LevelID, MeasurementsID, Status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('Maria123', '1234', 'Maria', 'Santos', '../static/img/FotoMaria.png', 'testuser@example.com', '1960-01-01', date.today(), 'User', '0', '1','0','Offline'))
    c.execute("""
        INSERT OR IGNORE INTO Users (Username, Password, Name, Surname, UserImage, Email, BirthDate, RegistrationDate, Role, UserXP, LevelID,MeasurementsID, Status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('Jorge123', '1234', 'Jorge', 'Fernandes', '../static/img/FotoJorge.jpg', 'testuser2@example.com', '1955-12-05', date.today(), 'User', '0', '1', '1','Offline'))
    c.execute("""
        INSERT OR IGNORE INTO Users (Username, Password, Name, Surname, UserImage, Email, BirthDate, RegistrationDate, Role, UserXP, LevelID,MeasurementsID, Status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ('Odete123', '1234', 'Odete', 'Lopes', '../static/img/FotoOdete.jpg', 'testuser3@example.com', '1975-02-01', date.today(), 'User', '0', '1', '2','Offline'))
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def add_measurements():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    measurements = [
        (date.today(), 165, 70, 80, 20),
        (date.today(), 180, 85, 90, 25),
        (date.today(), 158, 59, 70, 15)
    ]

    for measurement in measurements:
        measurement_date, height, weight, waist, body_fat = measurement

        # Convert height from cm to m
        height_m = height / 100

        # Calculate BMI
        bmi = round(weight / (height_m ** 2), 1)

        # Insert data into the database
        c.execute(
            "INSERT OR IGNORE INTO Measurements (Date, Height, Weight, Waist, BodyFat, BodyMassIndex) VALUES (?, ?, ?, ?, ?, ?)",
            (measurement_date, height, weight, waist, body_fat, bmi)
        )

    conn.commit()
    conn.close()

def add_badge_types():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO BadgeType (Name, Description, Type, Image, Requirements) VALUES ('Primeiro Treino', 'Concluiu o primeiro treino', 'Training', '../static/img/badge1.jpg', 'Concluir o primeiro treino');")
    c.execute("Insert OR IGNORE INTO BadgeType (Name, Description, Type, Image, Requirements) VALUES ('3 Treinos no mesmo dia', 'Concluiu 3 treinos no mesmo dia', 'Training', '../static/img/badge3treinos.jpg', 'Concluir 3 treinos no mesmo dia');")
    c.execute("INSERT OR IGNORE INTO BadgeType (Name, Description, Type, Image, Requirements) VALUES ('5 Treinos num plano', '5 treinos do mesmo plano', 'Training', '../static/img/badge3image.jpg', 'Concluir 5 treinos num plano');")
    c.execute("INSERT OR IGNORE INTO BadgeType (Name, Description, Type, Image, Requirements) VALUES ('Streak de 3 dias', '3 dias seguidos a treinar', 'Training', '../static/img/badge4image.jpeg', '3 dias seguidos a treinar');")
    
    #not implemented
    #c.execute("Insert OR IGNORE INTO BadgeType (Name, Description, Type, Image, Requirements) VALUES ('Treino de 1 semana', 'Concluiu 7 treinos em 7 dias', 'Training', '../static/img/badge1semana.jpg', 'Concluir 7 treinos em 7 dias');")
    #c.execute("Insert OR IGNORE INTO BadgeType (Name, Description, Type, Image, Requirements) VALUES ('Treino de 1 mês', 'Concluiu 30 treinos em 30 dias', 'Training', '../static/img/badge1mes.png', 'Concluir 30 treinos em 30 dias');")

    conn.commit()
    conn.close()

def add_test_fintrain():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO FinishTraining (FinishTime, FinishDate, Rating, TrainingPlanID, UserID) VALUES (120, '2024-02-28', 5, 1, 1);")
    c.execute("INSERT OR IGNORE INTO FinishTraining (FinishTime, FinishDate, Rating, TrainingPlanID, UserID) VALUES (130, '2024-02-27', 5, 1, 1);")
    c.execute("INSERT OR IGNORE INTO FinishTraining (FinishTime, FinishDate, Rating, TrainingPlanID, UserID) VALUES (99, '2024-02-29', 5, 1, 1);")
    c.execute("INSERT OR IGNORE INTO FinishTraining (FinishTime, FinishDate, Rating, TrainingPlanID, UserID) VALUES (123, '2024-02-29', 5, 1, 1);")
    c.execute("INSERT OR IGNORE INTO FinishTraining (FinishTime, FinishDate, Rating, TrainingPlanID, UserID) VALUES (150, '2024-02-29', 5, 1, 1);")

    conn.commit()
    conn.close()


def add_user_badges():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "INSERT OR IGNORE INTO UserBadges (DateAwarded, BadgeID, UserID) VALUES ('2021-01-01', 1, 1);")
    c.execute(
        "INSERT OR IGNORE INTO UserBadges (DateAwarded, BadgeID, UserID) VALUES ('2021-01-01', 2, 1);")
    c.execute(
        "INSERT OR IGNORE INTO UserBadges (DateAwarded, BadgeID, UserID) VALUES ('2021-01-01', 3, 1);")
    c.execute(
        "INSERT OR IGNORE INTO UserBadges (DateAwarded, BadgeID, UserID) VALUES ('2021-01-01', 4, 1);")

    conn.commit()
    conn.close()

def add_levels():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (0);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (1000);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (2500);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (5000);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (10000);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (20000);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (40000);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (90000);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (100000);")
    c.execute("INSERT OR IGNORE INTO Levels (Experience) VALUES (500000);")

    conn.commit()
    conn.close()


def add_exercises():
    # Connect to the SQLite database
    db = sqlite3.connect('database.db')
    cursor = db.cursor()

    # upper body
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Flexões', 'Um exercício que trabalha o peito, ombros e tríceps, pode ser feito com apoio dos joelhos', 'https://www.youtube.com/watch?v=jWxvty2KROs','static\\img\\flexao.jpg' ,'Musculacao', 'Medium');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg, Type, Difficulty) VALUES ('Bicep Curl', 'Um exercício de braços que trabalha os biceps.', 'https://www.youtube.com/watch?v=pB4Iic8p6Ag', 'static\\img\\bicep.jpg' ,'Musculacao', 'Medium');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg, Type, Difficulty) VALUES ('Abdominais', 'Um exercício de corpo inteiro que trabalha o core.', 'https://www.youtube.com/watch?v=Qz3ylqqJ90M','static\\img\\abs.jpg' , 'Musculacao', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Flexões de Parede', 'Trabalha os músculos do peito, ombros e braços.', 'http://example.com/wall-push-ups', 'static\\img\\flexao.jpg' ,'Musculacao', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Elevação de Halteres Sentado', 'Trabalha os músculos dos ombros.', 'http://example.com/seated-dumbbell-shoulder-press', 'static\\img\\flexao.jpg' ,'Musculacao', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Puxada com Faixa Elástica', 'Fortalece os músculos das costas.', 'http://example.com/resistance-band-pull', 'static\\img\\flexao.jpg' ,'Musculacao', 'Easy');")

    # lower body
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Squats', 'Um exercício composto que trabalha os quadríceps, isquiotibiais e glúteos.', 'https://www.youtube.com/watch?v=42bFodPahBU', 'static\\img\\squat.jpg' ,'Musculacao', 'Medium');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Lunges', 'Um exercício de perna que trabalha os quadríceps e glúteos.', 'https://www.youtube.com/watch?v=1J8mVmtyYpk', 'static\\img\\lunge.jpg' ,'Musculacao', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Squats com salto', 'Um exercício de perna que trabalha os quadríceps e glúteos.', 'https://www.youtube.com/watch?v=txLE-jOCEsc', 'static\\img\\jumpsquat.jpg' ,'Musculacao', 'Hard');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Squats com Faixa Elástica', 'Trabalha os músculos das pernas e glúteos.', 'http://example.com/resistance-band-squats', 'static\\img\\flexao.jpg' ,'Musculacao', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Elevação de Pernas Sentado', 'Trabalha os músculos das pernas.', 'http://example.com/seated-leg-raise', 'static\\img\\flexao.jpg' ,'Musculacao', 'Easy');")

    # cardio
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Polichinelos', 'Um exercício de cardio de corpo inteiro que pode ser feito em casa.', 'https://www.youtube.com/watch?v=2W4ZNSwoW_4', 'static\\img\\jumpingjacks.jpg' ,'Cardio', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Burpees', 'Um exercício de cardio de corpo inteiro que combina agachamentos, saltos e flexões.', 'https://www.youtube.com/watch?v=818SkLAPyKY', 'static\\img\\burpee.jpg' ,'Cardio', 'Hard');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Corrida no Local', 'Um exercício de cardio que também trabalha o core.', 'https://www.youtube.com/watch?v=Cmxr9xcNhgU', 'static\\img\\mountainclimber.jpg' ,'Cardio', 'Medium');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Corrida no Local', 'Um exercício que aumenta a frequência cardíaca e queima calorias, simulando o movimento de correr, mas sem sair do lugar.', 'http://example.com/jogging-in-place', 'static\\img\\flexao.jpg' ,'Cardio', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Saltar à Corda', 'Trabalha a coordenação, resistência e queima calorias.', 'http://example.com/jump-rope','static\\img\\flexao.jpg' , 'Cardio', 'Medium');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg,Type, Difficulty) VALUES ('Step Aeróbico', 'Aumenta a frequência cardíaca e trabalha os músculos das pernas.', 'http://example.com/step-aerobics','static\\img\\flexao.jpg' , 'Cardio', 'Medium');")

    # meditacao
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Meditação', 'Um exercício de relaxamento que ajuda a aliviar o stress.', 'http://example.com/meditation', 'static\\img\\yoga1.jpg' ,'Meditacao', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Meditação2', 'Um exercício de relaxamento que ajuda a aliviar o stress.', 'http://example.com/meditation', 'static\\img\\yoga2.jpg' ,'Meditacao', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Meditação3', 'Um exercício de relaxamento que ajuda a aliviar o stress.', 'http://example.com/meditation', 'static\\img\\yoga3.jpg' ,'Meditacao', 'Easy');")

    # alongamentos membros superiores
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento de Ombros', 'Este alongamento ajuda a alongar os músculos dos ombros e do pescoço.', 'http://exemplo.com/alongamento-ombros', 'static\\img\\ombro.jpg' ,'Alongamento', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento de Bíceps', 'Este alongamento foca nos músculos do bíceps.', 'http://exemplo.com/alongamento-biceps', 'static\\img\\bicep.jpg' ,'Alongamento', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento de Tríceps', 'Este exercício alonga os músculos do tríceps na parte de trás dos braços.', 'http://exemplo.com/alongamento-triceps', 'static\\img\\tricep.jpg' ,'Alongamento', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento dos Flexores do Pulso', 'Ajuda a alongar os músculos do antebraço e dos pulsos.', 'http://example.com/wrist-flexor-stretch', 'static\\img\\flexao.jpg' ,'Alongamento', 'Medium');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento de Costas', 'Este alongamento alonga os músculos das costas.', 'http://exemplo.com/alongamento-costas', 'static\\img\\flexao.jpg' ,'Alongamento', 'Easy');")

    # alongamentos membros inferiores
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento de Quadríceps', 'Este alongamento foca nos músculos dos quadríceps na parte da frente das coxas.', 'http://exemplo.com/alongamento-quadriceps', 'static\\img\\coxa.jpg' ,'Alongamento', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento de Posteriores', 'Este alongamento ajuda a alongar os músculos dos isquiotibiais na parte de trás das coxas.', 'http://exemplo.com/alongamento-isquiotibiais', 'static\\img\\posteriores.jpg' ,'Alongamento', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento dos Gémeos', 'Este alongamento alonga os músculos das panturrilhas na parte de trás das pernas.', 'http://exemplo.com/alongamento-panturrilhas', 'static\\img\\gemeo.jpg' ,'Alongamento', 'Easy');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento dos Flexores do Quadril', 'Ajuda a alongar os músculos da parte frontal da coxa e do quadril.', 'http://example.com/hip-flexor-stretch', 'static\\img\\flexao.jpg' ,'Alongamento', 'Medium');")
    cursor.execute("INSERT OR IGNORE INTO Exercises (Name, Description, URL, ExerciseImg ,Type, Difficulty) VALUES ('Alongamento de Glúteos', 'Este alongamento foca nos músculos dos glúteos.', 'http://exemplo.com/alongamento-gluteos', 'static\\img\\flexao.jpg' ,'Alongamento', 'Easy');")

    # ver as dificuldades

    db.commit()
    db.close()


def add_exercise_plan():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()

    # upper body
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (1, 2, 3);")
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (4, 5, 6);")

    # lower body
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (7, 8, 9);")
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (9, 10, 11);")

    # cardio
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (12, 13, 14);")
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (15, 16, 17);")

    # meditacao
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (18, 19, 20);")

    # alongamentos membros superiores
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (21, 22, 23);")
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (23, 24, 25);")

    # alongamentos membros inferiores
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (26, 27, 28);")
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (28, 29, 30);")
    

    #shared training plan
    cursor.execute(
        "INSERT OR IGNORE INTO ExercisePlan (Exercise1, Exercise2, Exercise3) VALUES (7, 8, 2);")


    db.commit()
    db.close()


def add_training_plan():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()

    # user1
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Treino de parte superior', 'Este plano visa a trabalhar a parte superior do corpo.', 'Musculacao', 'Medium', 150, 'static\\img\\upper-body.jpg' , 1, 1, 150);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Treino de parte inferior', 'Este plano visa a trabalhar a parte inferior do corpo.', 'Musculacao','Hard', 150,'static\\img\\lower-body.jpg', 3, 1, 200);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Treino de cardio', 'O objetivo deste plano é aumentar a resistencia.', 'Cardio','Hard', 150, 'static\\img\\cardio.jpg',5 , 1, 200);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Meditacao', 'Este plano tem como objetivo promover o relaxamento e a saúde mental.', 'Meditacao','Easy', 300, 'static\\img\\meditation.jpg',7, 1, 100);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Alongamentos membros superiores', 'A finalidade deste plano é melhorar a flexibilidade e aliviar a tensão muscular dos membros superiores.', 'Musculacao', 'Easy',90, 'static\\img\\upper-stretches.jpg',8, 1, 100);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Alongamentos membros inferiores', 'A finalidade deste plano é melhorar a flexibilidade e aliviar a tensão muscular dos membros inferiores', 'Musculacao', 'Easy',90, 'static\\img\\lower-stretches.jpg',10, 1, 100);")
    

    # user2
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Treino de parte superior', 'Este plano visa a trabalhar a parte superior do corpo.', 'Musculacao', 'Easy',150, 'static\\img\\upper-body.jpg',2, 2, 150);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Treino de parte inferior', 'Este plano visa a trabalhar a parte inferior do corpo.', 'Musculacao', 'Easy',150, 'static\\img\\lower-body.jpg',4, 3, 200);")  # changed user to 3 to test
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Treino de cardio', 'O objetivo deste plano é aumentar a resistencia.', 'Cardio','Easy', 150, 'static\\img\\cardio.jpg',6, 2, 200);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Meditacao', 'Este plano tem como objetivo promover o relaxamento e a saúde mental.', 'Meditacao','Easy', 300, 'static\\img\\meditation.jpg', 7, 2, 100);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Alongamentos membros superiores', 'A finalidade deste plano é melhorar a flexibilidade e aliviar a tensão muscular dos membros superiores.', 'Musculacao','Easy', 90,'static\\img\\upper-stretches.jpg', 9, 2, 100);")
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Alongamentos membros inferiores', 'A finalidade deste plano é melhorar a flexibilidade e aliviar a tensão muscular dos membros inferiores', 'Musculacao', 'Easy',90,'static\\img\\lower-stretches.jpg', 11, 2, 100);")
    
    #shared training plan
    cursor.execute("INSERT OR IGNORE INTO TrainingPlan (Name, Description, Type, Difficulty, PlanDuration, TrainImage,ExercisePlanID, UserID, XPreward) VALUES ('Treino corpo todo', 'Este plano visa a trabalhar a parte superior do corpo assim como a parte inferior.', 'Musculacao', 'Medium',150, 'static\\img\\upper-body.jpg',12,0,150);")
    db.commit()
    db.close()


def get_username(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("SELECT Username FROM Users WHERE UserID = ?", (userID,))
    username = cursor.fetchone()
    db.close()
    return username[0]


def get_user_data(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Users WHERE UserID = ?", (userID,))
    user_data = cursor.fetchone()
    print(user_data)
    db.close()
    return list(user_data)


def get_age(birthdate):
    today = date.today()
    age = today.year - birthdate.year - \
        ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def get_measurements(measurementsID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Measurements WHERE MeasurementsID = ?", (measurementsID,))
    measurements = cursor.fetchone()
    db.close()
    return measurements