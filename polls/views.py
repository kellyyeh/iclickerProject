import csv, io
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from polls.forms import homeInput, Choices, Numbered, MCForm,YesNoForm, NumberedForm, AdminForm
from django.http import Http404, HttpResponseNotFound, HttpResponse
from django.forms import formset_factory
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from polls.models import Room, Poll, Option, NumberedVote, YesNoVote, MCVote, NumberedOption, Participant
from django.utils.safestring import mark_safe
import csvmapper

import random, logging, string, channels, json, pdb, datetime, csv

logger = logging.getLogger(__name__)

# This is the page where admin has created a poll already
def admin(request,roomid):

    room = Room.objects.get(roomid=roomid)
    total_polls = room.total_polls
    print("total polls:", total_polls)
    poll_num = room.poll_num
    print("poll num:", poll_num)

    if request.user.is_authenticated:
        pass

    elif request.session.get('key','') != room.key:
        return redirect('/'+roomid)

    options = None

    try:
        print("Inside views.py / admin: try to filter for poll")
        poll = Poll.objects.filter(room__roomid=roomid, active=True).order_by('pub_date')[poll_num] #get latest active poll
        if poll_num < room.total_polls:
            room.poll_num = room.poll_num + 1


        if poll.type == 'mc':
            options = Option.objects.filter(poll_id=poll.id)

        elif poll.type == 'n':
            numberedoptions = NumberedOption.objects.get(poll=poll)
            options = [numberedoptions.start,numberedoptions.end]

        count = getvotecount(poll)

    except IndexError: # no active polls

        poll = None
        count = None

    newpoll = AdminForm()
    print("Inside views.py / admin: newpoll = AdminForm()")
    participants = Participant.objects.filter(room=room)


    context = {'poll': poll,
               'room': room,
               'total_polls': total_polls,
               'poll_num': poll_num,
               'options': options,
               'newpoll': newpoll,
               'roomid': mark_safe(json.dumps(room.roomid)),
               'count': count,
               'participants': participants,
                }
    print("Inside views.py / admin: context contains:",context)

    return render(request, 'polls/apollo.html', context)


def professor_home(request):
    print("key = ", request.session.get('key',''))
    key = request.session.get('key','')

    print("This is the professor's home page")
    if request.method == "GET":
        return render(request, "polls/professor_home.html", {})

    csv_file = request.FILES['file']

    if not csv_file.name.endswith('.csv'):
        messages.error(request,'NOT CSV FILE')


    room = createroom(False, False)
    roomid = room.roomid


    print("room id:",roomid)


    fieldnames = ("title","option1","option2","option3","option4")
    fi_obj = csv_file.open()
    json_list = []
    with io.TextIOWrapper(fi_obj, encoding='utf-8') as text_file:
        reader = csv.DictReader(text_file, fieldnames,  delimiter=',')
        for row in reader:
            print(row)
  
            json_row = json.dumps(row)
            print("What is this json?!:", json_row)
            json_list.append(json_row)

            poll = Poll(title = title, type = 'mc', active = True, room = room)
            poll.save()

            room.total_polls = room.total_polls+ 1
            room.save()

            choice_list = []
            choice_list.append(option1)
            choice_list.append(option2)
            choice_list.append(option3)
            choice_list.append(option4)
            for choice in choice_list:
                o = Option(option=choice, poll=poll)
                o.save()


    # Returned back:
    # What is this json?!: {"title": "q1", "option1": "a", "option2": "b", "option3": "c", "option4": "d"}
    # What is this json?!: {"title": "q2", "option1": "a", "option2": "b", "option3": "c", "option4": "d"}
    # What is this json?!: {"title": "q3", "option1": "a", "option2": "b", "option3": "c", "option4": "d"}
    # What is this json?!: {"title": "q4", "option1": "a", "option2": "b", "option3": "c", "option4": "d"}


    # for column in csv.reader(io_string, delimiter=','):
    #     poll = Poll(title = column[0], type = 'mc', active = True, room = room)
    #     poll.save()
    #
    #     # obj = Room.objects.create(val=1)
    #     # Room.objects.filter(roomid=roomid).update(poll_num=F('poll_num') + 1)
    #     # obj.refresh_from_db()
    #     room.total_polls = room.total_polls+ 1
    #     room.save()
    #
    #     choice_list = []
    #     choice_list.append(column[1])
    #     choice_list.append(column[2])
    #     choice_list.append(column[3])
    #     choice_list.append(column[4])
    #     for choice in choice_list:
    #         o = Option(option=choice, poll=poll)
    #         o.save()

    request.session['key'] = room.key
    request.session['room'] = room.roomid
    request.session['name'] = 'admin'
    request.session['list_of_jsons'] = list_of_jsons

    if json_list:
        #return redirect('professor/'+room.roomid)
        return redirect(room.roomid+'/admin')

    return render(request, 'polls/professor_home.html')
    # print("key = ", request.session.get('key',''))
    # key = request.session.get('key','')
    #
    # ChoiceSet = formset_factory(Choices, extra=1)
    #
    # newpoll = homeInput(request.POST or None)
    # choices = ChoiceSet(request.POST or None)
    # numbered = Numbered(request.POST or None)
    #
    # if newpoll.is_valid():
    #
    #     title = newpoll.cleaned_data['title'].capitalize()
    #     type = newpoll.cleaned_data['type']
    #     anon = newpoll.cleaned_data['anonymous']
    #     private = newpoll.cleaned_data['private']
    #
    #
    #     if type == 'mc' and choices.is_valid():
    #
    #         choice_list = []
    #
    #         for choice in choices:
    #             choice_list.append(choice.cleaned_data.get('choice'))
    #
    #         choice_list = list(filter(None,choice_list)) #remove empty strings, does not remove strings with spaces
    #                                                             # set() removes duplicates
    #
    #         if choice_list:
    #             room = createroom(anon, private)
    #
    #             poll = Poll(title=title, type=type, active=True, room=room)
    #             poll.save()
    #
    #             for choice in choice_list:
    #                 o = Option(option=choice, poll=poll)
    #                 o.save()
    #         else:
    #             logger.error('No choices were entered for this poll')
    #             return redirect('')
    #
    #     elif type == 'n' and numbered.is_valid():
    #
    #         start = numbered.cleaned_data['start']
    #         end = numbered.cleaned_data['end']
    #
    #         try:
    #             float(start)
    #             float(end)
    #
    #         except ValueError:
    #
    #             logger.error('Start/End field is not a number')
    #             return redirect('')
    #
    #         if start and end:
    #             room = createroom(anon, private)
    #             poll = Poll(title=title, type=type, active=True, room=room)
    #             poll.save()
    #
    #             options = NumberedOption(poll=poll, start=start, end=end)
    #             options.save()
    #
    #         else:
    #             return redirect('')
    #
    #     elif type == 'yn':
    #         room = createroom(anon, private)
    #         poll = Poll(title=title, type=type, active=True, room=room)
    #         poll.save()
    #
    #     else:
    #         logger.error('invalid poll type')
    #         return redirect('')
    #
    #     if request.user.is_authenticated:
    #         pass # save to db
    #     else:
    #         request.session['key'] = room.key
    #         request.session['room'] = room.roomid
    #         request.session['name'] = 'admin'
    #
    #     return redirect(room.roomid+'/admin')
    #
    # context = {'newpoll': newpoll,
    #            'choiceset': choices,
    #            'numbered': numbered,
    #            }

def student_home(request):
    print("This is the STUDENT HOME/login page")
    print("key = ", request.session.get('key',''))
    key = request.session.get('key','')

    ChoiceSet = formset_factory(Choices, extra=1)

    newpoll = homeInput(None)
    choices = ChoiceSet(None)
    numbered = Numbered(None)
    context = {'newpoll': newpoll,
               'choiceset': choices,
               'numbered': numbered,
               }

    return render(request,'polls/student_home.html', context)


def home(request):

    print("This is the HOME/login page")
    print("key = ", request.session.get('key',''))
    key = request.session.get('key','')

    # Student or professor login..
    ChoiceSet = formset_factory(Choices, extra=1)

    newpoll = homeInput(None)
    choices = ChoiceSet(None)
    numbered = Numbered(None)
    context = {'newpoll': newpoll,
               'choiceset': choices,
               'numbered': numbered,
               }

    return render(request,'polls/home.html', context)

def exportcsv(request,roomid):


    date = datetime.datetime.today().strftime('%m%d%Y')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pollhistory{}.csv"'.format(date)

    poll = Poll.objects.filter(room__roomid=roomid, active=True)[0]

    writer = csv.writer(response)
    writer.writerow(['Date Published:', poll.pub_date.strftime('%m-%d-%Y')])

    if poll.type == 'mc':

        choices = Option.objects.filter(poll=poll)
        choice_list = list(choices.values_list('option', flat=True))
        votes = []
        percent = []

        for choice in choices:
            numvotes = len(choice.mcvote_set.all())
            count = len(poll.mcvote_set.all())

            votes.append(numvotes) # [10, 11, 3..]
            percent.append(round(numvotes/(count if count > 0 else 1)*100,1))

        writer.writerow(['Type:', 'Multiple Choice'])
        writer.writerow(['']+choice_list)
        writer.writerow([poll.title]+votes)
        writer.writerow(['Percent:']+percent)

        writer.writerow(['']) # blank rows
        writer.writerow([''])

        writer.writerow(['Name', 'Vote'])

        for vote in poll.mcvote_set.all():                              # ['Mishari', 'Yes'
            s = SessionStore(session_key=vote.session.session_key)     #   'Munija', 'No'..]
            writer.writerow([s['name'], vote.vote.option])

    elif poll.type == 'n':

        numopt = NumberedOption.objects.get(poll=poll)
        votes = NumberedVote.objects.filter(poll=poll)
        votes_list = list(votes.values_list('vote', flat=True))

        writer.writerow(['Type:', 'Numbered'])
        writer.writerow([poll.title])
        writer.writerow(['Range:', str(numopt.start) + ' to ' + str(numopt.end)])
        writer.writerow(['Average:', round((sum(votes_list) if votes_list is not None else 0)/(len(votes_list) if len(votes_list) > 0 else 1)), "No Votes" if len(votes_list) > 0 else (str(len(votes_list)) + " Votes")])

        writer.writerow(['']) # blank rows
        writer.writerow([''])

        writer.writerow(['Name', 'Vote'])

        for vote in votes:
            s = SessionStore(session_key=vote.session.session_key)
            writer.writerow([s['name'], vote.vote])

    elif poll.type == 'yn':

        v = YesNoVote.objects.filter(poll=poll)
        yes_count = len(v.filter(vote='Yes'))
        no_count = len(v.filter(vote='No'))
        yes_percent = round(yes_count / (len(v) if len(v) > 0 else 1) * 100, 1)  # make sure not to divide by 0
        no_percent = round(no_count / (len(v) if len(v) > 0 else 1) * 100, 1)  # make sure not to divide by 0

        writer.writerow(['Type:', 'Yes/No'])
        writer.writerow([poll.title,'Yes','No'])
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
def user(request,roomid):

    if roomid == 'favicon.ico':
        raise Http404()
    elif not Room.objects.filter(roomid=roomid).exists():
        raise Http404()

    if request.session.session_key is not None:
        session = Session.objects.get(pk=request.session.session_key)
    else:
        session = None
        hasVoted = False

    try:
        poll = Poll.objects.filter(room__roomid=roomid, active=True).order_by('-pub_date')[0]

        vote = None

        if poll.type == 'mc':
            choices = Option.objects.filter(poll_id=poll.id)
            choices = [choice.option for choice in choices]
            userform = MCForm(list(zip(string.ascii_uppercase, choices)))  # group choices into tuples and create form
            if session:
                hasVoted = MCVote.objects.filter(poll=poll, session=session).exists()
                if hasVoted:
                    vote = MCVote.objects.get(poll=poll, session=session)

        elif poll.type == 'n':

            options = NumberedOption.objects.get(poll=poll)

            try:
                start = int(options.start)
                end = int(options.end)

            except ValueError:
                start = options.start
                end = options.end

            userform = {'start': start,
                        'end': end}

            if session:
                hasVoted = NumberedVote.objects.filter(poll=poll, session=session).exists()
                if hasVoted:
                    vote = NumberedVote.objects.get(poll=poll, session=session)


        elif poll.type == 'yn':

            userform = YesNoForm()
            hasVoted = YesNoVote.objects.filter(poll=poll, session=session).exists()
            if session:
                if hasVoted:
                    vote = YesNoVote.objects.get(poll=poll, session=session)

        else:
            logger.error('Nonexistent poll.')
            return HttpResponseNotFound('<h1>Page not found</h1>')

    except IndexError:
        poll = None
        userform = None
        hasVoted = False
        vote = None


    if 'name' not in request.session: #first time connecting
        request.session['name'] = ''
        request.session['present'] = ''

    if poll:
        polltype = mark_safe(json.dumps(poll.type))
    else:
        polltype = None

    context = {'roomid_json': mark_safe(json.dumps(roomid)),
               'roomid': roomid,
               'poll': poll,
               'polltype': polltype,
               'name_json': mark_safe(json.dumps(request.session.get('name',''))),
               'name': request.session.get('name',''),
               'userform': userform,
               'hasVoted': hasVoted,
               'vote': vote,
    }

    return render(request, 'polls/user.html', context)

def createroom(anon, private):

    roomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(6))  # random roomid string

    while Room.objects.filter(roomid=roomid).exists():  # ensure unique roomid
        roomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(6))  # regenerate roomid

    key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(16))
    room = Room(roomid=roomid, poll_num=0, total_polls=0, key=key, anonymous=anon, private=private)
    room.save()

    return room

def getvotecount(poll):

    if poll.type =='mc':
        return len(poll.mcvote_set.all())
    elif poll.type =='yn':
        return len(poll.yesnovote_set.all())
    elif poll.type == 'n':
        return len(poll.numberedvote_set.all())

def status(request):
    # health check for AWS load balancer
    return HttpResponse(status=200)
