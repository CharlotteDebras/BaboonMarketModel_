# BABOON MARKET MODEL
# Charlotte DEBRAS
# 8 paires de boxes 
# p la probabilité qu'au moment de choisir, l'individu focal trouve l'option aller dehors plus attractive que toutes les autres 
########################################################################################################################################################


########################################################################################################################################################
# PACKAGES A IMPORTER :

import random

import statistics
from statistics import mean

from math import *
# import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt

import csv 


########################################################################################################################################################


# PARAMETRES GENERAUX

mean_sat = 0 


Ne = 0

proba = 5



gamma = 0.5 # chance de se faire rejoindre 

delta = 0.25 # risque de se faiRe quitter 

minimal_RT = 5 # temps de réponse minimum qu'un singe peut produire lorsqu'il réalise une tâche 
initial_RT = 20 # temps de réponse initial (perfomance initiale)
a_solo = (1/60) #  (anciennement alpha) : espérance des gains d'une tâche solitaire 

# Feedback sociaux : de combien augmente  ou diminue le temps de réponse 
# Feedbacks sociaux positifs (fait baisser l'investissement coopératif)

soc_acc_chosen =  0.1
soc_acc_cbd = 0.1

# Feedbacks sociaux neutres 

#neutral_soc_feedback = 0 
soc_rej_not_chosen = 0
soc_acc_rechosen = 0
soc_acc_accepted = 0

# Feedbacks sociaux négatifs (fait augmenter l'investissement coopératif)

left_for_no_other = -0.5
soc_rej_rejected = -0.5
soc_rej_left = -0.5



#####################################################################################################################################################################################################################################################################
# CLASSE : AGENT
#####################################################################################################################################################################################################################################################################

the_agents = []
leavers = []


# INITIALISATION DE LA CLASSE AGENT :


class Agent:
    position = 0  # position initiale = 0 (outside), sinon le numéro du box que l'agent occupe
    current_state = 0 # état initial 0 correspond à "free" , les autres états sont 1 : "alone" et 2 : "paired"
    last_state = 0
    current_gain = 0
    partner = None
    last_partner = None 
    comparison_box_dico = {1:0,2:0}  # A modifier en fonction du nombre de paire de boxes 
    agent_history = []
    a_mean = 0
    already_chosen = False 
    coop_invest = 0
    performance = 0
    saturation = 0 
    choice = ''

    def __init__(self, name, number, gain_max , feedback_history):
        self.name = name
        self.number = number
        self.gain_max = gain_max
        self.feedback_history = feedback_history

        
        the_agents.append(self)
        
        
############################################
# INIT_HISTORY
# Statut : OK
# Objectif : définir pour chaque agent, une liste composée initialement de N_agents tuples (la première valeur du tuple étant le nom de l'agent, la seconde sa valeur de coopération initiale)

    def init_history(self):
        l = []

        for agent in the_agents:
            if self != agent:
                l.append((agent.name, agent.coop_invest))

        return l       
    

############################################
# COMPUTE MEAN
# Statut : OK
# Objectif : calculer a_mean : la valeur que l'agent focal attribue à un individu moyen, basée sur ce qu'il a reçu de ses partenaires lors de ses interactions passées 


    def compute_a_mean(self):
        value = []

        for i in self.agent_history:
            value.append(i[1])

        a_mean = mean(value)
        return a_mean   

############################################
# COMPUTE SATURATION
# Statut : OK
# Objectif : recalcule la saturation à chaque pas de temps 

    def compute_saturation(self):
        current_gain = self.current_gain
        gain_max = self.gain_max
        saturation = current_gain / gain_max
        return saturation

############################################
# COMPUTE EPSILON 
# Statut : OK
# Objectif : sortir une valeur d'epsilon dans une loi uniforme comprise entre 0 et 1 

    def compute_epsilon(self):
        epsilon = np.random.uniform(-0.02, 0.02)
        return epsilon      
        
        
############################################
# COMPUTE SOLO OPTION
# Statut : OK
# Objectif : Attribuer une valeur a une paire de boxes présentant une option "tâche solo"


    def compute_solo_option(self, box_number):
        epsilon = self.compute_epsilon()
        self.a_mean = self.compute_a_mean()
        self.saturation = self.compute_saturation()
        op1 = ((1-gamma) * a_solo) + (gamma * (self.a_mean ))
        op2 = 1 - self.saturation
        
        box_value = ( op1* op2)  + epsilon
        

        for key , value in self.comparison_box_dico.items():
            if key == box_number:
                self.comparison_box_dico[box_number] = box_value
        return self.comparison_box_dico
     

############################################
# COMPUTE COOP OPTION
# Statut : 
# Objectif : Attribuer une valeur a une paire de boxes présentant une option "tâche coop"

    def compute_coop_option(self, box_number,partner):
        values = []
        a_partner = 0

        for my_partner in self.agent_history:
            if my_partner[0] == partner:
                values.append(my_partner[1])
            else:
                pass
            if len(values) == 1 :
                a_partner = values[0]
            if len(values) in range (2,5) :
                a_partner = mean(values)
            if len(values) > 5:
                a_partner = mean(values[-5:])
            
            epsilon = self.compute_epsilon()
            self.saturation = self.compute_saturation()
            op1 = ((1-delta) * (a_partner)) + (delta * a_solo)
            op2 = 1 - self.saturation

            box_value = ( op1* op2)  + epsilon
           
            for key , value in self.comparison_box_dico.items():
                if key == box_number:
                    self.comparison_box_dico[box_number] = box_value
        return self.comparison_box_dico
                    

############################################
# COMPUTE IMPOSSIBLE OPTION
# Statut : OK
# Objectif : Attribuer une valeur négative (donc toujours moins bien que l'option "sortir") aux boxes complets (sauf pour les agents qui y sont déjà)
    
    
    def compute_impossible_option(self, box_number):
        box_value = -1
        for key , value in self.comparison_box_dico.items():
            if key == box_number:
                self.comparison_box_dico[box_number] = box_value
        return self.comparison_box_dico
            

############################################
# COMPARE OPTION 
# Statut : OK
# Comparer les différents boxes entre eux  

    def compare_options(self,the_boxes):
        for box in the_boxes:
            
###  SI L'AGENT EST DEHORS ("FREE") ####
            
            if self.current_state == 0:

## si le box que l'agent focal évalue est vide -> fait le calcul pour un box de tâche solitaire 
               
                if box.get_occupancy() == 0:
                    box_number = box.number
                    
                    self.compute_solo_option(box_number)
                    print(self.name, "analyse le box solo n°", box.number)


## si le box que l'agent focal évalue contient un indivudu -> fait le calcul pour un box de tâche coopérative          


                if box.get_occupancy() == 1:
                    box_number = box.number
                    partner = box.agents_inside[0]
                    
                    self.compute_coop_option(box_number, partner)
                    print(self.name, "analyse le box de coopération n°", box.number)


## si le box que l'agent focal évalue est plein (et comme il est dehors, il ne peut par définition pas être un des occupants ) -> fait le calcul pour l'option impossible   

                if box.get_occupancy() == 2:
                    box_number = box.number
                    self.compute_impossible_option(box_number)
                    print(self.name, "analyse un box complet")

              
                    
###  SI L'AGENT EST SEUL DANS UNE PAIRE DE BOXES ("ALONE") ####         
                
                    
            if self.current_state == 1: 

## si le box que l'agent focal évalue est vide -> fait le calcul pour un box de tâche solitaire 

                if box.get_occupancy() == 0:
                    box_number = box.number
                   
                    self.compute_solo_option(box_number)
                    print(self.name, "analyse le box solo n°", box.number)
 
 ## si le box que l'agent focal évalue contient un indivudu :  l'occupant peut être  (1) l'agent focal  ou (2) un autre agent                  
                    
                if box.get_occupancy() == 1:
                    box_number = box.number

# (1) L'occupant est l'agent focal -> fait le calcul pour un box de tâche solitaire 


                    if box.number == self.position:
                        box_number = box.number
                  
                        self.compute_solo_option(box_number)
                        print(self.name, "analyse le box solo n°", box.number)

# (2) L'occupant n'est pas l'agent focal -> fait le calcul pour un box de tâche coopérative  

                    else:
                        partner = box.agents_inside[0]
                        box_number = box.number
                        self.compute_coop_option(box_number, partner)
                        print(self.name, "analyse le box de coopération n°", box.number)
                        
## si le box que l'agent focal évalue est plein : l'agent focal étant "Alone", il ne peut, par définition, pas être un des occupants          
                        
                        
                if box.get_occupancy() == 2:
                    box_number = box.number
           
                    self.compute_impossible_option(box_number) 
                    print(self.name, "analyse un box complet")
             
                    
###  SI L'AGENT EST APPAIRE AVEC UN PARTENAIRE DANS UNE PAIRE DE BOXES ("PAIRED") ####         
             
            if self.current_state == 2: 
                
## si le box que l'agent focal évalue est vide -> fait le calcul pour un box de tâche solitaire 

                if box.get_occupancy() == 0:
                    
                    box_number = box.number
                    self.compute_solo_option(box_number)
                    print(self.name, "analyse le box solo n°", box.number)


 ## si le box que l'agent focal évalue contient un seul indivudu : l'agent focal étant "Paired", il ne peut, par définition, pas être cet occupant                          
                    
                if box.get_occupancy() == 1:
                    box_number = box.number
                    partner = box.agents_inside[0]
                    self.compute_coop_option(box_number, partner)
                    print(self.name, "analyse le box de coopération n°", box.number)
                    
## si le box que l'agent focal évalue est plein : l'agent focal peut être  (1) l'un des occupants  ou (2) étrangé à ce box
                    
                if box.get_occupancy() == 2:

# (1) L'agent focal est l'un des occupants -> fait le calcul pour un box de tâche de coopération  

                    if box.number == self.position:
                        box_number = box.number
                        if  box.agents_inside[0] == self.name:
                            partner = box.agents_inside[1]
                        else:
                            partner = box.agents_inside[0]
                            box_number = box.number
                        self.compute_coop_option(box_number, partner)
                        print(self.name, "analyse le box de coopération n°", box.number)

# (2) L'agent focal est étrangé à ce box, il ne peut par conséquent pas y rentrer -> fait le calcul pour l'option impossible   


                    else:
                        box_number = box.number
                        self.compute_impossible_option(box_number) 
                        print(self.name, "analyse un box complet")
        print(self.name, "box comparison list is : ",self.comparison_box_dico)
        

############################################
# CHOOSE BEST OPTION
# Statut : OK
# Objectif : Trouver la meilleure option parmi toutes celles comparées, changer de position en conséquence, remplir ou vider les boxes associés 
    
    
    def choose_best_option(self,the_boxes):
        
        best_choice = 0  # Par défaut pas de meilleur choix   
        max_value = 0 # Par défaut, pas de valeur maximale 
        
        
        for key, value in enumerate(self.comparison_box_dico.values()):
            if value > max_value:
                max_value = value
                
                
        for key, value in  self.comparison_box_dico.items():
            if value == max_value:
                best_choice = key
        print(self.name, "prefered box is :", best_choice)
        
### SI L'AGENT FOCAL EST DEHORS ("FREE") 

        if self.position == 0:

# et que sa meilleure option est supérieure à 0, il rejoint ce box 

            if best_choice != 0:
                for box in the_boxes :
                    if box.number == best_choice:
                        if len(box.agents_inside) < 2 :
                            box.put_agent_in_box(self.name)
                            self.position = best_choice




                        else:
                            pass

# si sa meilleure option est négative, il reste dehors                 
            else:
                self.position = 0

### SI L'AGENT FOCAL EST DANS UN BOX ("ALONE" ou "PAIRED")


# et que sa meilleure option est supérieure à 0, il rejoint ce box ET sort de celui qu'il occupait jusqu'à présent (ssi il ne choisi pas de rester dans son box)       
        else:
            if best_choice != 0:
                
# Le meilleur choix est de rester dans le meme box, sa position ne change donc pas 
                
                if best_choice == self.position: 
                    pass 
                
# Le meilleur choix est de rejoindre un nouveau box                  
                else : 
                    
# L'agent focal quitte le box qu'il occupait jusqu'à présent 

                    for box in the_boxes: 
                        
                        if box.number == self.position: 
                            box.remove_agent(self.name)
                            self.position = None 
                        else: 
                            pass 
                        
# ... et rejoint son nouveau box 

                    for other in the_boxes: 
                        if other.number == best_choice: 
                            if len(other.agents_inside) < 2 :
                                other.put_agent_in_box(self.name)
                                self.position = best_choice
                            else:
                                pass
                        else:
                            pass
                        
  
# si sa meilleure option est négative, il va dehors et sort du box qu'il occupait jusqu'à présent 

            else:
                for box in the_boxes :
                    if box.number == self.position:
                        box.remove_agent(self.name)
                self.position = 0

       
############################################
# UPDATE LAST STATE 
# Statut : OK
# Objectif : Le "current_state" de l'itération précédente devient le "last_state" 


    def update_last_state(agent):
        for agent in the_agents:
            agent.last_state = agent.current_state
        
        
############################################
# UPDATE CURRENT STATE 
# Statut : OK
# Objectif : Modifier l'état de l'individu qui choisi (i.e l'individu focal) 
#            ET celui de l'individu qui subit les répercussions (rejoint ou quitté) 
#            + Attribue les partenaires aux agents qui en ont 



    def update_current_state(agent, the_boxes):

        for agent in the_agents:
            if agent.position == 0:
                if agent.last_state == 2: 
                    agent.current_state = 0
                    agent.partner = None 
                else:
                    agent.current_state = 0
                    agent.partner = None
            else:
                for box in the_boxes:
                    if agent.position == box.number:
                        agent.current_state = len(box.agents_inside)

                        if agent.current_state == 2 :
                            if box.agents_inside[0] == agent.name:
                                agent.partner = box.agents_inside[1]
                            else:
                                agent.partner = box.agents_inside[0]

                        if agent.current_state == 1: 
                            if agent.last_state == 2: 
                                agent.last_partner = agent.partner 
                                for other in the_agents: 
                                    if other.name == agent.last_partner:
                                        other.last_partner = agent.name
                                    else:
                                        pass
                                agent.partner = None
                            else:
                                agent.last_partner = None
                                agent.partner = None






############################################
# UPDATE ALREADY_CHOSEN 
# Statut : OK
# Objectif : Le "current_state" de l'itération précédente devient le "last_state" 
# NB : Ne pas oublier de créer une méthode qui réinitialise TRUE -> FALSE à la fin 

    def update_already_chosen(self):
        self.already_chosen = True 

        
############################################
# LEAVE_GAME
# Statut : 
# Objectif :  Une fois que l'agent a atteint sa saturation : sort automatiquement 

    def leave_game(self,the_boxes):
        if self.number in leavers: 
            pass 
        
        else:
            for box in the_boxes:
                if self.position == box.number: 
                    if box.agents_inside[0] == self.name:
                        del box.agents_inside[0]
                    else:
                        del box.agents_inside[1]
            self.position = 0
            leavers.append(self.number)
            self.update_last_state()
            self.update_current_state(the_boxes)
            self.update_already_chosen()
            self.update_social_feedback_history(the_agents, the_boxes)
            with open('leavers8boxes', 'a', newline ='') as csvfile:
                fieldname = ['PDT', 'NE', 'Agent','AgentInvest']
                writer2 = csv.DictWriter(csvfile, fieldnames=fieldname)
                writer2.writerow({'PDT': TimeScale, 'NE' : Ne , 'Agent' : focal.name, 'AgentInvest': focal.coop_invest })


############################################
# COMPUTE OUTSIDE OPTION ATTRACTIVITY 
# Statut : 
# Objectif :  

    def outside_option_attractivity(self,the_boxes,the_agents):


        if self.current_state == 0 : 
            pass
        



        if self.current_state == 1:

            self.update_last_state()
            for box in the_boxes :
                if box.number == self.position:
                    box.remove_agent(self.name)
                else:
                    pass
            self.position = 0
            self.update_current_state(the_boxes)




        if self.current_state == 2:

            self.update_last_state()
            for box in the_boxes :
                if box.number == self.position:
                    box.remove_agent(self.name)
                else:
                    pass
            self.position = 0
            self.update_current_state(the_boxes)



            for agent in the_agents: 

                if agent.name == self.partner: 
                    agent.update_last_state()
                    agent.partner = None
                    agent.update_current_state(the_boxes)
                
                else:
                    pass


            

####################################################################################################################
#                                                MAKE CHOICE
####################################################################################################################
# Statut : 
# Objectif : Procédure de choix regroupant :
#             - (1) la comparaison des options 
#             - (2) le choix de la meilleure option 
#             - (3) la modification de l'état de l'individu focal et des individus impactés par ce choix


    def make_choice(self,the_boxes):
        n = random.randint(1,100)
        if n < proba : 
            self.choice = 'No'
            self.outside_option_attractivity(the_boxes,the_agents)
            self.update_already_chosen()
            self.update_social_feedback_history(the_agents, the_boxes)

        else:
            self.choice = 'Yes'
            self.compare_options(the_boxes)
            self.choose_best_option(the_boxes)
            self.update_last_state()
            self.update_current_state(the_boxes)
            self.update_already_chosen()
            self.update_social_feedback_history(the_agents, the_boxes)
      


############################################
# UPDATE SOCIAL FEEDBACK HISTORY
# Statut : OK
# Objectif : Remplir, au cours d'un pas de temps, l'histoire des feedback sociaux reçus par chaque individu (IMPACT DU CHOIX DE L'AGENT FOCAL SUR LES AUTRES AGENTS)

    def update_social_feedback_history(self, the_agents, the_boxes):

        for agent in the_agents:





# Pour tout agent différent de l'agent focal 

            if agent.name != self.name:


# (0) - Si l'agent est actuellement dehors --> Aucun effet, car le choix de l'agent focal n'influence pas le feedback social des individus qui n'occupent aucun box :

                if agent.current_state == 0: 
                    pass



# (1) - Si l'agent est actuellement dans un box solo, càd associé à aucun partenaire : le choix de l'agent focal peut entrainer les feedbacks : (1) Quitté, (2) Pas choisi 


                if agent.current_state == 1: 


                    if agent.last_state == 0:
                        pass


# Si l'agent était déjà seul, c'est qu'il n'a pas été choisi 

                    if agent.last_state == 1: 

                        l = []
                        for other in the_agents:
                            if agent.name != other.name:
                                if other.last_state == 1 and other.current_state == 2:
                                    l.append("not chosen")
                                if other.last_state == 0 and other.current_state == 1:
                                    l.append("not chosen")
                        if any(l):
                            agent.feedback_history.append("not chosen")


# Si l'agent était avec un partenaire, c'est soit qu'il a été rejeté (dans le cas où il a déjà choisi), soit qu'il a été 

                    if agent.last_state == 2: 

                        if agent.already_chosen == True :

                            if self.name == agent.last_partner: 
                                if self.current_state == 0: 
                                    agent.feedback_history.append("left for no other partner")
                                else:
                                    agent.feedback_history.append("rejected")

                        else:
                            if self.name == agent.last_partner: 
                                if self.current_state == 0: 
                                    agent.feedback_history.append("left for no other partner")
                                else:
                                    agent.feedback_history.append("left")
 


# (2) - Si l'agent est actuellement associé à un partenaire : 

                if agent.current_state == 2:

                    # et que ce partenaire est l'individu focal :
                    if agent.partner == self.name:

                        # si l'agent était déjà dans l'état 2 avant que l'individu focal ne choisisse et si l'individu focal est son partenaire actuel, alors l'agent focal était déjà son partenaire, il l'a donc rechoisi 

                        if agent.last_state == 2 : 
                            if agent.already_chosen == False :
                                if agent.last_partner == self.name:
                                    agent.feedback_history.append("re-chosen")
                                
                            else:
                                agent.feedback_history.append("accepted")


                        else:
                            coopbox = []
                            cbd = []
                            for box in the_boxes:
                                if box.get_occupancy() == 1:
                                    coopbox.append(box.number)
                                else:
                                    pass

                            if len(coopbox) != 0: 
                                agent.feedback_history.append("chosen")
                            else:
                                cbd.append("chosen by default")
                            if any (cbd):
                                agent.feedback_history.append("chosen by default")
                                
                

# Si le partenaire de cet agent n'est pas l'individu focal, on ne fait rien 
                    
                    else:
                        pass

                    
####################################################################################################################
#                                                GIVE GAINS 
####################################################################################################################
    

############################################
# INIT PERFORMANCE 
# Statut : 
# Objectif

    def init_performance(self):
        
        self.performance = initial_RT
        

############################################
# INIT COOPERATION 
# Statut : 
# Objectif

    def init_coop_invest(self):
        
        self.coop_invest = 1/self.performance 
        

        
            
        
############################################
# UPDATE PERF 
# Statut : OK
# Objectif : Modifier la coopération en fonction des feedbacks sociaux reçus au cours d'un pas de temps (POUR TOUS LES AGENTS)

    def update_performance(self):

        

        

        

# Feedbacks sociaux positifs         

        if "chosen" in self.feedback_history:
            self.performance = self.performance + soc_acc_chosen
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass




        if "re-chosen" in self.feedback_history:
            self.performance = self.performance + soc_acc_rechosen
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass


        if "chosen by default" in self.feedback_history:
            self.performance = self.performance + soc_acc_cbd
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass


        if "accepted" in self.feedback_history:
            self.performance = self.performance + soc_acc_accepted
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass

# Feedbacks sociaux neutres 

#        if "neutral" in self.feedback_history:
#            self.performance = self.performance + neutral_soc_feedback
#            if self.performance < minimal_RT:
#                self.performance = minimal_RT
#            else:
#                pass

# Feedbacks sociaux négatifs  

        if "left for no other partner" in self.feedback_history:
            self.performance = self.performance + left_for_no_other
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass


        if "rejected"  in self.feedback_history:
            self.performance = self.performance + soc_rej_rejected
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass


        if "left"  in  self.feedback_history:
            self.performance = self.performance + soc_rej_left
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass


        if "not chosen"  in  self.feedback_history:
            self.performance = self.performance + soc_rej_not_chosen
            if self.performance < minimal_RT:
                self.performance = minimal_RT
            else:
                pass

        else:
            pass

        

############################################
# UPDATE COOPERATION 
# Statut : OK
# Objectif : Modifier la coopération en fonction des feedbacks sociaux reçus au cours d'un pas de temps (POUR TOUS LES AGENTS)

    def update_cooperation(self):
        
        
        self.coop_invest = (1/self.performance)
     
 

############################################
# UPDATE GAIN  
# Statut : 
# Objectif : Actualiser les gains (dans le cadre d'un dilemme du prisonnier)

    def update_gain(self):
        
       

        if self.current_state == 2: 
            for agent in the_agents: 
                if agent.name == self.partner: 
                    partner = agent 
                    self.current_gain = self.current_gain + partner.coop_invest
                    agent.agent_history.append((agent.partner, partner.coop_invest))
                else:
                    pass

        if self.current_state == 1: 
            self.current_gain = self.current_gain + a_solo 
        else:
            pass

            
############################################
# RESET SOCIAL FEEDBACK HISTORY
# Statut : 0K
# Objectif : Vider la liste Social Feedback History (SFH)

    def reset_SFH(self):
        for agent in the_agents: 
            del agent.feedback_history[:]


############################################
# RESET ALREADY CHOSEN 
# Statut : 
# Objectif : Vider la liste Social Feedback History (SFH)

    def reset_already_chosen(self):
        for agent in the_agents: 
            agent.already_chosen = False

#####################################################################################################
#                                     AGENTS MAKER 
#####################################################################################################        
        
Agent("Angele", 1, 222,[])
Agent("Arielle", 2, 95,[])
Agent("Atmosphere", 3, 150,[])
Agent("Bobo", 4, 42,[])
Agent("Ewine", 5, 180,[])
Agent("Fana", 6, 118,[])
Agent("Felipe", 7, 23,[])
Agent("Feya", 8, 76,[])
Agent("Harlem", 9, 82,[])
Agent("Kali", 10, 222,[])
Agent("Lips", 11, 161,[])
Agent("Lome", 12, 191,[])
Agent("Mako", 13, 211,[])
Agent("Mali", 14, 116,[])
Agent("Muse", 15, 126,[])
Agent("Nekke", 16, 96,[])
Agent("Petoulette", 17, 72,[])
Agent("Pipo", 18, 35,[])
Agent("Violette", 19, 221,[])

#####################################################################################################################################################################################################################################################################
# CLASSE : BOXES
#####################################################################################################################################################################################################################################################################

the_boxes = []

# INITIALISATION DE LA CLASSE BOXES :


class Box:
    value = None

    def __init__(self, number, agents_inside):
        self.number = number
        self.agents_inside = agents_inside
        the_boxes.append(self)




########################################################################################################################################################################################################################################################################

# METHODES DES PAIRES DE BOXES

############################################


############################################
# GET OCCUPANCY 
# Statut : OK
# Objectif : Retourner l'occupation d'un box (vide, à moitié rempli ou totalement rempli )

    def get_occupancy(self):
        return len(self.agents_inside)

############################################
# PUT AGENT IN BOX 
# Statut : OK
# Objectif : Ajouter un agent à un box 

    def put_agent_in_box(self, name):
        return self.agents_inside.append(name)

############################################
# REMOVE AGENT 
# Statut : OK
# Objectif : Retirer un agent d'un box 
    
    def remove_agent(self, name):
        if self.agents_inside[0] == name:
            del self.agents_inside[0]
        else:
            del self.agents_inside[1]
        return self.agents_inside


#####################################################################################################
#                                     BOX PAIRS MAKER
#####################################################################################################

Box(1, [])
Box(2, [])



########################################################################################################################################################
# MAIN
########################################################################################################################################################
# Etape 1 : On attribue à chaque agent une histoire qui par défaut attribue une valeur initial_coop à tous ses partenaires potentiels



for agent in the_agents:
    agent.init_performance()
    agent.init_coop_invest()
    
for agent in the_agents: 
    agent.agent_history = agent.init_history()

for agent in the_agents: 
    agent.a_mean = agent.compute_a_mean()
    print(agent.name, "Agent's a_mean = ", agent.a_mean)
    agent.saturation = agent.compute_saturation()
    print(agent.saturation)


# Tous les agents ont leur liste "histoire" initialisée

def randomize_rank():
    random.shuffle(the_agents)   

############################################
# Compute Mean Saturation 
# Statut : 
# Objectif : Calculer la saturation moyenne de l'ensemble des agents à chaque pas de temps 

def mean_saturation(the_agents, mean_sat):
    
    tot_saturation = []
    for agent in the_agents: 
        tot_saturation.append(agent.saturation) 
    mean_sat = mean(tot_saturation)
    print(mean_sat)
    return mean_sat



############################################
# Compute_Ne
# Statut : 
# Objectif : Calculer l'effectif efficace à chaque pas de temps

def compute_Ne(the_agents, Ne):
    
    Ne = len(the_agents) - len(leavers)

    return Ne



############################################



# a_mean est à recalculer à chaque fois, il faut donc l'appeler

TimeScale = 0

with open('6boxes_results', 'a', newline ='') as f: 
    fieldnames = ['TimeScale','Agent_name','Coop_invest' ,'Position', 'State','Partner','Last_partner','Choice','History' ]
    thewriter = csv.DictWriter(f, fieldnames = fieldnames)
    thewriter.writeheader()
         
#with open('8boxes', 'a', newline ='') as csvfile:
 #   fieldname = ['PasdeTemps', 'BoxNumber', 'AgentsInside','MeanSaturation', 'Effectif_efficace']
 #   writer = csv.DictWriter(csvfile, fieldnames=fieldname)
 #   writer.writeheader()
    
#with open('leavers8boxes', 'a', newline ='') as csvfile:
  #  fieldname = ['PDT', 'NE', 'Agent','AgentInvest']
  #  writer2 = csv.DictWriter(csvfile, fieldnames=fieldname)
   # writer2.writeheader()        
         
    
while len(leavers) != 19 : 
    TimeScale = TimeScale + 1
    

        
    randomize_rank()
    for agent in the_agents:
        agent.reset_already_chosen()
        agent.reset_SFH()


    for focal in the_agents:
        if focal.saturation <1:
            focal.make_choice(the_boxes)
           

            
        else:
            focal.leave_game(the_boxes)
            



        
        
    for agent in the_agents:
        agent.update_performance()
        agent.update_cooperation()
        agent.update_gain()

        
    
    for box in the_boxes:
        print(box.agents_inside)

    mean_sat = mean_saturation(the_agents, mean_sat)
    Ne = compute_Ne(the_agents, Ne)
    
    for agent in the_agents:
        with open('6boxes_results', 'a', newline ='') as f:
            thewriter = csv.DictWriter(f, fieldnames = fieldnames)
            thewriter.writerow({'TimeScale' : TimeScale  , 'Agent_name' : agent.name ,'Coop_invest': agent.coop_invest ,'Position': agent.position, 'State': agent.current_state, 'Partner' : agent.partner,'Last_partner': agent.last_partner, 'Choice' : agent.choice ,'History': agent.feedback_history})
    
  #  with open('8boxes', 'a', newline ='') as csvfile:
   #     fieldname = ['PasdeTemps', 'BoxNumber', 'AgentsInside', 'MeanSaturation', 'Effectif_efficace']
   #     writer = csv.DictWriter(csvfile, fieldnames=fieldname)
    #    for box in the_boxes:  
     #       writer.writerow({'PasdeTemps': TimeScale, 'BoxNumber': box.number,'AgentsInside': len(box.agents_inside), 'MeanSaturation' : mean_sat, 'Effectif_efficace': Ne})

                    
               
        

        
        
        
        
        