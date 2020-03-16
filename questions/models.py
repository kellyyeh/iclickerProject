from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class Lecture(models.Model):
    lectureid = models.CharField("Lecture ID",max_length=10, blank=False)
    question_num = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    anonymous = models.BooleanField("anonymous")
    private = models.BooleanField("private")
    key = models.CharField(max_length=16)

    def __str__(self):
        return self.lectureid

class Participant(models.Model):
    name = models.CharField("name", max_length=100, blank=False)
    lecture = models.ForeignKey(lecture, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, null=True, on_delete=models.CASCADE)
    present = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class question(models.Model):

    title = models.CharField("title",max_length=100, blank=False)
    pub_date = models.DateTimeField("Date Created",auto_now_add=True)
    type = models.CharField("Type", max_length=20)
    active = models.BooleanField(default=True)
    avgVote = models.DecimalField(max_digits=3,decimal_places=2,null=True)
    voteCount = models.IntegerField(null=True)
    lecture = models.ForeignKey(lecture, on_delete=models.CASCADE)


    def __str__(self):
        return self.title

class Option(models.Model):
    option = models.CharField("option", max_length=200, blank=True, default=None)
    question = models.ForeignKey(question, on_delete=models.CASCADE)
    def __str__(self):
        return self.option

class MCVote(models.Model):
    vote = models.ForeignKey(Option, on_delete=models.CASCADE)
    question = models.ForeignKey(question, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.vote.option

