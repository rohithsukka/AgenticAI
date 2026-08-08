import datetime
class Employee:
    raise_percentage = 1.04 # Class variable
    num_of_employees = 0
    company = "Infosys"

    def __init__(self, first, last, pay):
        self.first = first
        self.last = last
        self.pay = pay
        self.email = f"{first.lower()}.{last.lower()}@infossy.com"
        Employee.num_of_employees += 1

    def full_name(self):
        return f"{self.first} {self.last}"
    
    def apply_raise(self):
        self.pay = int(self.pay * self.raise_percentage) # 4%

    @classmethod
    def set_raise_percentage(cls,amount):
        cls.raise_percentage = amount

    @classmethod
    def get_count(cls):
        return cls.num_of_employees

    @staticmethod
    def is_workday(day):
        return day.weekday() < 5 # 0 is Monday, 6 is Sunday

    
import datetime
my_date = datetime.date(2026,8,6) #Thursday
weekend = datetime.date(2026,8,9) #saturday

print(Employee.is_workday(my_date))
print(Employee.is_workday(weekend))














