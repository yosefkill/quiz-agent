import os
import requests
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.database import SessionLocal, engine
from dotenv import load_dotenv
import json
import re

load_dotenv()

app = FastAPI()

HUAWEI_API_URL = os.getenv("HUAWEI_API_URL")
HUAWEI_API_KEY = os.getenv("HUAWEI_API_KEY")
HUAWEI_MODEL_NAME = os.getenv("HUAWEI_MODEL_NAME")

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def call_deepseek_generate_quiz(role: str, topic: str, num_questions: int):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HUAWEI_API_KEY}",
    }

    prompt = f"""
    Generate {num_questions} quiz questions for a {role} on {topic} with exactly 4 answer choices each.
    Return ONLY pure JSON array, no text, no markdown, no remarks.

    Format:
    [
      {{
        "question": "...",
        "options": ["choice1", "choice2", "choice3", "choice4"],
        "correct_answer": "choice1"
      }},
     ...
    ]
    """

    payload = {
        "model": HUAWEI_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 1000,
        "top_p": 1,
        "n": 1,
        "stream": False,
        "stop": None
    }

    response = requests.post(HUAWEI_API_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"DeepSeek API error: {response.text}")

    result = response.json()
    content = result["choices"][0]["message"]["content"]
    print("LLM content:", content)  # For debug

    # Extract JSON from any code block or parse raw JSON in text
    match = re.search(r'``````', content)
    if not match:
        match = re.search(r'``````', content)
    if not match:
        start = content.find('[')
        end = content.rfind(']')
        if start != -1 and end != -1 and end > start:
            json_str = content[start:end+1]
        else:
            raise HTTPException(status_code=500, detail="Could not find JSON block in LLM response.")
    else:
        json_str = match.group(1)
    try:
        questions = json.loads(json_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse extracted JSON: {e}")

    return questions

@app.post("/generate_quiz/", response_model=schemas.Quiz)
def generate_quiz(request: schemas.GenerateQuizRequest, db: Session = Depends(get_db)):
    questions_data = call_deepseek_generate_quiz(request.role, request.topic, request.num_questions)
    question_objs = []
    for q in questions_data:
        question_objs.append(schemas.QuestionCreate(
            text=q["question"],
            qtype="mcq",
            options=json.dumps(q["options"]),
            correct=q["correct_answer"]
        ))
    quiz_create = schemas.QuizCreate(
        title=f"{request.role} - {request.topic} Quiz",
        questions=question_objs
    )
    quiz = crud.create_quiz(db, quiz_create)
    return quiz

@app.get("/quiz/{quiz_id}", response_model=schemas.Quiz)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = crud.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    return quiz

@app.post("/answer/", response_model=schemas.Answer)
def submit_answer(answer: schemas.AnswerCreate, db: Session = Depends(get_db)):
    return crud.create_answer(db, answer)

@app.post("/grade/{quiz_id}/{user_id}", response_model=schemas.Result)
def grade_quiz(quiz_id: int, user_id: int, db: Session = Depends(get_db)):
    return crud.grade_quiz(db, quiz_id, user_id)
