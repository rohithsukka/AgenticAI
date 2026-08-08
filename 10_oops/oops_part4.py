class Employee:
    raise_percentage = 1.04 #Class Variable
    num_of_employees = 0


    def __init__(self, first, last, pay):
        self.first = first
        self.last = last
        self.pay = pay
        self.email = f"{first.lower()}.{last.lower()}@infosys.com"
        Employee.num_of_employees += 1

    def full_name(self):
        return f"{self.first} {self.last}"

    def apply_raise(self):
        self.pay = int(self.pay * self.raise_percentage) #4


class Developer(Employee):  #Inheritance. Now every developer is an employee
    raise_percentage = 1.10

    def __init__(self, first, last, pay, prog_lang):
        super().__init__(first, last, pay)
        self.prog_lang = prog_lang

dev1 = Developer("Rahul","Sharma",800000,"python")
emp1 = Employee("Priya","Patel",900000)

print(dev1.full_name())
print(dev1.email)
print(dev1.pay)

dev1.apply_raise()
print(dev1.pay)
print(dev1.raise_percentage)

emp1.apply_raise()
print(emp1.pay)
print(emp1.raise_percentage)


#print(Developer.raise_percentage)


class Manager(Employee):
    raise_percentage = 1.05

    def __init__(self, first, last, pay,employees=None):
        super().__init__(first, last, pay)
        self.employees = employees

    def add_employee(self,emp):
        if emp not in self.employees:
            self.employees.append(emp)

    def remove_employee(self,emp):
        if emp in self.employees:
            self.employees.remove(emp)

    def print_employees(self):
        for emp in self.employees:
            print(f" --> {emp.full_name()}")


    def apply_raise(self):
        super().apply_raise()
        for emp in self.employees:
            emp.pay = int(emp.pay * 1.01)


dev1 = Developer("Rahul","Sharma",800000,"python")
dev2 = Developer("Priya","Patel",900000,"Java")

mgr1 = Manager("Amit","Kumar",150000,[dev1])

mgr1.print_employees()

mgr1.add_employee(dev2)
mgr1.print_employees()

mgr1.remove_employee(dev1)
mgr1.print_employees()

mgr1.apply_raise()
