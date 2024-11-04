import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Öffne den Browser mit undetected_chromedriver
driver = uc.Chrome()

# 1. Öffne die ChatGPT-Webseite
driver.get('https://chat.openai.com/')

# Warte, bis die Seite geladen ist und du dich manuell eingeloggt hast
input("Bitte logge dich ein und löse alle Captchas, dann drücke Enter.")

# Finde das Textfeld und schreibe den Text hinein
text_area = driver.find_element(By.ID, 'prompt-textarea')
input_text = "Dein Beispieltext hier."
text_area.send_keys(input_text)
text_area.send_keys(Keys.ENTER)

# Warte auf das Laden der Seite
time.sleep(5)

# Suche nach allen Nachrichtenelementen, die das Attribut 'data-message-author-role' enthalten
messages = driver.find_elements(By.CSS_SELECTOR, '[data-message-author-role]')

# Extrahiere den Text aus jeder Nachricht und drucke ihn
for message in messages:
    author_role = message.get_attribute("data-message-author-role")
    message_text = message.text
    print(f"Role: {author_role}\nMessage: {message_text}\n")

# Halte das Skript am Leben, damit der Browser offen bleibt
input("Drücke Enter, um das Skript zu beenden und den Browser offen zu lassen.")
# Schließe den Browser
# driver.quit()
