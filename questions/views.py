import csv, io
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from questions.forms import homeInput, Choices, Numbered, MCForm,YesNoForm, NumberedForm, AdminForm
from django.http import Http404, HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.forms import formset_factory
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from questions.models import lecture, question, Option, NumberedVote, YesNoVote, MCVote, NumberedOption, Participant
from django.utils.safestring import mark_safe

import random, logging, string, channels, json, pdb, datetime, csv

logger = logging.getLogger(__name__)

def admin(request,lectureid):

    lecture = lecture.objects.get(lectureid=lectureid)
    total_questions = lecture.total_questions
    print("total questions:", total_questions)
    question_num = lecture.question_num
    print("question num:", question_num)

    if request.user.is_authenticated:
        pass

    elif request.session.get('key','') != lecture.key:
        return redirect('/'+lectureid)

    options = None

    try:
        print("Inside views.py / admin: try to filter for question")
        question = question.objects.filter(lecture__lectureid=lectureid, active=True).order_by('pub_date')[0] #get latest active question


        if question.type == 'mc':
            options = Option.objects.filter(question_id=question.id)

        count = getvotecount(question)

    except IndexError:

        question = None
        count = None

    newquestion = AdminForm()
    print("Inside views.py / admin: newquestion = AdminForm()")
    participants = Participant.objects.filter(lecture=lecture)


    context = {'question': question,
               'lecture': lecture,
               'total_questions': total_questions,
               'question_num': question_num,
               'options': options,
               'newquestion': newquestion,
               'lectureid': mark_safe(json.dumps(lecture.lectureid)),
               'count': count,
               'participants': participants,
                }
    print("Inside views.py / admin: context contains:",context)

    return render(request, 'questions/iclicker.html', context)


def professor_home(request):
    print("key = ", request.session.get('key',''))
    key = request.session.get('key','')

    print("This is the professor's home page")
    if request.method == "GET":
        return render(request, "questions/professor_home.html", {})

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        messages.error(request,'NOT CSV FILE')


    lecture = createlecture(False, False)
    lectureid = lecture.lectureid


    print("lecture id:",lectureid)


    fieldnames = ("title","option1","option2","option3","option4")
    fi_obj = csv_file.open()
    json_list = []
    with io.TextIOWrapper(fi_obj, encoding='utf-8') as text_file:
        reader = csv.DictReader(text_file, fieldnames,  delimiter=',')
        for row in reader:
            print(row)
            title = row["title"]
            print("row title:", title)
            option1 = row["option1"]
            print(option1)
            option2 = row["option2"]
            print(option2)
            option3 = row["option3"]
            print(option3)
            option4 = row["option4"]
            print(option4)

            json_row = json.dumps(row)
            print("What is this json?!:", json_row)
            json_list.append(json_row)

            question = question(title = title, type = 'mc', active = True, lecture = lecture)
            question.save()

            choice_list = []
            choice_list.append(option1)
            choice_list.append(option2)
            choice_list.append(option3)
            choice_list.append(option4)
            for choice in choice_list:
                o = Option(option=choice, question=question)
                o.save()

    if request.user.is_authenticated:
        pass # save to db
    else:
        request.session['key'] = lecture.key
        request.session['lecture'] = lecture.lectureid
        request.session['name'] = 'admin'
        request.session['list_of_jsons'] = json_list

    return redirect(lecture.lectureid+'/admin')

    context = {'newquestion': newquestion,
               'choiceset': choices,
               'numbered': numbered,
               }


    return render(request, 'questions/professor_home.html')


def student_home(request):
    print("This is the STUDENT HOME/login page")
    print("key = ", request.session.get('key',''))
    key = request.session.get('key','')

    ChoiceSet = formset_factory(Choices, extra=1)

    newquestion = homeInput(None)
    choices = ChoiceSet(None)
    numbered = Numbered(None)
    context = {'newquestion': newquestion,
               'choiceset': choices,
               'numbered': numbered,
               }

    return render(request,'questions/student_home.html', context)


def home(request):

    print("This is the HOME/login page")
    print("key = ", request.session.get('key',''))
    key = request.session.get('key','')

    # Student or professor login..
    
    ChoiceSet = formset_factory(Choices, extra=1)

    newquestion = homeInput(None)
    choices = ChoiceSet(None)
    numbered = Numbered(None)
    context = {'newquestion': newquestion,
               'choiceset': choices,
               'numbered': numbered,
               }

    return render(request,'questions/home.html', context)

def exportcsv(request,lectureid):


    date = datetime.datetime.today().strftime('%m%d%Y')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="questionhistory{}.csv"'.format(date)

    question = question.objects.filter(lecture__lectureid=lectureid, active=True)[0]

    writer = csv.writer(response)
    writer.writerow(['Date Published:', question.pub_date.strftime('%m-%d-%Y')])

    if question.type == 'mc':

        choices = Option.objects.filter(question=question)
        choice_list = list(choices.values_list('option', flat=True))
        votes = []
        percent = []

        for choice in choices:
            numvotes = len(choice.mcvote_set.all())
            count = len(question.mcvote_set.all())

            votes.append(numvotes) # [10, 11, 3..]
            percent.append(round(numvotes/(count if count > 0 else 1)*100,1))

        writer.writerow(['Type:', 'Multiple Choice'])
        writer.writerow(['']+choice_list)
        writer.writerow([question.title]+votes)
        writer.writerow(['Percent:']+percent)

        writer.writerow(['']) # blank rows
        writer.writerow([''])

        writer.writerow(['Name', 'Vote'])

        for vote in question.mcvote_set.all():                        
            s = SessionStore(session_key=vote.session.session_key)    
            writer.writerow([s['name'], vote.vote.option])

    elif question.type == 'n':

        numopt = NumberedOption.objects.get(question=question)
        votes = NumberedVote.objects.filter(question=question)
        votes_list = list(votes.values_list('vote', flat=True))

        writer.writerow(['Type:', 'Numbered'])
        writer.writerow([question.title])
        writer.writerow(['Range:', str(numopt.start) + ' to ' + str(numopt.end)])
        writer.writerow(['Average:', round((sum(votes_list) if votes_list is not None else 0)/(len(votes_list) if len(votes_list) > 0 else 1)), "No Votes" if len(votes_list) > 0 else (str(len(votes_list)) + " Votes")])

        writer.writerow(['']) # blank rows
        writer.writerow([''])

        writer.writerow(['Name', 'Vote'])

        for vote in votes:
            s = SessionStore(session_key=vote.session.session_key)
            writer.writerow([s['name'], vote.vote])

    elif question.type == 'yn':

        v = YesNoVote.objects.filter(question=question)
        yes_count = len(v.filter(vote='Yes'))
        no_count = len(v.filter(vote='No'))
        yes_percent = round(yes_count / (len(v) if len(v) > 0 else 1) * 100, 1)  # make sure not to divide by 0
        no_percent = round(no_count / (len(v) if len(v) > 0 else 1) * 100, 1)  # make sure not to divide by 0

        writer.writerow(['Type:', 'Yes/No'])
        writer.writerow([question.title,'Yes','No'])
        writer.writerow(['Count',yes_count,no_count])
        writer.writerow(['Percent',yes_percent,no_percent])

        writer.writerow(['']) # blank rows
        writer.writerow([''])

        writer.writerow(['Name', 'Vote'])

        for vote in v:
            s = SessionStore(session_key=vote.session.session_key)
            writer.writerow([s['name'], vote.vote])


    return response


# The student's second page
def user(request,lectureid):

    if lectureid == 'favicon.ico':
        raise Http404()
    elif not lecture.objects.filter(lectureid=lectureid).exists():
        raise Http404()

    if request.session.session_key is not None:
        session = Session.objects.get(pk=request.session.session_key)
    else:
        session = None
        hasVoted = False

    try:
        question = question.objects.filter(lecture__lectureid=lectureid, active=True).order_by('-pub_date')[0]

        vote = None

        if question.type == 'mc':
            choices = Option.objects.filter(question_id=question.id)
            choices = [choice.option for choice in choices]
            userform = MCForm(list(zip(string.ascii_uppercase, choices)))  # group choices into tuples and create form
            if session:
                hasVoted = MCVote.objects.filter(question=question, session=session).exists()
                if hasVoted:
                    vote = MCVote.objects.get(question=question, session=session)

        elif question.type == 'n':

            options = NumberedOption.objects.get(question=question)

            try:
                start = int(options.start)
                end = int(options.end)

            except ValueError:
                start = options.start
                end = options.end

            userform = {'start': start,
                        'end': end}

            if session:
                hasVoted = NumberedVote.objects.filter(question=question, session=session).exists()
                if hasVoted:
                    vote = NumberedVote.objects.get(question=question, session=session)


        elif question.type == 'yn':

            userform = YesNoForm()
            hasVoted = YesNoVote.objects.filter(question=question, session=session).exists()
            if session:
                if hasVoted:
                    vote = YesNoVote.objects.get(question=question, session=session)

        else:
            logger.error('Nonexistent question.')
            return HttpResponseNotFound('<h1>Page not found</h1>')

    except IndexError:
        question = None
        userform = None
        hasVoted = False
        vote = None


    if 'name' not in request.session: #first time connecting
        request.session['name'] = ''
        request.session['present'] = ''

    if question:
        questiontype = mark_safe(json.dumps(question.type))
    else:
        questiontype = None

    context = {'lectureid_json': mark_safe(json.dumps(lectureid)),
               'lectureid': lectureid,
               'question': question,
               'questiontype': questiontype,
               'name_json': mark_safe(json.dumps(request.session.get('name',''))),
               'name': request.session.get('name',''),
               'userform': userform,
               'hasVoted': hasVoted,
               'vote': vote,
    }

    return render(request, 'questions/user.html', context)

def createlecture(anon, private):

    lectureid = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(6))  # random lectureid string

    while lecture.objects.filter(lectureid=lectureid).exists():  # ensure unique lectureid
        lectureid = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(6))  # regenerate lectureid

    key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(16))
    lecture = lecture(lectureid=lectureid, question_num=0, total_questions=0, key=key, anonymous=anon, private=private)
    lecture.save()

    return lecture

def getvotecount(question):

    if question.type =='mc':
        return len(question.mcvote_set.all())

def status(request):
    # health check for AWS load balancer
    return HttpResponse(status=200)
