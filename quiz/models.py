from django.db import models
from admin_dashboard.models import User


class Quiz(models.Model):
    name = models.CharField(max_length=120)
    time = models.IntegerField(help_text="duration of the quiz in minutes")
    score_to_pass = models.IntegerField(help_text="Minimum score(%) to pass")
    order = models.PositiveIntegerField(default = 0)
    def __str__(self):
        return f"{self.name}"
    
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "number_of_questions": self.quiz_questions.count(),
            "time": self.time,
            "score_to_pass": self.score_to_pass,
            "order": self.order,
        }
    
    class Meta:
        verbose_name_plural = 'Quizes'
        ordering = ['order']


class Question(models.Model):
    question_text = models.CharField(max_length=255)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,related_name="quiz_questions")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.question_text)
    
    def get_answers(self):
        return self.answers_for_question.all()
    
    def serialize(self):
        return {
            'id': self.id,
            'question_text': self.question_text,
            'quiz': self.quiz.id,
        }
    

class Answer(models.Model):
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False) 
    question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='answers_for_question')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"question: {self.question.question_text}, answer: {self.answer_text}, correct: {self.is_correct}"
    
    def serialize(self):
        return {
            'id': self.id,
            'answer_text': self.answer_text,
            'is_correct': self.is_correct,
            'question': self.question.id,
        }
    

class Result(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="user_results")
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null = True, blank = True)
    user_answers = models.JSONField(default=dict)
    is_passed = models.BooleanField(default=False)

    def __str__(self):
        return f"${self.user}'s result for ${self.quiz}"