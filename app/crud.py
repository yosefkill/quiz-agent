from sqlalchemy.orm import Session
from app import models, schemas
import json

def create_quiz(db: Session, quiz: schemas.QuizCreate):
    db_quiz = models.Quiz(title=quiz.title)
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)

    for question in quiz.questions:
        db_question = models.Question(
            text=question.text,
            qtype=question.qtype,
            options=question.options,
            correct=question.correct,
            quiz_id=db_quiz.id
        )
        db.add(db_question)
    db.commit()
    return db_quiz

def get_quiz(db: Session, quiz_id: int):
    return db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()

def create_answer(db: Session, answer: schemas.AnswerCreate):
    db_answer = models.Answer(**answer.dict())
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer

def grade_quiz(db: Session, quiz_id: int, user_id: int):
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        return None

    answers = db.query(models.Answer).filter(models.Answer.quiz_id == quiz_id, models.Answer.user_id == user_id).all()
    correct_count = 0
    total = len(quiz.questions)
    for question in quiz.questions:
        user_answer = next((a for a in answers if a.question_id == question.id), None)
        if user_answer and user_answer.response == question.correct:
            correct_count += 1
    
    score = int((correct_count / total) * 100) if total > 0 else 0
    
    feedback = f"Your score: {score}% ({correct_count} out of {total} correct)"
    
    db_result = models.Result(
        user_id=user_id,
        quiz_id=quiz_id,
        score=score,
        feedback=feedback
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result
