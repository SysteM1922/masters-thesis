from flask import Flask
from flask import render_template
import sqlite3

def getUserTrainingPlans(userID):   #devolve ids dos planos do user

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT TrainingPlanID
                   FROM TrainingPlan
                   WHERE UserID = ?
                   """, (userID,))
    training_plans_id = cursor.fetchall()
    db.close()

    if training_plans_id is None:
        return None
    
    return training_plans_id

def getTrainingPlanData(trainingPlanID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""SELECT Name, Description, Type, PlanDuration, TrainImage, Difficulty, XPreward
                   FROM TrainingPlan
                   WHERE TrainingPlanID = ?
                   """, (trainingPlanID,))

    training_plan_data = cursor.fetchone()
    db.close()

    if training_plan_data is None:
        return None
    
    return training_plan_data


def get_exercise_data(exercisePlanID):
    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute("""
                SELECT e1.Name, e1.Description,e1.URL,e1.Type,e1.Difficulty,e1.ExerciseImg,
                    e2.Name, e2.Description,e2.URL,e2.Type,e2.Difficulty,e2.ExerciseImg,
                    e3.Name, e3.Description,e3.URL,e3.Type,e3.Difficulty,e3.ExerciseImg
                FROM ExercisePlan
                INNER JOIN Exercises e1 ON ExercisePlan.Exercise1 = e1.ExerciseID
                INNER JOIN Exercises e2 ON ExercisePlan.Exercise2 = e2.ExerciseID
                INNER JOIN Exercises e3 ON ExercisePlan.Exercise3 = e3.ExerciseID
                WHERE ExercisePlan.ExercisePlanID = ?
                        """, (exercisePlanID,))

    exercise_data = cursor.fetchone()
    db.close()

    exercises = [exercise_data[i:i+6] for i in range(0, len(exercise_data), 6)]
    return exercises