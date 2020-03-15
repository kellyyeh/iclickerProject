from channels.generic.websocket import WebsocketConsumer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
from polls.models import MCVote, NumberedVote, YesNoVote, Poll, Option, NumberedOption, Room, Participant
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
        self.roomid = self.scope['url_route']['kwargs']['roomid']

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
            self.roomid,
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
        room = Room.objects.get(roomid=self.roomid)

        if self.name is not 'admin':     # if not admin of the room we set this user's presence to false
            p = Participant.objects.filter(name=self.name, room=room, session=session)

            p.update(present=False)
            id = p[0].pk

        else:
            id = ''

        async_to_sync(self.channel_layer.group_discard)(
            self.roomid,
            self.channel_name
        )

        assert self.name != ''

        async_to_sync(self.channel_layer.group_send)(
            self.roomid,
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

            room = Room.objects.get(roomid=self.roomid)
            session = Session.objects.get(pk=self.scope['session'].session_key)
            participant, created = Participant.objects.get_or_create(name=self.name, room=room, session=session)

            if not created:     # avoid querying twice unnecessarily
                participant.present = True
                participant.save()

            print('CREATED: ',created)
            print(self.name, '\n', session, '\n', room, '\n')

            async_to_sync(self.channel_layer.group_send)(
                self.roomid,
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
                    poll = Poll.objects.filter(room__roomid=self.roomid, active=True).order_by('-pub_date')[0]
                except:
                    logger.error('No active polls exist')

                vote = json_input_data['vote']
                self.save_vote(poll, vote, self.name) #save vote to DB

                self.send(text_data=json.dumps({'conf': vote}))

                async_to_sync(self.channel_layer.group_send)(
                    self.roomid,
                    {
                        'type': 'receive_vote', #calls the receive_vote method for each client
                        'vote': vote

                    }

                )
        elif 'close' in json_input_data:

            # poll closed

            polls = Poll.objects.filter(room__roomid=self.roomid, active=True)
            polls.update(active=False)

            async_to_sync(self.channel_layer.group_send)(
                self.roomid,
                {
                    'type': 'close_poll',

                }

            )



        elif 'open' in json_input_data:

            # poll opened

            polls = Poll.objects.filter(room__roomid=self.roomid, active=True)

            if polls.exists():
                polls.update(active=False) #fallback - deactivate active polls

            title = json_input_data['title'].capitalize()
            type = json_input_data['type']
            options = json_input_data['options']

            self.create_poll(title,type,options)

            async_to_sync(self.channel_layer.group_send)(
                self.roomid,
                {
                    'type': 'open_poll',
                    'title': title,
                    'polltype': type,
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

    def close_poll(self, event):
        self.send(text_data=json.dumps({'close': 'c'}))

    def open_poll(self, event):

        title = event['title']
        type = event['polltype']
        options = event.get('options','')

        self.send(text_data=json.dumps({'newpoll':'',
                                        'title': title,
                                        'type': type,
                                        'options': options,
                                        }))

    def save_vote(self, poll, vote, name):

        # save vote to DB

        session = Session.objects.get(pk=self.scope['session'].session_key)
        if poll.type =='mc':
            if not MCVote.objects.filter(poll=poll, session=session).exists():
                option = Option.objects.get(option=vote, poll=poll)
                v = MCVote.objects.create(vote=option, poll=poll, session=session) # add user=USERNAME arg for authenticated users

        elif poll.type =='yn':
            if not YesNoVote.objects.filter(poll=poll, session=session).exists():
                v = YesNoVote.objects.create(vote=vote, poll=poll, session=session)
        elif poll.type == 'n':
            if not NumberedVote.objects.filter(poll=poll, session=session).exists():
                v = NumberedVote.objects.create(vote=vote, poll=poll, session=session)
        else:
            raise ValueError("Invalid poll type.")

        try:
            v
        except:
            raise ValueError("Invalid vote. Did this user already vote?")


    # Create a brand new poll using the room number
    def create_poll(self, title, type, options):
        try:
            room = Room.objects.get(roomid=self.roomid)
        except Room.DoesNotExist:
            logger.error('\nroom does not exist\n')
            print('\nroom does not exist\n')

        poll = Poll.objects.create(title=title, type=type, active=True, room=room)

        if type == 'mc':

            options = list(filter(None,options))   #remove empty strings
                                                        # set() removes duplicates
                                                        # does not remove strings with spaces

            if options:
                for option in options:
                    Option.objects.create(option=option, poll=poll)

        elif type == 'n':
            try:
                start = float(options[0])
                end = float(options[1])
            except:
                logger.error('Entry is not a float')
                return

            if start < end:
                NumberedOption.objects.create(poll=poll, start=start, end=end)

        self.send(text_data=json.dumps({
                'newpoll-conf': 'true'
        }))
def capitalize_string (string):
    " ".join(w.capitalize() for w in string.split())
