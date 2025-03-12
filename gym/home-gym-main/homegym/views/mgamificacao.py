from flask import Flask
from flask import render_template
import sqlite3
from datetime import date, timedelta, datetime


def streak(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT FinishDate
                   FROM FinishTraining
                   WHERE UserID = ?
                   ORDER BY FinishDate
                   """, (userID,))
    data = cursor.fetchall()
    db.close()

    if not data:  # If there are no records
        return 0
    
    dates = sorted(set([datetime.strptime(date[0], "%Y-%m-%d").date() for date in data]), reverse=True)
    streak = 0
    current_date = datetime.now().date()

    for date in dates:
        if date == current_date or date == current_date - timedelta(days=1):
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    return streak

#PROGRESS------------------------------

def get_plans_done(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT COUNT(*)
                   FROM FinishTraining
                   WHERE UserID = ?
                   """, (userID,))
    plans_done = cursor.fetchone()
    db.close()

    return plans_done[0]


def get_exs_done(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT COUNT(*)
                   FROM FinishTraining
                   WHERE UserID = ?
                   """, (userID,))
    plans_done = cursor.fetchone()
    db.close()
    exs_done = plans_done[0]*3

    return exs_done

def get_avg_time(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT AVG(FinishTime)
                   FROM FinishTraining
                   WHERE UserID = ?
                   """, (userID,))
    avg_time = cursor.fetchone()
    db.close()
    
    if avg_time[0] == None:
        return 0
    
    return avg_time[0]


def get_total_time(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT SUM(FinishTime)
                   FROM FinishTraining
                   WHERE UserID = ?
                   """, (userID,))
    total_time = cursor.fetchone()
    db.close()

    if total_time[0] == None:
        return 0
    
    else:
        return total_time[0] / 60
    

#LEVELS------------------------------
def give_plan_xp(userID, planID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT UserXP
                    FROM Users
                    WHERE UserID = ?
                     """, (userID,))
    user_exp = cursor.fetchone()
    db.close()

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT XPreward
                    FROM TrainingPlan
                    WHERE TrainingPlanID = ?
                     """, (planID,))
    plan_exp = cursor.fetchone()

    new_exp = user_exp[0] + plan_exp[0]

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""UPDATE Users
                    SET UserXP = ?
                    WHERE UserID = ?
                     """, (new_exp, userID))
    db.commit()
    db.close()

    return new_exp

def give_badge_xp(userID, badgeID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT UserXP
                    FROM Users
                    WHERE UserID = ?
                     """, (userID,))
    user_exp = cursor.fetchone()
    db.close()

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT XPreward
                    FROM BadgeType
                    WHERE BadgeID = ?
                     """, (badgeID,))
    badge_exp = cursor.fetchone()

    new_exp = user_exp[0] + badge_exp[0]

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""UPDATE Users
                    SET UserXP = ?
                    WHERE UserID = ?
                     """, (new_exp, userID))
    db.commit()
    db.close()

    return new_exp

def check_level(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT LevelID, Experience
                   FROM Levels
                   ORDER BY LevelID DESC
                   """,)
    all_levels = cursor.fetchall()
    db.close()

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT UserXP, LevelID
                    FROM Users
                    WHERE UserID = ?
                     """, (userID,))
    user = cursor.fetchone()
    user_exp = user[0]
    user_level = user[1]
    db.close()

    for level in all_levels:
        if user_exp >= level[1] and user_level < level[0]:
            db = sqlite3.connect('database.db')
            cursor = db.cursor()
            cursor.execute("""UPDATE Users
                            SET LevelID = ?
                            WHERE UserID = ?
                             """, (level[0], userID))
            db.commit()
            db.close()
            return 1
    return 0

def get_plan_xp(planID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT XPreward
                   FROM TrainingPlan
                   WHERE TrainingPlanID = ?
                   """, (planID,))
    plan_exp = cursor.fetchone()
    db.close()

    return plan_exp[0]

def get_level(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT LevelID
                   FROM Users
                   WHERE UserID = ?
                   """, (userID,))
    levelID = cursor.fetchone()
    db.close()

    return levelID[0]

def get_level_progress(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT UserXP, LevelID
                   FROM Users
                   WHERE UserID = ?
                   """, (userID,))
    user = cursor.fetchone()
    print("-----")
    print(user)
    user_exp = user[0]
    user_level = user[1]

    db.close()

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""
            SELECT LevelID, Experience
            FROM Levels
            WHERE LevelID = ?
            UNION
            SELECT LevelID, Experience
            FROM Levels
            WHERE LevelID = ?
        """, (user_level, user_level + 1))
    levels = cursor.fetchall()
    print(levels)
    current_level = levels[0]
    next_level = levels[1]
    db.close()

    return [user_exp, current_level, next_level]

#BADGES--------------------------
def getallbadges():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT Name, Description, Type, Image
                   FROM BadgeType
                   """,)
    badges = cursor.fetchall()
    db.close()

    return badges

def getbadges_type(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT BadgeID
                   FROM UserBadges
                   WHERE UserID = ?
                   """, (userID,))
    badges_id = cursor.fetchall()
    db.close()

    return badges_id

def getbadges_data(badgeID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT Name, Description, Type, Image
                   FROM BadgeType
                   WHERE BadgeID = ?
                   """, (badgeID,))
    badge_data = cursor.fetchone()
    db.close()
    
    return badge_data


#check badges
def badges(userID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT BadgeID
                   FROM UserBadges
                   WHERE UserID = ?
                   """, (userID,))
    badges_id = [item for sublist in cursor.fetchall() for item in sublist]
    db.close()

    badge_checks = {1: badge_check_1, 2: badge_check_2, 3: badge_check_3, 4: badge_check_4}  
    badge_awarded = []

    for badge_id, check_func in badge_checks.items():
        if badge_id not in badges_id:
            if check_func(userID):
                badge_awarded.append(badge_id)

    return badge_awarded


def badge_check_1(userID): #badge 1
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT FinishTrainingID
                   FROM FinishTraining
                   WHERE UserID = ?
                   """, (userID,))
    fin = cursor.fetchone()
    db.close()

    if fin: #se existir um registo de treino
        Awdate = date.today()
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute("""INSERT INTO UserBadges (DateAwarded, UserID, BadgeID)
                       VALUES (?, ?, 1)
                       """, (Awdate,userID,))
        db.commit()
        db.close()
        return True  # Badge awarded
    
    return False


def badge_check_2(userID): #badge 2
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT FinishDate, COUNT(*)
                      FROM FinishTraining
                      WHERE UserID = ?
                      GROUP BY FinishDate
                      HAVING COUNT(*) >= 3
                   """, (userID,))
    result = cursor.fetchone()
    db.close()

    if result:  # If there is a day with at least 3 records
        date = result[0]
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute("""INSERT INTO UserBadges (DateAwarded, UserID, BadgeID)
                          VALUES (?, ?, 2)
                       """, (date, userID,))
        db.commit()
        db.close()
        return True # Badge awarded
    
    return False

def badge_check_3(userID): #badge 3
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT FinishTrainingID
                  FROM FinishTraining
                  WHERE UserID = ?
                  GROUP BY TrainingPlanID
                  HAVING COUNT(*) >= 5
               """, (userID,))
    
    result = cursor.fetchone()
    db.close()

    if result:
        Awdate = date.today()
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute("""INSERT INTO UserBadges (DateAwarded, UserID, BadgeID)
                       VALUES (?, ?, 3)
                       """, (Awdate,userID,))
        db.commit()
        db.close()
        return True  # Badge awarded

    return False

def badge_check_4(userID): #badge 4
    daystreak = streak(userID)

    if daystreak >= 3:
        Awdate = date.today()
        db = sqlite3.connect('database.db')
        cursor = db.cursor()
        cursor.execute("""INSERT INTO UserBadges (DateAwarded, UserID, BadgeID)
                       VALUES (?, ?, 4)
                       """, (Awdate,userID,))
        db.commit()
        db.close()
        return True
    
    return False



