import re
import math

def call_gearcalc(self, e):
    calculator = TireCalc(e.input)
    e.output = e.nick + ', ' + calculator.solve()
    return e
call_gearcalc.command = "!tirecalc"

class TireCalc:

    psi_to_bar = 0.0689476
    lbs_to_kg = 2.20462262185
    parameter_meta_data = {
        'totalweight': {
            'name': 'Weight',
            'examples': ['200lbs']
        },
        'width': {
            'name': 'Width',
            'examples': ['40mm']
        },
        'pertire': {
            'name': 'Percentage of weight on rear tire',
            'examples': ['53%']
        }
    }

    def __init__(self, calc_string):
        self.tokens = self.tokenize(calc_string)
        self.totalweight = self.find_weight()
        self.width = self.find_width()
        self.pertire = self.find_pertire()
        
        #self.cadence = self.find_cadence()
        #self.speed = self.find_speed()
        #self.front_teeth = self.find_front_teeth()
        #self.rear_teeth = self.find_rear_teeth()
        #self.wheel_circumference = self.find_erto()
        #self.metric = self.find_metric()
        
    def get_parameter_meta_data(self, parameter, data_type):
        return self.parameter_meta_data[parameter][data_type]

    def get_list_metadata_from_parameters(self, parameters, data_type):
        return_list = []
        for parameter in parameters:
            value = self.get_parameter_meta_data(parameter, data_type)
            if value is not None:
                if type(value) is list:
                    for item in value:
                        return_list.append(item)
                else:
                    return_list.append(value)
        return return_list

    @staticmethod
    def tokenize(calc_string):
        return re.split('\s', calc_string)

    def solve(self):
        if self.is_solvable():
            front_tire = round((0.7 * (self.totalweight) * (self.totalweight) * (100 - self.pertire) / 100 * (100 - self.pertire) / 100 + 400 * (self.totalweight) * (100 - self.pertire) / 100) / self.width / self.width + 10)
            rear_tire = round((0.7 * (self.totalweight) * (self.totalweight) * (self.pertire) / 100 * (self.pertire) / 100 + 400 * (self.totalweight) * (self.pertire) / 100) / self.width / self.width + 10)
            return "Front Tire: " + str(front_tire) + "psi/" + str(self.psitobar(front_tire)) + "bar | Rear Tire: " + str(rear_tire) + "psi/" + str(self.psitobar(rear_tire)) + "bar"
        else:
            return "I need more information try some of the following: " + ', '.join(str(v) for v in self.get_list_metadata_from_parameters(self.find_missing_parameters(), 'name')) + " Eg.) " + ', '.join(str(v) for v in self.get_list_metadata_from_parameters(self.find_missing_parameters(), 'examples'))

    def psitobar(self, psi):
        return round(self.psi_to_bar * psi, 2)

    def is_solvable(self):
        if self.totalweight != None and self.width != None and self.pertire != None:
            return True
        else:
            return False

    def find_weight(self):
        try:
            #weight = self.tokens[0]
            weight = ''.join(filter(lambda x: x.isdigit(), self.tokens[0]))
            if weight != '':
                return int(weight)
        except:
            return None

    def find_width(self):
        try:
            #width = self.tokens[1]
            width = ''.join(filter(lambda x: x.isdigit(), self.tokens[1]))
            if width != '':
                return int(width)
        except:
            return None

    def find_pertire(self):
        try:
            #pertire = self.tokens[2]
            pertire = ''.join(filter(lambda x: x.isdigit(), self.tokens[2]))
            if pertire != '':
                return int(pertire)
        except:
            return None
    
    def find_missing_parameter(self):
        missing_parameters = self.find_missing_parameters()
        if missing_parameters:
            return missing_parameters.pop(0)

    def find_missing_parameters(self):
        missing_parameters = []
        object_values = vars(self)
        for key in object_values:
            if object_values[key] is None and key != 'metric':
                missing_parameters.append(key)
        return missing_parameters
