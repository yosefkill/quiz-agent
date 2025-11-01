from pydantic import BaseModel
from typing import List, Optional

class QuestionBase(BaseModel):
    text: str
    qtype: Optional[str] = "mcq"
    options: str  # JSON string of options
    correct: str

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    quiz_id: int

    class Config:
        orm_mode = True

class QuizBase(BaseModel):
    title: str

class QuizCreate(QuizBase):
    questions: List[QuestionCreate]

class Quiz(QuizBase):
    id: int
    questions: List[Question]

    class Config:
        orm_mode = True

class AnswerCreate(BaseModel):
    user_id: int
    quiz_id: int
    question_id: int
    response: str

class Answer(AnswerCreate):
    id: int
    class Config:
        orm_mode = True

class Result(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    score: int
    feedback: Optional[str]

    class Config:
        orm_mode = True

class GenerateQuizRequest(BaseModel):
    role: str
    topic: str
    num_questions: int = 5
