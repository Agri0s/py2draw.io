from typing import List, Tuple

# Base class representing a Person
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def __str__(self):
        return f"Name: {self.name}, Age: {self.age}"

# Subclass representing an Employee (inherits from Person)
class Employee(Person):
    def __init__(self, name: str, age: int, employee_id: int, salary: float):
        super().__init__(name, age)
        self.employee_id = employee_id
        self.salary = salary

    def __str__(self):
        return f"{super().__str__()}, Employee ID: {self.employee_id}, Salary: ${self.salary}"

# Subclass representing a Manager (inherits from Employee)
class Manager(Employee):
    def __init__(self, name: str, age: int, employee_id: int, salary: float, department: str):
        super().__init__(name, age, employee_id, salary)
        self.department = department

    def __str__(self):
        return f"{super().__str__()}, Department: {self.department}"

# Class representing a Task
class Task:
    def __init__(self, title: str, description: str, completed: bool = False):
        self.title = title
        self.description = description
        self.completed = completed

    def __str__(self):
        status = "Completed" if self.completed else "Pending"
        return f"Task: {self.title}, Description: {self.description}, Status: {status}"

# Class representing a Company (Aggregation)
class Company:
    def __init__(self, name: str):
        self.name = name
        self.employees: List[Employee] = []  # type: ignore

    def add_employee(self, employee: Employee):
        self.employees.append(employee)

    def __str__(self):
        return f"Company: {self.name}, Employees: {len(self.employees)}"

    def list_employees(self):
        for employee in self.employees:
            print(employee)

# Class representing a Project (Composition)
class Project:
    def __init__(self, title: str, budget: float, manager: Manager):
        self.title = title
        self.budget = budget
        self.manager = manager  # Composition: Project has a Manager who is integral to the project
        self.tasks: List[Task] = []  # type: ignore

    def add_task(self, task: Task):
        self.tasks.append(task)

    def list_tasks(self):
        print(f"Project: {self.title} Tasks:")
        for task in self.tasks:
            print(task)

    def __str__(self):
        return f"Project: {self.title}, Budget: ${self.budget}, Managed by: {self.manager.name}"

# Example usage
if __name__ == "__main__":
    # Create some Person objects
    alice = Person(name="Alice", age=30)
    bob = Employee(name="Bob", age=25, employee_id=101, salary=50000.0)
    charlie = Manager(name="Charlie", age=40, employee_id=102, salary=80000.0, department="Engineering")

    # Create a Company object and add employees (Aggregation)
    company = Company(name="Tech Corp")
    company.add_employee(bob)
    company.add_employee(charlie)

    # List employees in the company
    print(company)
    company.list_employees()

    # Create a Project object (Composition)
    project = Project(title="AI Development", budget=1000000.0, manager=charlie)

    # Create some Task objects and add them to the project
    task1 = Task(title="Design AI Model", description="Design the architecture of the AI model")
    task2 = Task(title="Implement AI", description="Code the AI model based on the design", completed=True)
    task3 = Task(title="Test AI", description="Test the AI model for performance and accuracy")

    project.add_task(task1)
    project.add_task(task2)
    project.add_task(task3)

    # List tasks in the project
    print(project)
    project.list_tasks()
