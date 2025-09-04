import datetime
import pickle
from collections import UserDict

# Декоратор для обробки помилок введення.
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError, KeyError, AttributeError) as e:
            # Змінено: повертаємо конкретне повідомлення для KeyError та AttributeError.
            if isinstance(e, (KeyError, AttributeError)):
                return "Контакт не знайдено."
            return str(e)
    return inner

# Базовий клас для полів запису.
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

# Клас для імені контакту.
class Name(Field):
    pass

# Клас для номера телефону з валідацією.
class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Номер телефону повинен містити 10 цифр.")
        super().__init__(value)

# Клас для дати народження з валідацією.
# Змінено: збереження значення як рядка та додано метод для перетворення на об'єкт дати.
class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Невірний формат дати. Використовуйте DD.MM.YYYY")
        super().__init__(value)

    # Додано: метод для отримання об'єкта дати.
    @property
    def date(self):
        return datetime.datetime.strptime(self.value, "%d.%m.%Y").date()

# Клас для запису контакту.
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None 

    def add_phone(self, phone_number):
        phone_obj = Phone(phone_number)
        self.phones.append(phone_obj)

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def remove_phone(self, phone_number):
        phone = self.find_phone(phone_number)
        if phone:
            self.phones.remove(phone)
            return True
        return False

    def edit_phone(self, old_phone, new_phone):
        phone_to_edit = self.find_phone(old_phone)
        if not phone_to_edit:
            raise ValueError("Номер телефону не знайдено.")
        
        new_phone_obj = Phone(new_phone)
        self.phones.remove(phone_to_edit)
        self.phones.append(new_phone_obj)
        return True

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = "; ".join(p.value for p in self.phones)
        # Змінено: використовується новий атрибут `date` для форматування дати.
        birthday_str = f", birthday: {self.birthday.date.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"

# Клас адресної книги.
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return True
        return False

    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today = datetime.date.today()
        for record in self.data.values():
            # Змінено: тепер використовується атрибут `date`.
            if record.birthday and record.birthday.date:
                birthday_this_year = record.birthday.date.replace(year=today.year)
                
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                
                delta_days = (birthday_this_year - today).days

                if 0 <= delta_days < 7:
                    if birthday_this_year.weekday() >= 5:
                        if birthday_this_year.weekday() == 5:
                            birthday_this_year += datetime.timedelta(days=2)
                        elif birthday_this_year.weekday() == 6:
                            birthday_this_year += datetime.timedelta(days=1)
                    
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": birthday_this_year.strftime("%d.%m.%Y")
                    })
        return upcoming_birthdays

    def __str__(self):
        if not self.data:
            return "Адресна книга порожня."
        return '\n'.join(str(record) for record in self.data.values())
    
# --- Функції для серіалізації/десеріалізації ---
def save_data(book, filename="addressbook.pkl"):
    """
    Зберігає об'єкт AddressBook у файл за допомогою pickle.
    """
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    """
    Завантажує об'єкт AddressBook з файлу.
    Якщо файл не знайдено, повертає новий екземпляр.
    """
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

# --- Функції-обробники команд ---

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.lower()
    return cmd, *args

@input_error
def add_contact(args, book):
    if len(args) < 2:
        raise IndexError("Неповна команда. Введіть ім'я та хоча б один телефон.")
    name, *phones = args
    record = book.find(name)
    message = "Контакт оновлено."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Контакт додано."
    
    for phone in phones:
        record.add_phone(phone)
    
    return message

@input_error
def change_contact(args, book):
    if len(args) != 3:
        raise IndexError("Неповна команда. Введіть ім'я, старий телефон та новий телефон.")
    name, old_phone, new_phone = args
    record = book.find(name)
    # Змінено: видалено if-перевірку, дозволяючи декоратору обробити AttributeError.
    record.edit_phone(old_phone, new_phone)
    return "Контакт оновлено."
    
# Змінено: функція `show_phone` тепер показує лише номери телефонів.
@input_error
def show_phone(args, book):
    if len(args) != 1:
        raise IndexError("Неповна команда. Введіть ім'я.")
    name = args[0]
    # Змінено: видалено if-перевірку, дозволяючи декоратору обробити AttributeError.
    record = book.find(name)
    phones_str = "; ".join(p.value for p in record.phones)
    return phones_str if phones_str else "У контакту немає номерів телефону."

@input_error
def add_birthday(args, book):
    if len(args) != 2:
        raise IndexError("Неповна команда. Введіть ім'я та дату народження (DD.MM.YYYY).")
    name, birthday = args
    # Змінено: видалено if-перевірку, дозволяючи декоратору обробити AttributeError.
    record = book.find(name)
    record.add_birthday(birthday)
    return "Дату народження додано."
    

@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise IndexError("Неповна команда. Введіть ім'я.")
    name = args[0]
    record = book.find(name)
    # Змінено: використовується атрибут `date.
    if record.birthday:
        return f"Дата народження {record.name.value}: {record.birthday.date.strftime('%d.%m.%Y')}"
    else:
        return "У контакту не вказано дату народження."
    

@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "Немає найближчих днів народження."
    
    output = "Дні народження на найближчий тиждень:\n"
    for item in upcoming:
        output += f"{item['name']}: {item['birthday']}\n"
    return output

# --- Головна функція ---
def main():
    # Завантажуємо дані з файлу, якщо він існує. Інакше створюємо нову адресну книгу.
    book = load_data() 
    print("Вітаю! Я ваш бот-помічник. Чим можу допомогти?")
    print("Список команд: add, change, phone, all, add-birthday, show-birthday, birthdays, hello, exit, close")
    while True:
        user_input = input("Введіть команду: ")
        command, *args = parse_input(user_input)

        # Змінено: перенесено обробку порожнього вводу.
        if command is None:
            print("Будь ласка, введіть команду.")
            continue

        
        if command in ["close", "exit"]:
            # Зберігаємо поточну адресну книгу у файл перед виходом з програми.
            save_data(book)
            print("До побачення!")
            break
        elif command == "hello":
            print("Як я можу вам допомогти?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(book)
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Невірна команда.")
            
if __name__ == "__main__":
    main()