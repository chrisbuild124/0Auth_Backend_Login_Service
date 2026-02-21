class Profile:
    def __init__(self):
        self._name = ""
        self._weight = 0
        self._age = 0
        self._gender = ""
        self._activity_level = ""
        self._goals = ""

    @property 
    def name(self): 
        return self._name 
    
    @name.setter 
    def name(self, value): 
        self._name = value

    @property 
    def weight(self): 
        return self._weight
    
    @weight.setter 
    def weight(self, value): 
        self._weight = value

    @property 
    def age(self): 
        return self._age
    
    @age.setter 
    def age(self, value): 
        self._age = value

    @property 
    def gender(self): 
        return self._gender
    
    @gender.setter 
    def gender(self, value): 
        self._gender = value

    @property 
    def activity_level(self): 
        return self._activity_level
    
    @activity_level.setter 
    def activity_level(self, value): 
        self._activity_level = value

    @property 
    def goals(self): 
        return self._goals
    
    @goals.setter 
    def goals(self, value): 
        self._goals = value
