class Employee:

    def __init__(self, first, last, pay):
        self.first = first,
        self.last = last,
        self.pay = pay,
        self.email = f"{first.lower()}.{last.lower()}@infosys.com"

    def full_name(self):
        return f"{self.first} {self.last}"

    def increase_pay(self,percentage):
        self.pay = int(self.pay * (1+percentage/100))

    


emp1 = Employee("Rahul","Sharma",50000)

emp2 = Employee("Priya","Patel",40000)

print(emp1.last)
print(emp2.last)

print(emp1.email)
print(emp1.pay)

emp1.pay = 60000
print(emp1.pay)

print(emp1.__dict__)


# print the full name of the employee

print(emp1.first,emp1.last)

print(emp2.full_name())

emp1.increase_pay(4)
print(emp1.pay)

emp1.increase_pay(4)
print(emp1.pay)
Employee.increase_pay(emp1,4)
print(emp1.pay)