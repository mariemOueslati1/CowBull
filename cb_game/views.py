from django.shortcuts import render
from spyne.service import ServiceBase
from spyne.decorator import rpc
from spyne.model.primitive import Unicode,Integer
from spyne.application import Application
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoApplication
from django.views.decorators.csrf import csrf_exempt
from django import forms


import random
# Create your views here.
class GameService(ServiceBase):
    
    
    _hidden_number = set()  # Change the data structure to a set
    _result=""
    _nb_attempts = 10

    @rpc(_returns=Unicode(nillable=False))
    def about():
        data = {
            "title": "About Cow and Bull Game",
            "description": "This is the game of Cow and Bull. You have to guess a 4-digit number (all digits are different). Each time, you have to propose a number. If a proposed digit is in the right place you'll get 'B', if the digit is misplaced you'll get 'C'. You win if you get '4B'. You lose if you make 10 attempts. For example, if the hidden number is 5429, and you give 1432, you'll get 1C and 1B.",
        }
        return data

    

    @rpc(Unicode(nillable=True),Integer(nillable=True),_returns=Unicode(nillable=False))
    def start_game(self,player_name="guess player", nb_attempts=3):
        GameService._hidden_number = set()  # Clear the previous hidden numbers
        GameService._hidden_number.add(random.randint(1, 9))
        while len(GameService._hidden_number)<4:
            GameService._hidden_number.add(random.randint(0,9))

        GameService._player_name=player_name
        if nb_attempts<1 or nb_attempts>10:
            return "Error! The number of attempts must be between 1 and 10."
        GameService._nb_attempts=nb_attempts
        print("hidden number  in start game :" , GameService._hidden_number)
        return "The game was initialized. You can go."



    @rpc( Unicode(nillable=False), _returns=Unicode(nillable=False))
    def play_game(player_proposition, player_name):
        if GameService._nb_attempts == 0:
            print("attemps in play game ", GameService._nb_attempts)
            return "You lost. You have exceeded the maximum attempts."
        
        if GameService._result == '4B':
            print("attemps in play game ", GameService._nb_attempts)
            return "You have already won the game."

        try:
            proposition = str(player_proposition)
            if len(proposition) != 4:
                raise ValueError("You must introduce a 4-digit number")

            hidden_number = list(GameService._hidden_number)
            print("hidden_number : ", hidden_number)
            print("attemps in play game ", GameService._nb_attempts)
            nbBull = 0
            nbCow = 0
            for i in range(4):
                if int(proposition[i]) == hidden_number[i]:
                    nbBull += 1
                elif int(proposition[i]) in GameService._hidden_number:
                    j = 0
                    while j < i and proposition[j] != proposition[i]:
                        j += 1
                    if j == i:
                        nbCow += 1

            GameService._nb_attempts -= 1
            print("attemps in play game ", GameService._nb_attempts)

            if nbBull == 0 and nbCow > 0:
                GameService._result = str(nbCow) + "C"
            elif nbBull > 0 and nbCow == 0:
                GameService._result = str(nbBull) + "B"
            else:
                GameService._result = str(nbBull) + "B" + "-" + str(nbCow) + "C"

            if GameService._result == "4B":
                GameService._result += player_name + " Congratulations! You have won the game"
            
            return GameService._result
        
        except Exception as e:
            return str(e)
        
        
def game_interface(request):
    game_service = GameService()
    data = game_service.about()  # Call the 'about' function to get the data
    return render(request, 'about.html', {'data': data})

def start_game_view(request):
    result = None

    if request.method == 'POST':
        player_name = request.POST.get('player_name', 'Guess Player')
        nb_attempts = int(request.POST.get('attempts', 10))

        # Call the start_game method from your GameService instance
        game_service = GameService()  # Replace with the actual import and instantiation
        result = game_service.start_game(player_name, nb_attempts)

    return render(request, 'start_game_template.html', {'result': result})
def play_game_view(request):
    result = None

    if request.method == 'POST':
        player_proposition = request.POST.get('player_proposition', '')
        player_name = request.POST.get('player_name', 'Guess Player')

        # Call the play_game method from your GameService instance
        game_service = GameService()  # Replace with the actual import and instantiation
        result = game_service.play_game(player_proposition, player_name)
        
        # Print the result to the console
        print(f"Result: {result}")
    return render(request, 'play_game_template.html', {'result': result})
#Create the Django Application to be called remotely
#using Soap11, lxml and the GameService class
spyne_app=Application(
  [GameService],
  #target namespace
  #it contains the tags (like <play_game>,</play_game>, ....) definitions
  tns='http://isg.soa.game.tn',
  #lxml is a library to check the XML, HTML and XHTML definitions
  in_protocol=Soap11(validator='lxml'), #for The SOAP-REQUEST Entity
  out_protocol=Soap11() #for The SOAP-RESPONSE Entity
)
#create the DjangoApplication instance
django_app=DjangoApplication(spyne_app)
#create the instance that will be used to respond to The SOAP-REQUESTs
cb_game_app=csrf_exempt(django_app)