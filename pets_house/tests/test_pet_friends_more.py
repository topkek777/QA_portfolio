from api import PetFriends
from settings import valid_email, valid_password
import os

pf = PetFriends()

def test_add_new_pet_without_photo(name='Давид', animal_type='Бродяга', age='4'):
    """Проверяем, что можно добавить питомца без фото"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Создаем питомца без фото
    status, result = pf.add_new_pet_without_photo(auth_key, name, animal_type, age)

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 200
    assert result['name'] == name
    assert result['pet_photo'] == ''

def test_add_pet_photo(pet_photo='images/P1040103.jpg'):
    """Проверяем, что можно добавить фото существующего питомца без фото"""

    # Получаем ключ auth_key и запрашиваем список своих питомцев
    _, auth_key = pf.get_api_key(valid_email, valid_password)
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")

    # Получаем полный путь изображения питомца и сохраняем в переменную pet_photo_edit
    pet_photo_edit = os.path.join(os.path.dirname(__file__), pet_photo)

    # Ищем питомца без фото. Если такого нет, то вызываем ошибку
    pet_id = ''
    for pet in my_pets['pets']:
        if pet['pet_photo'] == '':
            pet_id = pet['id']
            break

    # Сверяем полученный ответ с ожидаемым результатом
    if pet['id'] != '':
        status, result = pf.add_pet_photo(auth_key, pet_id, pet_photo_edit)
        print(result['pet_photo'])
        assert status == 200
    else:
        raise Exception("Нет питомцев без фото!")

def test_update_pet_photo(pet_photo='images/cat1.jpg'):
    """Проверяем, что можно обновить фото существующего питомца с фото"""

    # Получаем ключ auth_key и запрашиваем список своих питомцев
    _, auth_key = pf.get_api_key(valid_email, valid_password)
    _, my_pets = pf.get_list_of_pets(auth_key, "my_pets")

    # Получаем полный путь изображения питомца и сохраняем в переменную pet_photo_edit
    pet_photo_edit = os.path.join(os.path.dirname(__file__), pet_photo)

    # Ищем питомца с фото. Если такого нет, то вызываем ошибку
    pet_id = ''
    for pet in my_pets['pets']:
        if pet['pet_photo'] != '':
            pet_id = pet['id']
            break

    # Сверяем полученный ответ с ожидаемым результатом
    if pet['id'] != '':
        status, result = pf.add_pet_photo(auth_key, pet_id, pet_photo_edit)
        assert status == 200
    else:
        raise Exception("Нет питомцев с фото!")

def test_get_api_key_for_non_existent_user():
    """ Проверяем, что невозможно получить API-ключ для несуществующего пользователя"""

    email = '123ema45ilsomerandomwords@mail.ru'
    password = 'randompassword'

    # Отправляем запрос и сохраняем полученный ответ с кодом статуса в status, а текст ответа в result
    status, result = pf.get_api_key(email, password)

    # Сверяем полученные данные с нашими ожиданиями
    assert status == 403

def test_add_new_pet_with_invalid_auth_key(name='Давид', animal_type='Бродяга', age='4'):
    """Проверяем, что нельзя добавить питомца с некорректным ключом авторизации"""

    # Создаем рандомный ключ
    auth_key = {'key': '63c23208e3f6cd32a4965705606293a6e0c975d2431a50b08d99a6219'}

    # Создаем питомца без фото
    status, result = pf.add_new_pet_without_photo(auth_key, name, animal_type, age)

    # Сверяем полученный ответ с ожидаемым результатом
    assert status == 403

def test_add_new_pet_with_invalid_photo(name='Давид', animal_type='Бродяга', age='4', pet_photo='images/fake.html'):
    """Проверяем, что нельзя добавить питомца с неверным форматом фото"""

    # Получаем полный путь изображения питомца и сохраняем в переменную pet_photo
    pet_photo = os.path.join(os.path.dirname(__file__), pet_photo)

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Добавляем питомца
    status, result = pf.add_new_pet(auth_key, name, animal_type, age, pet_photo)
    print(status, result)

    # Сверяем полученный ответ с ожидаемым результатом
    if result['name'] == name and result['id'] != '':
        raise Exception('Питомец добавлен с неверным форматом фото!')
    assert status == 403

def test_add_new_pet_with_invalid_age(name='Давид', animal_type='Бродяга', age='Опасный'):
    """Проверяем, что нельзя добавить питомца с неправильным форматом возраста"""

    # Запрашиваем ключ api и сохраняем в переменую auth_key
    _, auth_key = pf.get_api_key(valid_email, valid_password)

    # Создаем питомца без фото
    status, result = pf.add_new_pet_without_photo(auth_key, name, animal_type, age)
    print(result)

    # Сверяем полученный ответ с ожидаемым результатом
    if result['id']:
        raise Exception('Питомец добавлен с неверным форматом возраста')
    assert status == 403
