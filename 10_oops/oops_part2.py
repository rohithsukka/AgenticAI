class Employee:
    raise_percentage = 1.04 #Class Variable
    count = 0

    #__slots__ = ["first","last","pay","email"] # This is enforcing python

    def __init__(self, first, last, pay):
        self.first = first
        self.last = last
        self.pay = pay
        self.email = f"{first.lower()}.{last.lower()}@infosys.com"
        Employee.count += 1
        #self.count += 1

    def full_name(self):
        return f"{self.first} {self.last}"

    def increase_pay(self):
        self.pay = int(self.pay * self.raise_percentage) #4


emp1 = Employee("Rahul","Sharma",800000)
print(emp1.count)
emp2 = Employee("Priya" , "Patel",600000)
print(emp2.count)
emp3 = Employee("mani" , "Sharma",700000)
print(emp3.count)


print(Employee.count)


Employee.raise_percentage = 1.07

emp1.raise_percentage = 1.15
print(Employee.raise_percentage)
print(emp1.raise_percentage)
print(emp2.raise_percentage)

# print(type(emp1.first))
# print(type(emp1.last))
# print(type(emp1.pay))
#print(emp1.__dict__)

#print(Employee.raise_percentage)

#print(emp1.raise_percentage)

# emp1.increase_pay()
# print(emp1.pay)

#emp1.pya = 500000 #Typo
# print(emp1.__dict__) #The pay is still 800000

# employees = [Employee("Rahul","Sharma",800000),
#              Employee("Priya","Patel",900000)]

# employees[0].department = "Engineering"

# for emp in employees:
#      print(emp.department)