from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
from questions.models import MCVote, NumberedVote, YesNoVote, question, Option, NumberedOption, lecture, Participant
from django.contrib.sessions.models import Session
import json, logging, pdb, time, datetime
logger = logging.getLogger(__name__)

# self.channel_layer -> channel layers allow communication between different instances of an application
#       relies on Redis Channel Layer on the BACKEND


class Consumer(WebsocketConsumer):


    def connect(self):
        # add connection to channel layer

        # This will store the name of the group inside our user's session
        # Consumers receive the connection’s scope when they are initialised, which contains a lot of the information you’d find on the request object in a Django view
        self.lectureid = self.scope['url_route']['kwargs']['lectureid']

        # DETERMINE IF IP MATCH
        self.client_ip_address = self.scope['client']
        print("CLIENT: ",self.client_ip_address)
        self.server_ip_address = self.scope['server']
        print("SERVER: ",self.server_ip_address)
        #CLIENT:  ['192.168.0.15', 54866]
        #SERVER:  ['192.168.0.15', 8001]

        # Group - channels data structure
        # create a group and add it in all channels, so we can send messages to the group
        # Create a group and add the user's channel to it when connecting to the server
        # Wrap with async_to_syc
        async_to_sync(self.channel_layer.group_add)(
            self.lectureid,
            self.channel_name
        )

        self.accept() # Consumer receives a message and replies with the flag "accept"
        # This tells the browser to accept the connection.
        # Other things you can return:
        # --> text - send a string
        # --> bytes - send encrypted data to the frontend

    def disconnect(self, close_code):
        # update user status and discard channel from group
        self.name = self.scope['session'].get('name','') #empty if admin

        session = Session.objects.get(pk=self.scope['session'].session_key)
        lecture = lecture.objects.get(lectureid=self.lectureid)

        if self.name is not 'admin':     # if not admin of the lecture we set this user's presence to false
            p = Participant.objects.filter(name=self.name, lecture=lecture, session=session)

            p.update(present=False)
            id = p[0].pk

        else:
            id = ''

        async_to_sync(self.channel_layer.group_discard)(
            self.lectureid,
            self.channel_name
        )

        assert self.name != ''

        async_to_sync(self.channel_layer.group_send)(
            self.lectureid,
            {
                'type': 'user_left',
                'name':  self.name if self.name != '' else 'ERROR:no name',
                'id': id

            }

        )

        raise StopConsumer




    def receive(self, text_data=None, byte_data=None):
        # receive a message

        json_input_data = json.loads(text_data)

        if 'name' in json_input_data:
            # new user is joining, add him to the group

            self.name = self.scope['session']['name'] = json_input_data['name']
            self.scope['session'].save()

            lecture = lecture.objects.get(lectureid=self.lectureid)
            session = Session.objects.get(pk=self.scope['session'].session_key)
            participant, created = Participant.objects.get_or_create(name=self.name, lecture=lecture, session=session)

            if not created:     # avoid querying twice unnecessarily
                participant.present = True
                participant.save()

            print('CREATED: ',created)
            print(self.name, '\n', session, '\n', lecture, '\n')

            async_to_sync(self.channel_layer.group_send)(
                self.lectureid,
                {
                    'type': 'user_joined',
                    'name': json_input_data['name'],
                    'id': participant.pk,
                }

            )


        elif 'vote' in json_input_data:

            #vote received

            if self.name:    #save vote to DB only if user submitted his name
                try:
                    question = question.objects.filter(lecture__lectureid=self.lectureid, active=True).order_by('-pub_date')[0]
                except:
                    logger.error('No active questions exist')

                vote = json_input_data['vote']
                self.save_vote(question, vote, self.name) #save vote to DB

                self.send(text_data=json.dumps({'conf': vote}))

                async_to_sync(self.channel_layer.group_send)(
                    self.lectureid,
                    {
                        'type': 'receive_vote', #calls the receive_vote method for each client
                        'vote': vote

                    }

                )
        elif 'close' in json_input_data:

            # question closed

            questions = question.objects.filter(lecture__lectureid=self.lectureid, active=True)
            questions.update(active=False)

            async_to_sync(self.channel_layer.group_send)(
                self.lectureid,
                {
                    'type': 'close_question',

                }

            )



        elif 'open' in json_input_data:

            # question opened

            questions = question.objects.filter(lecture__lectureid=self.lectureid, active=True)

            if questions.exists():
                questions.update(active=False) #fallback - deactivate active questions

            title = json_input_data['title'].capitalize()
            type = json_input_data['type']
            options = json_input_data['options']

            self.create_question(title,type,options)

            async_to_sync(self.channel_layer.group_send)(
                self.lectureid,
                {
                    'type': 'open_question',
                    'title': title,
                    'questiontype': type,
                    'options': options
                }

            )

    def receive_vote(self, event):

        vote = event['vote']

        self.send(text_data=json.dumps({
                'vote': vote
        }))

    def user_joined(self, event):
        name = event['name']
        id = event['id']

        self.send(text_data=json.dumps({
                'joined': name,
                'id': id,
        }))

    def user_left(self, event):
        name = event['name']
        id = event['id']

        self.send(text_data=json.dumps({'left': name,
                                        'id': id
                                        }))

    def close_question(self, event):
        self.send(text_data=json.dumps({'close': 'c'}))

    def open_question(self, event):

        title = event['title']
        type = event['questiontype']
        options = event.get('options','')

        self.send(text_data=json.dumps({'newquestion':'',
                                        'title': title,
                                        'type': type,
                                        'options': options,
                                        }))

    def save_vote(self, question, vote, name):

        # save vote to DB

        session = Session.objects.get(pk=self.scope['session'].session_key)
        if question.type =='mc':
            if not MCVote.objects.filter(question=question, session=session).exists():
                option = Option.objects.get(option=vote, question=question)
                v = MCVote.objects.create(vote=option, question=question, session=session) # add user=USERNAME arg for authenticated users

        elif question.type =='yn':
            if not YesNoVote.objects.filter(question=question, session=session).exists():
                v = YesNoVote.objects.create(vote=vote, question=question, session=session)
        elif question.type == 'n':
            if not NumberedVote.objects.filter(question=question, session=session).exists():
                v = NumberedVote.objects.create(vote=vote, question=question, session=session)
        else:
            raise ValueError("Invalid question type.")

        try:
            v
        except:
            raise ValueError("Invalid vote. Did this user already vote?")


    # Create a brand new question using the lecture number
    def create_question(self, title, type, options):
        try:
            lecture = lecture.objects.get(lectureid=self.lectureid)
        except lecture.DoesNotExist:
            logger.error('\nlecture does not exist\n')
            print('\nlecture does not exist\n')

        question = question.objects.create(title=title, type=type, active=True, lecture=lecture)

        if type == 'mc':

            options = list(filter(None,options))   #remove empty strings
                                                        # set() removes duplicates
                                                        # does not remove strings with spaces

            if options:
                for option in options:
                    Option.objects.create(option=option, question=question)


            if start < end:
                NumberedOption.objects.create(question=question, start=start, end=end)

        self.send(text_data=json.dumps({
                'newquestion-conf': 'true'
        }))
def capitalize_string (string):
    " ".join(w.capitalize() for w in string.split())
