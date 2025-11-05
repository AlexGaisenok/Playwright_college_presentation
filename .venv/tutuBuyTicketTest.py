import re
from playwright.sync_api import sync_playwright
from pages.mainPage import *
from pages.resultsTickets import *
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Launch the Chromium browser
    page = browser.new_page()
    page.goto('https://avia.tutu.ru/')

    origin_dest = page.locator(destination)
    origin_dest.click()
    origin_dest.fill('Владивосток')
    page.wait_for_timeout(3000)
    origin_dest.press('Enter')
    final_dest = page.locator(final_destination)
    final_dest.click()
    final_dest.fill('')
    final_dest.fill('Рио')
    page.wait_for_timeout(3000)
    final_dest.press('Enter')
    depDate = page.locator(departure_date)
    depDate.click()
    StartDateOfFlight = page.locator(depart_date_calendar)
    StartDateOfFlight.wait_for(state='visible', timeout=5000)
    StartDateOfFlight.click()

    buttonFind = page.locator(button_find_tickets)
    buttonFind.wait_for(state='visible', timeout=10000)
    buttonFind.click()
    # Ждём, пока появится хотя бы один элемент с ценой
    page.wait_for_selector('xpath=//*[@data-ti="price" and contains(text(), "₽")]', state='visible', timeout=15000)

    # Потом ждём, пока их количество перестанет меняться (просто короткий цикл)
    previous_count = 0
    for _ in range(10):  # максимум 10 попыток
        current_count = page.locator('xpath=//*[@data-ti="price" and contains(text(), "₽")]').count()
        if current_count == previous_count and current_count > 0:
            break  # список стабилизировался
        previous_count = current_count
        page.wait_for_timeout(500)  # подождать полсекунды

    # Теперь можно уверенно получить все элементы
    price_elements = page.locator('xpath=//*[@data-ti="price" and contains(text(), "₽")]').all()

    # 2. Преобразуем текст цен в числа
    prices_dict = {}  # словарь: элемент → цена
    for el in price_elements:
        try:
            price_text = el.inner_text()
            price_number = int(re.sub(r"[^\d]", "", price_text))
            prices_dict[el] = price_number
        except ValueError:
            continue  # если вдруг текст не число, пропускаем

    # 3. Находим элемент с минимальной ценой
    min_price_el = min(prices_dict, key=lambda el: prices_dict[el])
    print("Минимальная цена:", prices_dict[min_price_el])
    # Находим родительский контейнер цены (можно подняться до ближайшего div)
    parent_container = min_price_el.evaluate_handle("el => el.closest('div[data-ti=\"tariff\"]')")

    # Ищем кнопку "Выбрать билет" внутри этого контейнера
    buy_button = parent_container.as_element().query_selector('xpath=.//*[contains(text(), "Выбрать билет")]')

    # Кликаем
    if buy_button:
        buy_button.click()
    else:
        print("Кнопка не найдена!")

    page.wait_for_timeout(5000)
    buttonBuyTicket = page.locator(buttonBuyATicket)
    buttonBuyTicket.wait_for(state='visible', timeout=5000)
    buttonBuyTicket.click()

    page.wait_for_timeout(20000)

    browser.close()